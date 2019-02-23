import concurrent.futures
import logging
import sys
from datetime import date, datetime, timedelta
from time import time
from typing import List, Tuple, TypeVar

from dateutil.relativedelta import WE, relativedelta

from .board_card import Card
from .ghdriver import GithubHelper
from .issue import states

nl = '\n'


class Sprint(object):
    def __init__(self, access_token, repos, project_id, ignore_columns, start=None, end=None, week_number=None, verbosity=0):
        self.ghh = GithubHelper(access_token, repos, project_id, ignore_columns, verbosity=verbosity)

        # logging
        self.logger = logging.Logger('sprint')
        if verbosity >= 3:
            self.logger.setLevel(logging.DEBUG)
        elif verbosity >= 2:
            self.logger.setLevel(logging.INFO)
        elif verbosity >= 1:
            self.logger.setLevel(logging.WARNING)
        elif verbosity <= 0:
            self.logger.setLevel(logging.ERROR)

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

        # PRs
        start = time()
        PRs = self.ghh.get_all_PRs()
        self.logger.info('time for PRs:\t{:.1f}s'.format(time() - start))

        start = time()
        # for pr in PRs:
        #    pr.add_reviews(fetch_PR_reviews(pr.number))
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            for pr, revs in zip(PRs, executor.map(self.ghh.fetch_PR_reviews, PRs)):
                pr.add_reviews(revs)
        self.logger.info('time for PR reviews:\t{:.1f}s'.format(time() - start))

        start = time()
        cols = self.ghh.get_all_columns()
        self.logger.info('time for board columns:\t{:.1f}s'.format(time() - start))
        all_cards = []
        start = time()
        # for col in cols:
        #    col_cards = get_all_cards(col)
        #    all_cards.extend(col_cards)
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            for col, cards in zip(cols, executor.map(self.ghh.get_all_cards, cols)):
                all_cards.extend(cards)
                # self.logger.info('{}\t{}'.format(col.name, len(cards)))
        self.logger.info('time for all board cards:\t{:.1f}s'.format(time() - start))

        start = time()
        cards_with_issues = [c for c in all_cards if c.has_issue]
        # for c in cards_with_issues:
        #     c.set_events(get_all_events(c.issue_num))
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            for card, events in zip(cards_with_issues, executor.map(self.ghh.get_all_events, [c.issue_num for c in cards_with_issues])):
                card.set_events(events)
        self.logger.info('time for all board card events:\t{:.1f}s'.format(time() - start))

        start = time()
        # for c in cards_with_issues:
        #     c.set_issue(get_single_issue(c.issue_num))
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            for card, issue in zip(cards_with_issues, executor.map(self.ghh.get_single_issue_from_card, cards_with_issues)):
                card.set_issue(issue)
        self.logger.info('time for all board card issues:\t{:.1f}s'.format(time() - start))
        self.logger.info('total time:\t{:.1f}s'.format(time() - start_0))

        self.set_pokered_leftovers(all_cards)
        self.set_pokered(all_cards)
        self.set_repokered(all_cards)
        self.prs = PRs
        self.set_PRs_without_stories(PRs)

    def print_report(self):
        def print_pr(pr):
            return ' - PR {} {} [{} #{} {}]({} ) {}'.format(pr.get_state(), pr.get_review_state(), pr.repo.name, pr.number, pr.title, pr.url, pr.user_name)

        def print_story(story):
            txt = ''
            leftover = story.get_pokered_value(
                self.date_start-timedelta(days=1), self.date_start)
            poker = story.get_pokered_value(
                self.date_start, self.date_start+timedelta(hours=8))
            repoker = story.get_pokered_value(
                self.date_end-timedelta(hours=5), self.date_end) or '?'
            poker_repoker = '{}({})'.format(repoker, poker or leftover)
            txt += '- {} [**{}**] [**{}**]({} ) {}'.format(
                story.get_state(),
                poker_repoker,
                story.issue.title.strip(),
                story.issue.url,
                ', '.join(story.get_assignees())
            )
            pr_block = []
            for pr_event in [ev for ev in story.events if ev.source_is_pr]:
                merged_txt = ''
                prs = [pr for pr in self.prs if pr.number == pr_event.source_number and pr.repo == pr_event.source_repo]
                if len(prs) == 0:
                    pr = self.ghh.get_pr(pr_event.source_repo, pr_event.source_number)
                else:
                    pr = prs[0]
                pr_block.append('  ' + print_pr(pr))
            if len(pr_block) > 0:
                txt += nl
                txt += nl.join(pr_block)
            return txt

        # report list, will be joined at the end with newline character
        rprt = []

        # title
        all_titles = [c.issue.title.strip() for c in self.all_pokered_cards]
        rprt.append('# '+', '.join(all_titles))
        rprt.append('')

        # date range: 06. February - 12. February 2019
        rprt.append('{} - {}'.format(self.date_start.strftime("%d. %B"),
                                     self.date_end.strftime("%d. %B %Y")))
        rprt.append('')

        # Velocity
        rprt.append('Velocity: **X**')
        rprt.append('')

        # Stories
        if len(self.all_pokered_leftover) > 0:
            rprt.append('# Leftover stories from last week')
            for story in self.all_pokered_leftover:
                rprt.append(print_story(story))
                rprt.append('')

        rprt.append('# Stories of the week')
        for story in self.all_pokered_cards:
            rprt.append(print_story(story))
            rprt.append('')

        # PRs without story:
        rprt.append('# PRs without issue')
        for pr in self.PRs_without_issues:
            rprt.append(print_pr(pr))

        # - [**no-poker**] [**pseudonymize users local folder when using labelImg**](https://github.com/fedger/menu-service/issues/257)
        #   - PR [#118](https://github.com/fedger/labelImg/pull/118)

        return nl.join(rprt)
