
from .utils import str2date

class Repo(object):
    def __init__(self, owner:str, name:str):
        self.owner = owner
        self.name = name

    def __hash__(self):
        return hash(self.owner+self.name)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.owner == other.owner and self.name == other.name

    @classmethod
    def from_http(cls,url):
        if not url.startswith('http'):
            raise ValueError('{} does not start with `http`')
        owner, name = url.split('/')[-4:-2]
        return cls(owner, name)

class Commit(object):
    def __init__(self, commit):
        self.message = commit['commit']['message']
        self.sha = commit['commit']['tree']['sha']
        self.committer_name = commit['commit']['committer']['name']
        self.committer_date = str2date(commit['commit']['committer']['date'])

        pattern = ' \\(#(\\d+)\\)$'
        pr_num = None
        for pr_num in re.findall(pattern, self.message):
            self.pr_num = pr_num
