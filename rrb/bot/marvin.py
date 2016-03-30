import codecs, json, os, codecs, logging
from pprint import pprint
from collections import namedtuple
import itertools
import operator

from git import Repo
from git.remote import RemoteProgress
from requests import get
import whatthepatch
from sh import git
from github3 import GitHub
from github3.pulls import PullRequest

class Marvin(object):
	"""Merely A ReView INcentivizer """
	def __init__(self, repo_dir=None):
		class ProgressHandler(RemoteProgress):
			def line_dropped(self, line):
				logging.info(line)
			def update(self, *args):
				logging.info(self._cur_line)
		logging.info('Marvin started!')
		self.progress = ProgressHandler()
		if repo_dir is None:
			repo_dir = 'repos'
		self.repo_dir = os.path.abspath(repo_dir)
		logging.info('Storing repos to "%s"' % self.repo_dir)

		self.github = self._get_github_api()
		logging.info('Attempting to connect to Github...')
		ratelimit_remaining = self.github.ratelimit_remaining
		logging.info("Ratelimit remaining: %s" % ratelimit_remaining)
		self.pull_request = None
		self.repo_owner = None
		self.repo_name = None
		self.branch = None
		self.repo_path = None
		self.repo = None
		self.raw_diff = None
		self.file_changes = None
		self.gh_repo = None
		self.repo_path = None

	def handle_pr(self, pull_request_dict):
		# Build an object that encapsulates the Github Ppull request API
		self.pull_request = self._construct_pull_request(pull_request_dict)
		# Retrieve all information necessary to clone the repository
		clone_info = self._get_clone_info(pull_request_dict)
		self.repo_owner = clone_info['owner']
		self.repo_name = clone_info['name']
		self.branch = clone_info['branch']
		self.repo_path = os.path.join(self.repo_dir, self.repo_owner, self.repo_name)
		# Clone the repo / get a prviously cloned repository
		self.repo = self._get_repo(clone_info['clone_url'], self.branch)
		# Query Github for the pull request's diff
		self.raw_diff = self.pull_request.diff()
		# Find lines around changes
		self.file_changes = self.analyze_diff(self.raw_diff)
		# Find users that edited those lines
		self.blames = self.blame_changes(self.file_changes)
		# Git blame returns names and emails, query GH for the unique user logins
		self.result = self.connect_with_gh_logins(self.blames)
		# Create statistics of who should review
		return self.summarize(self.result)

	def _get_github_api(self):
		# TODO
		config_path = os.path.join(os.getcwd(), 'bot', 'gh_config.json')
		with open(config_path) as f:
			config = json.loads(f.read())
		return GitHub(config['login'], config['password'])

	def _construct_pull_request(self, pull_request_dict):
		pull_request = PullRequest.from_dict(pull_request_dict)
		pull_request.session = self.github.session
		logging.info('Handling PR #{number}: "{title}" ({html_url})'.format(
			number=pull_request.number,
			title=pull_request.title,
			html_url=pull_request.html_url))
		return pull_request

	def _get_clone_info(self, pull_request_dict):
		info = {}
		info['clone_url'] = pull_request_dict['head']['repo']['clone_url']
		info['owner'] = pull_request_dict['head']['repo']['owner']['login']
		info['name'] = pull_request_dict['head']['repo']['name']
		info['branch'] = pull_request_dict['head']['ref']
		logging.info('Clone info: %s' % info)
		return info

	def _is_git_dir(self, dir_path):
		return os.path.isdir(os.path.join(dir_path, '.git'))

	def _get_repo(self, clone_url=None, branch=None):
		if self._is_git_dir(self.repo_path):
			logging.info('"%s" is already a git repo.' % self.repo_path)
			repo = Repo(self.repo_path)
			logging.info('Currently on branch "%s"' % repo.active_branch.name)
			last_commit_sha = repo.active_branch.log_entry(0).newhexsha
			if last_commit_sha != self.pull_request.head.sha:
				logging.info('Repo is outdated. Switching to "%s" and pulling.' % self.branch)
				repo.git.pull('origin', self.branch)
				repo.git.checkout(self.branch)
			return repo
		else:
			# git clone --branch <branch> --single-branch --no-checkout --depth <n>
			logging.info('Cloning into %s' % self.repo_path)
			return Repo.clone_from(clone_url, self.repo_path,
				progress=self.progress,
				branch=branch)

	def analyze_diff(self, diff):
		def status(change):
			if change[0] is None:
				return 'insert'
			elif change[1] is None:
				return 'delete'
			else:
				return 'equal'
		out = []
		for hunk in whatthepatch.parse_patch(diff.decode('utf-8')):
			file_changes = []
			in_changeset = False
			for mode in [('insert',1), ('delete',0)]:
				for change in hunk.changes:
					if status(change) == mode[0] and not in_changeset:
						in_changeset = True
						file_changes.append({'start':change[mode[1]], 'type':mode[0]})
					elif status(change) == 'equal' and in_changeset:
						in_changeset = False
						file_changes[-1]['end'] = change[mode[1]]-1
			out.append({'header':hunk.header, 'changes':file_changes})
		return out

	def blame_changes(self, file_changes):
		insert_blames = self.blame_surrounding_lines(file_changes)
		delete_blames = self.blame_prev_rev_lines(file_changes)
		combined = {
			x: insert_blames.get(x, []) + delete_blames.get(x, [])
			for x in set(insert_blames).union(delete_blames)
		}
		return combined

	def blame_surrounding_lines(self, file_changes):
		out = {}
		for changeset in file_changes:
			file_path = changeset['header'].new_path
			logging.info('git blaming lines around inserts in %s' % file_path)
			changes = changeset['changes']
			inserts = [x for x in changes if x['type'] == 'insert']
			file_blames = []
			for insert in inserts:
				logging.debug('Blaming around %s' % insert)
				for line in [insert['start'] - 1, insert['end'] + 1]:
					commit_hash, author, timestamp = self.blame_line(line, file_path)
					previous = next((d for d in file_blames if d['commit'] == commit_hash), None)
					if previous:
						previous['lines'].add(line)
					else:
						file_blames.append({
							'commit':commit_hash,
							'lines':set([line]),
							'type':'insert',
							'author': author,
							'timestamp':timestamp})
			out[file_path] = file_blames
		return out

	def blame_prev_rev_lines(self, file_changes):
		out = {}
		for changeset in file_changes:
			file_path = changeset['header'].new_path
			logging.info('git blaming lines around deletions in %s' % file_path)
			changes = changeset['changes']
			deletions = [x for x in changes if x['type'] == 'delete']
			file_blames = []
			for deletion in deletions:
				logging.debug('Blaming around %s' % deletion)
				for line in range(deletion['start'], deletion['end']+1):
					commit_hash, author, timestamp = self.blame_line(line, file_path, prev_rev=self.pull_request.commits_count)
					previous = next((d for d in file_blames if d['commit'] == commit_hash), None)
					if previous:
						previous['lines'].add(line)
					else:
						file_blames.append({
							'commit':commit_hash, 
							'lines':set([line]),
							'type':'delete',
							'author': author,
							'timestamp':timestamp})
			out[file_path] = file_blames
		return out

	def blame_line(self, line, file_path, prev_rev=None):
		prev_rev_param = 'HEAD'
		if prev_rev is not None:
			prev_rev_param = 'HEAD~' + str(prev_rev)
		# git -C <repo_path> --no-pager blame -L<line>,+<range> HEAD~<prev> -l -- <file_path>
		blame_out = git('-C', self.repo_path, '--no-pager', 'blame', '-L' + str(line) + ',+1', prev_rev_param, '-p', '--', file_path)
		blame_split = blame_out.split('\n')
		commit_hash = blame_split[0].split(' ')[0]
		author = blame_split[1].split('author ')[1]
		timestamp = blame_split[3].split('author-time ')[1]
		logging.debug('Blame line %s: %s' % (line, commit_hash))
		return (commit_hash, author, timestamp)

	def get_github_login(self, sha):
		if not self.gh_repo:
			self.gh_repo = self.github.repository(self.repo_owner, self.repo_name)
		login = self.gh_repo.commit(sha).author.login
		return login

	def connect_with_gh_logins(self, blames):
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
			github_logins[author] = self.get_github_login(changes[0]['commit'])
		# print(github_logins)

		pr_changes = []
		for author, changes in reviewers.items():
			login = github_logins[author]
			for change in changes:
				change['login'] = login
				pr_changes.append(change)
		pprint(pr_changes)

		return pr_changes

	def summarize(self, pr_changes):
		get_attr = operator.itemgetter('login')
		# Have to sort before groupby
		pr_changes = sorted(pr_changes, key=get_attr)
		changes_count = [{'login':key, 'count':sum(1 for x in group)} for key, group in itertools.groupby(pr_changes, get_attr)]
		changes_count = sorted(changes_count, key=lambda x: x['count'], reverse=True)
		return changes_count
