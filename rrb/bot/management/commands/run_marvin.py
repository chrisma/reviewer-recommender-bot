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
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('github3').setLevel(logging.WARNING)
        logging.info(self.style.SUCCESS('Command "run_marvin" started!'))

        pr = GitHubPullRequest.objects.get(id=7)
        repo_storage_dir = '/home/christoph/git/reviewer-recommender-bot/repos'
        marvin = Marvin(repo_dir=repo_storage_dir)
        summary = marvin.handle_pr(pr.pull_request_json)
        pprint(summary)
