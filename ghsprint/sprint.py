import concurrent.futures
import logging
import sys
from datetime import date, datetime, timedelta
from time import time
from typing import List, Tuple, TypeVar

from dateutil.relativedelta import WE, relativedelta
from rake_nltk import Rake
from tqdm import tqdm

from .board_card import Card
from .ghdriver import GithubHelper
from .issue import states

nl = '\n'


class Sprint(object):
    def __init__(self, access_token, repos, project_name, ignore_columns, keep_columns, login_name_mapper='', start=None, end=None, week_number=None, special_tags='', verbosity=0):
        self.ghh = GithubHelper(access_token, repos, project_name, ignore_columns, keep_columns, login_name_mapper=login_name_mapper, special_tags=special_tags, verbosity=verbosity)

        # logging
        self.logger = logging.Logger('sprint')
        self.logger.setLevel(logging.INFO)

        format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(format)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.logger.info('starting')

        sprint_start_day = WE
        start_hour = 9
        end_hour = 19
        sprint_length = 7
        if not week_number:
            today = datetime.now()
            last_wed = today + relativedelta(weekday=sprint_start_day(-1))
            start = last_wed
        else:
            start = date(date.today().year, 1, 1)+timedelta(weeks=week_number) + relativedelta(weekday=sprint_start_day(-1))
            start = datetime.combine(start, datetime.min.time())

        start = start.replace(hour=start_hour, minute=0, microsecond=0, second=0)
        self.date_start = start
        if not end:
            self.date_end = self.date_start + timedelta(days=sprint_length-1)
        else:
            self.date_end = end
        self.date_end = self.date_end.replace(hour=end_hour, minute=0, microsecond=0, second=0)

        if self.date_end <= self.date_start:
            raise ValueError('end is set incorrectly')

    def set_pokered_leftovers(self, all_cards: List[Card]):
        self.all_pokered_leftover = [c for c in all_cards if c.has_label_val_created_within(
            self.date_start-timedelta(days=1), self.date_start)]

    def set_pokered(self, all_cards: List[Card]):
        self.all_pokered_cards = [c for c in all_cards if c.has_label_val_created_within(
            self.date_start, self.date_start+timedelta(hours=8))]

    def set_unchanged_stories(self, all_cards: List[Card]):
        self.all_stale_cards = [c for c in all_cards if c.col.name in self.ghh.cols_keep and c not in self.all_pokered_cards and c not in self.all_pokered_leftover]

    def set_repokered(self, all_cards: List[Card]):
        self.all_repokered_cards = [c for c in all_cards if c.has_label_val_created_within(
            self.date_end-timedelta(hours=12), self.date_end)]

    def set_PRs_without_stories(self, all_PRs):
        self.PRs_without_issues = [pr for pr in all_PRs if len(pr.closes) == 0 and self.date_start < pr.created_at < self.date_end]


    def fetch_all_data(self):
        start_0 = time()
        # to know that is in not yet in production
        # prod_sha = self.ghh.get_production_sha()
        # master_sha = self.ghh.get_master_sha()
        # compare = self.ghh.compare_commits(prod_sha, master_sha)
        # self.logger.info('time for production tag difference:\t{:.1f}s'.format(time() - start_0))

        # get project_id
        start = time()
        found_matching_name = False
        with tqdm(total=len(self.ghh.repos)) as pbar:
            for repo in self.ghh.repos:
                pbar.set_description(f'Checking {repo.owner}/{repo.name}')
                prjs = self.ghh.get_all_projects(repo)
                for project in prjs:
                    if self.ghh.project_name.lower() == project['name'].lower():
                        self.ghh.project_id = project['id']
                        found_matching_name = True
                        pbar.update(len(self.ghh.repos)-pbar.n)
                        break
                if found_matching_name:
                    break
                pbar.update()
        if not found_matching_name:
            raise RuntimeError(f'No suitable project called "{self.ghh.project_name}" found in {self.ghh.repos}')
        self.logger.info('time for getting project id:\t{:.1f}s'.format(time() - start))

        # get all columns in project
        start = time()
        cols = self.ghh.get_all_columns()
        self.logger.info('time for board columns:\t{:.1f}s'.format(time() - start))

        # get all cards from board and columns
        all_cards = []
        start = time()
        with tqdm(total=len(cols)) as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
                for col, cards in zip(cols, executor.map(self.ghh.get_all_cards, cols)):
                    pbar.set_description(f'Fetched cards for {col.name}')
                    all_cards.extend(cards)
                    pbar.update()

        self.logger.info('time for all board cards:\t{:.1f}s'.format(time() - start))

        # recognize related repos, add it to config
        self.ghh.repos = self.ghh.repos + list(set(c.repo for c in all_cards if c.repo != None and c.repo not in self.ghh.repos))

        # PRs
        start = time()
        pull_requests = self.ghh.get_all_PRs()
        self.logger.info('time for PRs:\t{:.1f}s'.format(time() - start))

        start = time()
        with tqdm(total=len(pull_requests)) as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
                for pr, revs in zip(pull_requests, executor.map(self.ghh.fetch_PR_reviews, pull_requests)):
                    pbar.set_description(f'Fetched PR reviews for #{pr.number}')
                    pr.add_reviews(revs)
                    pbar.update()
        self.logger.info('time for PR reviews:\t{:.1f}s'.format(time() - start))

        start = time()
        with tqdm(total=len(pull_requests)) as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
                for pr, data in zip(pull_requests, executor.map(self.ghh.fetch_PR_data, pull_requests)):
                    pbar.set_description(f'Fetched PR data for #{pr.number}')
                    pr.update(data)
                    pbar.update()
        self.logger.info('time for PR data:\t{:.1f}s'.format(time() - start))

        # get all events
        start = time()
        cards_with_issues = [c for c in all_cards if c.has_issue]
        with tqdm(total=len(cards_with_issues)) as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                for card, events in zip(cards_with_issues, executor.map(self.ghh.get_all_events, [c.issue_num for c in cards_with_issues])):
                    pbar.set_description(f'Fetched events for #{card.id}')
                    card.set_events(events)
                    pbar.update()
        self.logger.info('time for all board card events:\t{:.1f}s'.format(time() - start))

        # issue data
        start = time()
        with tqdm(total=len(cards_with_issues)) as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
                for card, issue in zip(cards_with_issues, executor.map(self.ghh.get_single_issue_from_card, cards_with_issues)):
                    pbar.set_description(f'Fetched issue data for #{card.id}')
                    card.set_issue(issue)
                    pbar.update()
        self.logger.info('time for all board card issues:\t{:.1f}s'.format(time() - start))

        # total
        self.logger.info('total time:\t{:.1f}s'.format(time() - start_0))

        self.set_pokered_leftovers(cards_with_issues)
        self.set_pokered(cards_with_issues)
        self.set_repokered(cards_with_issues)
        self.set_unchanged_stories(cards_with_issues)
        self.prs = pull_requests
        self.set_PRs_without_stories(pull_requests)

    def get_all_stories(self):
        return self.all_pokered_cards + self.all_pokered_leftover + self.all_stale_cards + self.all_repokered_cards

    def print_report(self):
        def print_pr(pr, print_user):
            user = pr.user_name if print_user else ''
            special_tags = [tag for tag in pr.labels if tag['name'] in self.ghh.special_tags]
            special_tags_str = ''
            if special_tags:
                special_tags_str = ', '.join(f'[**{tag["name"]}**]' for tag in special_tags) + ', '
            return f' - PR {pr.get_state()} [{pr.repo.name} #{pr.number} {pr.title}]({pr.url} ) {user}\n' + \
                   f'      - {special_tags_str}+{pr.additions}, -{pr.deletions}, files changed: {pr.changed_files}\n' + \
                   f'      - Reviews: {pr.get_review_state(self.ghh.login_name_mapper)}'

        def print_story(story):
            txt = ''
            leftover = story.get_pokered_value(
                self.date_start-timedelta(days=1), self.date_start)
            poker = story.get_pokered_value(
                self.date_start, self.date_start+timedelta(hours=8)) or story.get_current_value()
            repoker = story.get_pokered_value(
                self.date_end-timedelta(hours=5), self.date_end) or '?'
            poker_repoker = '{}({})'.format(repoker, poker or leftover)
            special_tags = ' ' + ', '.join(f'[**{tag["name"]}**]' for tag in story.issue.labels if tag['name'] in self.ghh.special_tags)
            txt += '- {}{} [**{}**] [**{}**]({} ) {}'.format(
                story.get_state(),
                special_tags,
                poker_repoker,
                story.issue.title.strip(),
                story.issue.url,
                ', '.join(story.get_assignees(self.ghh.login_name_mapper))
            )
            pr_block = []
            for pr_event in [ev for ev in story.events if ev.source_is_pr]:
                merged_txt = ''
                prs = [pr for pr in self.prs if pr.number == pr_event.source_number and pr.repo == pr_event.source_repo]
                if len(prs) == 0:
                    pr = self.ghh.get_pr(pr_event.source_repo, pr_event.source_number)
                else:
                    pr = prs[0]
                pr_block.append('  ' + print_pr(pr, print_user=False))
            if len(pr_block) > 0:
                txt += nl
                txt += nl.join(pr_block)
            return txt

        # report list, will be joined at the end with newline character
        rprt = []

        # title by using word frequency
        all_titles = '. '.join([c.issue.title.strip() for c in self.get_all_stories()])
        r = Rake()
        r.extract_keywords_from_text(all_titles)
        word_degs = r.get_word_degrees()
        sorted_tuples = sorted(word_degs.items(), key=lambda item: item[1], reverse=True)
        rprt.append('# '+', '.join([t[0] for t in sorted_tuples[:10]]))
        rprt.append('')

        # date range: 06. February - 12. February 2019
        rprt.append('{} - {}'.format(self.date_start.strftime("%d. %B"),
                                     self.date_end.strftime("%d. %B %Y")))
        rprt.append('')

        # Velocity
        rprt.append('Velocity: **X**')
        rprt.append('')

        # Stories
        if self.all_pokered_leftover:
            rprt.append('# Leftover stories from last week')
            for story in self.all_pokered_leftover:
                rprt.append(print_story(story))
                rprt.append('')

        if self.all_pokered_cards:
            rprt.append('# Stories of the week')
            for story in self.all_pokered_cards:
                rprt.append(print_story(story))
                rprt.append('')

        if self.all_stale_cards:
            rprt.append('# Unchanged stories')
            for story in self.all_stale_cards:
                rprt.append(print_story(story))
                rprt.append('')

        # PRs without story:
        if self.PRs_without_issues:
            rprt.append('# PRs without issue')
            for pr in self.PRs_without_issues:
                rprt.append(print_pr(pr, print_user=True))

        return nl.join(rprt)
