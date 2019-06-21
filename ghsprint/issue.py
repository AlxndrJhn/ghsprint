from enum import Enum

from .repo_stuff import Repo
from .utils import str2date


class states(Enum):
    unknown = 0
    open = 1
    closed = 2


class Issue(object):
    def __init__(self, repo: Repo, issue_dict: dict):
        self.repo = repo
        self.closed_at = str2date(issue_dict.get('closed_at', None))
        self.id = issue_dict.get('id', None)
        self.number = issue_dict.get('number', None)
        self.title = issue_dict.get('title', None)
        self.url = issue_dict.get('html_url', None)
        self.assignees = issue_dict.get('assignees', [])
        self.labels = issue_dict.get('labels', [])
        state_string = issue_dict.get('state', None)
        self.state = None
        if state_string:
            self.state = states[state_string]

    @classmethod
    def from_closes_line(cls, line: str, default_repo: Repo):
        # https://github.com/fedger/menu-service/issues/857
        line = line.strip()
        if not line.lower().startswith('- closes '):
            raise ValueError('this line `{}` is not like `- closes [...]`'.format(line))

        http = 'http'
        if http in line:
            url = http+line.split(http)[-1]
            url = url.replace(')','')
            try:
                number = int(url.split('/')[-1])
            except:
                pass
                number = -1
            repo = Repo.from_http(url)
            return cls(repo, {'number': number, 'html_url': url})
        elif line.endswith('none'):
            return None
        elif '<' in line or '>' in line:
            return None
        else:
            if '#' not in line:
                raise ValueError('this line `{}` does not have a `#` in it'.format(line))

            number = int(line.split('#')[1])
            return cls(default_repo, {'number': number})
