from django.core.management.base import BaseCommand, CommandError
from bot.models import GitHubPullRequest
from bot.marvin import Marvin
from pprint import pprint
import logging
import itertools
import operator

class Command(BaseCommand):
    help = 'Starts Marvin on GitHubPullRequests in the database.'

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('sh').setLevel(logging.WARNING)

        logging.info(self.style.SUCCESS('Command started!'))
        pr = GitHubPullRequest.objects.get(id=5)
        logging.info('Using PR: ' + str(pr))
        repo_storage_path = '/home/christoph/git/reviewer-recommender-bot/repos'
        marvin = Marvin(repo_storage_path=repo_storage_path)
        marvin.handle_pr(pr.pull_request_json)
        marvin.number_commits = 3
        file_changes = marvin.diff
        blames = marvin.blame_changes(file_changes)
        # pprint(blames)

        reviewers = {}
        for file, changes in blames.items():
            for change in changes:
                change['file'] = file
                author = change['author']
                if author in reviewers:
                    reviewers[author].append(change)
                else:
                    reviewers[author] = [change]
        # pprint(reviewers)

        github_logins = {}
        for author, changes in reviewers.items():
            github_logins[author] = marvin.get_github_login(changes[0]['commit'])
        # print(github_logins)

        pr_changes = []
        for author, changes in reviewers.items():
            login = github_logins[author]
            for change in changes:
                change['login'] = login
                pr_changes.append(change)
        # pprint(pr_changes)

        get_attr = operator.itemgetter('login')
        changes_count = [{'login':key, 'count':sum(1 for x in group)} for key, group in itertools.groupby(pr_changes, get_attr)]
        changes_count = sorted(changes_count, key=lambda x: x['count'], reverse=True)
        print(changes_count)
        # import pdb; pdb.set_trace()
