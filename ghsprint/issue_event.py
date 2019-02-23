from .issue import states
from .utils import str2date
from .repo_stuff import Repo


class Event(object):
    def __init__(self, ev, label2val: dict = {}):
        self.date = str2date(ev['created_at'])
        self.id = ev.get('id', None)
        self.event = ev['event']
        self.label = ev.get('label', {}).get('name', None)
        self.label_val = label2val.get(self.label, None)
        self.assignee = ev.get('assignee', {}).get('login', None)

        src = ev.get('source', {})
        issue = src.get('issue', {})

        self.source_title = None
        self.source_number = None
        self.source_closed_at = None
        self.source_state = None
        self.source_is_pr = None
        self.source_repo = None
        if src:
            owner, repo = issue['repository_url'].split('/')[-2:]
            self.source_repo = Repo(owner, repo)
            self.source_title = issue.get('title', None)
            self.source_number = issue.get('number', None)
            self.source_closed_at = str2date(self.source_closed_at)
            self.source_state = states[issue.get('state', None)]
            self.source_is_pr = 'pull_request' in issue
            self.source_body = issue['body']
