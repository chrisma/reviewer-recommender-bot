from django.core.management.base import BaseCommand, CommandError
from bot.models import GitHubPullRequest
from bot.marvin import Marvin
from pprint import pprint
import logging

class Command(BaseCommand):
    help = 'Starts Marvin on GitHubPullRequests in the database.'

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('sh').setLevel(logging.WARNING)

        self.stdout.write(self.style.SUCCESS('Command started!'))
        pr = GitHubPullRequest.objects.get(id=5)
        self.stdout.write('Using PR: ' + str(pr))
        repo_storage_path = '/home/christoph/git/reviewer-recommender-bot/repos'
        marvin = Marvin(repo_storage_path=repo_storage_path)
        marvin.handle_pr(pr.pull_request_json)
        marvin.number_commits = 3
        file_changes = marvin.diff
        blames = marvin.blame_changes(file_changes)
        pprint(blames)

