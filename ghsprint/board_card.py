from datetime import datetime
from typing import List, Dict

from .board_stuff import Column
from .issue_event import Event
from .utils import str2date
from .repo_stuff import Repo


class Card(object):
    def __init__(self, col: Column, input_dict: dict):
        self.col = col
        self.id = input_dict['id']
        self.created_at = str2date(input_dict['created_at'])
        self.updated_at = str2date(input_dict['updated_at'])
        self.content_url = input_dict.get('content_url', None)

        self.has_issue = False
        self.issue_num = None
        self.repo = None
        if self.content_url:
            self.repo = Repo.from_http(self.content_url)
            self.has_issue = True
            self.issue_num = int(self.content_url.split('/')[-1])
        self.events = []

    def __str__(self):
        return 'id: {}, issue_num: {}'.format(self.id, self.issue_num)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.created_at == other.created_at and self.content_url == other.content_url

    def set_events(self, events: List[Event]):
        self.events = events

    def get_state(self):
        last_change = next((ev.event for ev in self.events[::-1] if ev.event in ['reopened', 'closed']), None)
        state = 'open'
        if last_change:
            state = last_change

        return state

    def has_label_val_created_within(self, start: datetime, end: datetime, min_value: float = 0.5):
        val = self.get_pokered_value(start, end)
        return val is not None and val >= min_value

    def get_pokered_value(self, start: datetime, end: datetime):
        vals = [e.label_val for e in self.events if start <=
                e.date <= end and e.label_val]
        if len(vals) > 0:
            return vals[0]
        else:
            return None

    def get_current_value(self):
        vals = [e.label_val for e in self.events if e.label_val]
        if len(vals) > 0:
            return vals[-1]
        else:
            return None

    def set_issue(self, issue):
        self.issue = issue

    def was_assigned(self):
        return any(o.assignee for o in self.events)

    def get_assignees(self, login_to_name_mapping: Dict[str, str]={}):
        assignees = []
        for user in self.issue.assignees:
            user_name = login_to_name_mapping.get(user['login'].lower(), user['login'])
            assignees.append(user_name)

        return assignees or ['not assigned']
