from enum import Enum

from typing import Dict

from .issue import Issue, states
from .repo_stuff import Repo
from .utils import str2date


class PR(object):
    def __init__(self, repo: Repo, pr_dict: dict):
        self.repo = repo
        self.id = pr_dict['id']
        self.number = pr_dict['number']
        self.title = pr_dict['title']
        self.state = states[pr_dict['state']]
        self.created_at = str2date(pr_dict['created_at'])
        self.updated_at = str2date(pr_dict['updated_at'])
        self.url = pr_dict['html_url']

        self.merged_at = str2date(pr_dict['merged_at'])
        self.is_in_prod = None
        self.body = pr_dict['body']
        self.merge_commit_sha = pr_dict['merge_commit_sha']
        self.user_name = pr_dict['user']['login']

        self.labels = []
        self.deletions = None
        self.additions = None
        self.changed_files = None
        self.is_draft = False

        self.closes = []
        closes_lines = [line.strip() for line in pr_dict['body'].lower().split('\r\n') if line.startswith('- closes ')]
        if len(closes_lines) > 0:
            for line in closes_lines:
                issue = Issue.from_closes_line(line, repo)
                if issue:
                    self.closes.append(issue)

    def add_reviews(self, revs):
        self.reviews = revs

    def update(self, data):
        self.deletions = data['deletions']
        self.additions = data['additions']
        self.changed_files = data['changed_files']
        self.labels = data['labels']
        self.is_draft = data['mergeable_state'] == 'draft'

    def get_state(self):
        state = str(self.state.name)
        if self.merged_at:
            state = 'merged'
        return state

    def get_review_state(self, login_to_name_mapping: Dict[str, str]={}):
        ignore_states = [Review.states.DISMISSED, Review.states.COMMENTED]
        unique_reviewers = list({o.reviewer for o in self.reviews if o.state not in ignore_states})
        if len(unique_reviewers) == 0:
            return 'not reviewed'
        txt = []
        for reviewer in unique_reviewers:
            latest_review = next(rev for rev in self.reviews[::-1] if rev.reviewer == reviewer and rev.state not in ignore_states)
            mapped_reviewer_name = login_to_name_mapping.get(reviewer.lower(), reviewer)
            txt.append(f'{mapped_reviewer_name} > {latest_review.state.name.lower().replace("_", " ")}')
        return ', '.join(txt)


class Review(object):
    class states(Enum):
        CHANGES_REQUESTED = 0
        COMMENTED = 1
        APPROVED = 2
        DISMISSED = 3
        PENDING = 4

    def __init__(self, pr: PR, rev: dict):
        self.pr = pr
        self.submitted_at = str2date(rev.get('submitted_at', None))
        self.url = rev['html_url']
        self.reviewer = rev['user']['login']
        self.state = Review.states[rev['state']]
