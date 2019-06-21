import concurrent.futures
import datetime
import os
import sys
import typing
from datetime import date, datetime, timedelta
from time import time
from typing import List, Tuple, TypeVar

import click

from ghsprint.sprint import Sprint

os.putenv('PYTHONIOENCODING', 'UTF-8')


@click.command()
@click.option('--ignore-columns', default='', help='list of columns names to ignore, separated by commas')
@click.option('-v', '--verbose', count=True)
@click.option('-w', '--week')
@click.option('--keep-columns', default='', help='list of columns names to always have in report, separated by commas')
@click.option('--login-name-mapper', default='', help='<login>:<name>,...')
@click.option('--special-tags', default='', help='<tag string>,...')
@click.argument('access-token')
@click.argument('project-name')
@click.argument('repos', nargs=-1)
def start_sprint(access_token, repos, project_name, ignore_columns, keep_columns, verbose, week, login_name_mapper, special_tags):
    """Fetches all data from github to create the sprint report."""
    if week:
        week = int(week)
    sp = Sprint(access_token, repos, project_name, ignore_columns, keep_columns, login_name_mapper=login_name_mapper, week_number=week, verbosity=verbose, special_tags=special_tags)
    sp.fetch_all_data()
    report = sp.print_report()
    print(report)


if __name__ == '__main__':
    start_sprint()
