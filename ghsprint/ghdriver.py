import concurrent.futures
import datetime
import typing
from datetime import date, datetime, timedelta
from time import time
from typing import Dict, List, Tuple, TypeVar

from .board_card import Card
from .board_stuff import Column
from .issue import Issue
from .issue_event import Event
from .pr_stuff import PR, Review
from .repo_stuff import Commit, Repo
from .request_session import requests_retry_session
from .utils import str2date


class GithubHelper(object):
    def __init__(self, access_token: str, repos: List[str], project_name: str, ignore_columns: str, keep_columns: str, login_name_mapper: str, special_tags: str, verbosity=0):
        self.access_token = access_token
        self.headers = {'Accept': 'application/vnd.github.inertia-preview+json'}

        if repos is None:
            raise ValueError('set `repos` in github-scope')

        if len(repos) == 0:
            raise ValueError('set at least one repo in `repos` in github-scope')

        self.repos = [Repo(x[0], x[1]) for x in (x.split("/") for x in repos) if x[1] != 5]

        self.project_name = project_name
        self.cols_ignore = ignore_columns.split(',')
        self.cols_keep = keep_columns.split(',')

        self.login_name_mapper = dict(entry.split(':') for entry in login_name_mapper.split(','))
        self.login_name_mapper = {k.lower(): v for k, v in self.login_name_mapper.items()}
        self.special_tags = special_tags.split(',')
        self.label2val = {'0': 0, '½': 0.5, '1': 1, '2': 2, '3': 3, '5': 5, '8': 8, '13': 13, '25': 25, '50': 50, '100': 100}

    def get_all_projects(self, repo: Repo):
        url = 'https://api.github.com/repos/{}/{}/projects?access_token={}'.format(repo.owner, repo.name, self.access_token)
        r = requests_retry_session().get(url, headers=self.headers)
        if r.status_code == 200:
            return r.json()
        else:
            raise RuntimeError(f'Connection error fetching projects for {repo}')

    def get_all_columns(self) -> List[Column]:
        url = 'https://api.github.com/projects/{}/columns?access_token={}'.format(self.project_id, self.access_token)
        r = requests_retry_session().get(url, headers=self.headers)
        if r.status_code == 200:
            return [Column(self.project_id, col) for col in r.json() if col['name'] not in self.cols_ignore]
        return []

    def get_all_cards(self, col: Column) -> List[Card]:
        url = 'https://api.github.com/projects/columns/{}/cards?access_token={}&per_page=100'.format(col.id, self.access_token)
        r = requests_retry_session().get(url, headers=self.headers)
        if r.status_code == 200:
            return [Card(col, card) for card in r.json()]
        return []

    def get_all_current_labels(self, issue) -> List[str]:
        url = 'https://api.github.com/repos/{}/{}/issues/{}/labels?access_token={}'.format(
            issue.owner,
            issue.repo,
            issue.number,
            self.access_token)
        r = requests_retry_session().get(url, headers=self.headers)

        if r.status_code == 200:
            return [lab['name'] for lab in r.json() if lab['name'] in self.import_label_types]
        return []

    def get_all_events(self, issue_num) -> List[Event]:
        events = []
        for repo in self.repos:
            interesting_event_types = ['labeled', 'unlabeled', 'reopened', 'closed', 'assigned', 'cross-referenced']
            url = 'https://api.github.com/repos/{}/{}/issues/{}/timeline?access_token={}&per_page=100'.format(repo.owner, repo.name, issue_num, self.access_token)
            header = {'Accept': 'application/vnd.github.mockingbird-preview'}
            r = requests_retry_session().get(url, headers=header)

            if r.status_code == 200:

                for ev in r.json():
                    if ev['event'] in interesting_event_types:
                        events.append(Event(ev, self.label2val))
                return events
        return []

    def get_all_active_repos(self, owner, weeks=1) -> List[Repo]:
        rlist = []
        for repo in self.repos:
            url = 'https://api.github.com/orgs/{}/repos?access_token={}'.format(
                repo.owner,
                self.access_token)
            r = requests_retry_session().get(url, headers=self.headers)

            if r.status_code == 200:
                for repo in r.json():
                    last_push = str2date(repo['pushed_at'])
                    if datetime.now()-timedelta(weeks=weeks) < last_push:
                        rlist.append(Repo(repo['name'], repo['id']))
        return rlist

    def get_all_issues(self) -> List[Issue]:
        rlist = []
        for repo in self.repos:
            url = 'https://api.github.com/repos/{}/{}/issues?access_token={}&per_page=100'.format(
                repo.owner,
                repo.name,
                self.access_token)
            r = requests_retry_session().get(url, headers=self.headers)

            if r.status_code == 200:
                for issue_dict in r.json():
                    rlist.append(Issue(repo, issue_dict))
        return rlist

    def get_pr(self, repo, pr_num):
        # /repos/:owner/:repo/pulls/:number
        url = 'https://api.github.com/repos/{}/{}/pulls/{}?access_token={}'.format(
            repo.owner,
            repo.name,
            pr_num,
            self.access_token)
        r = requests_retry_session().get(url, headers=self.headers)

        if r.status_code == 200:
            pr = PR(repo, r.json())
            revs = self.fetch_PR_reviews(pr)
            pr.add_reviews(revs)
            return pr
        raise ValueError('invalid PR request for {}/{} #{}'.format(repo.owner, repo.name, pr_num))

    def get_all_PRs(self) -> List[PR]:
        pull_requests = []
        for repo in self.repos:
            url = 'https://api.github.com/repos/{}/{}/pulls?access_token={}&per_page=100'.format(
                repo.owner,
                repo.name,
                self.access_token)
            params = {
                'state': 'all',
                'sort': 'updated',
                'direction': 'desc'
            }
            r = requests_retry_session().get(url, headers=self.headers, data=params)

            if r.status_code == 200:
                for pr_dict in r.json():
                    pull_requests.append(PR(repo, pr_dict))
        return pull_requests

    def fetch_PR_data(self, pr: PR) -> List[Review]:
        # GET /repos/:owner/:repo/pulls/:number/reviews
        url = 'https://api.github.com/repos/{}/{}/pulls/{}?access_token={}'.format(
            pr.repo.owner,
            pr.repo.name,
            pr.number,
            self.access_token)

        r = requests_retry_session().get(url, headers=self.headers)

        if r.status_code == 200:
            return r.json()
        return None

    def fetch_PR_reviews(self, pr: PR) -> List[Review]:
        # GET /repos/:owner/:repo/pulls/:number/reviews
        url = 'https://api.github.com/repos/{}/{}/pulls/{}/reviews?access_token={}&per_page=100'.format(
            pr.repo.owner,
            pr.repo.name,
            pr.number,
            self.access_token)

        r = requests_retry_session().get(url, headers=self.headers)

        if r.status_code == 200:
            revs = []
            for rev in r.json():
                revs.append(Review(pr, rev))
            return revs
        return []

    def get_single_issue_from_card(self, card: Card) -> Issue:
        # /repos/:owner/:repo/issues/:number
        url = 'https://api.github.com/repos/{}/{}/issues/{}?access_token={}'.format(
            card.repo.owner,
            card.repo.name,
            card.issue_num,
            self.access_token)

        r = requests_retry_session().get(url, headers=self.headers)

        if r.status_code == 200:
            return Issue(card.repo, r.json())
        return None

    def get_production_sha(self, repo: Repo) -> str:
        # GET /repos/:owner/:repo/git/refs/tags
        ref = 'production'
        url = 'https://api.github.com/repos/{}/{}/git/refs/tags?access_token={}'.format(
            repo.owner,
            repo.name,
            self.access_token)

        r = requests_retry_session().get(url, headers=self.headers)

        if r.status_code == 200:
            prod_tag = [r for r in r.json() if 'refs/tags/{}'.format(ref)
                        == r['ref']][0]
            commit_sha = prod_tag['object']['sha']
            return commit_sha
        return None

    def get_master_sha(self, repo: Repo) -> str:
        # GET #/repos/:owner/:repo/git/refs/:ref
        url = 'https://api.github.com/repos/{}/{}/git/refs?access_token={}'.format(
            repo.owner,
            repo.name,
            self.access_token)
        r = requests_retry_session().get(url, headers=self.headers)
        if r.status_code == 200:
            master_ref = [r for r in r.json() if 'master' in r['ref']][0]
            commit_sha = master_ref['object']['sha']
            return commit_sha
        return None

    def compare_commits(self, repo: Repo, base: str, head: str) -> List[Commit]:
        # /repos/:owner/:repo/compare/:base...:head
        url = 'https://api.github.com/repos/{}/{}/compare/{}...{}?access_token={}'.format(
            repo.owner,
            repo.name,
            base,
            head,
            self.access_token)
        r = requests_retry_session().get(url, headers=self.headers)

        if r.status_code == 200:
            cmp = r.json()

            return cmp['ahead_by'], [Commit(c) for c in cmp['commits']]
        return None, None
