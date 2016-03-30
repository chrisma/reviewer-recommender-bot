import codecs, json, os, codecs, logging
from pprint import pprint
from collections import namedtuple
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
		logging.info("Ratelimit remaining:  %s" % self.github.ratelimit_remaining)
		self.gh_repo = None
		self.pull_request = None
		self.repo_path = None

	def _get_github_api(self):
		# TODO
		config_path = os.path.join(os.getcwd(), 'bot', 'gh_config.json')
		with open(config_path) as f:
			config = json.loads(f.read())
		return GitHub(config['login'], config['password'])

	def handle_pr(self, pull_request_dict):
		pull_request = PullRequest.from_dict(pull_request_dict)
		pull_request.session = self.github.session
		self.pull_request = pull_request
		logging.info('Handling PR #{number}:{title} ({html_url})'.format(
			number=pull_request.number,
			title=pull_request.title,
			html_url=pull_request.html_url))

		clone_info = self._get_clone_info(pull_request_dict)
		self.repo_owner = clone_info['owner']
		self.repo_name = clone_info['name']
		self.repo_path = os.path.join(self.repo_dir, self.repo_owner, self.repo_name)
		self.repo = self._get_repo(clone_info['clone_url'], clone_info['branch'])
		self.diff = self.analyze_diff(diff_url=pull_request_dict['diff_url'])

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
			return Repo(self.repo_path)
		else:
			# git clone --branch <branch> --single-branch --no-checkout --depth <n>
			logging.info('Cloning into %s' % self.repo_path)
			return Repo.clone_from(clone_url, self.repo_path,
				progress=self.progress,
				branch=branch)

	def analyze_diff(self, diff_url=None, diff_path=None):
		diff = self.pull_request.diff()
		return self._process_diff(diff)

	def _process_diff(self, diff):
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


if __name__ == "__main__":
		# import pdb; pdb.set_trace()
	# print('Using an example pull request')
	# path = '338.json'
	# print('Loading pr from:', path)
	# with codecs.open(path, 'r', encoding='utf-8') as f:
	# 	pr = json.loads(f.read())
	# bot = Marvin(pr, repo_dir='repos')

	# print('*'*20)
	# print(bot.repo.working_dir)
	# print(bot.repo.description)
	# print(bot.repo.active_branch)
	# print('*'*20)
	# pprint(bot.get_changes())

	# rev = 'd34b7de78259a2e83ec7cfc16bff084ad1d4685c'
	# file = 'app/assets/stylesheets/application.css'
	# blame_infos = bot.repo.blame(rev, file)
	# [
	#  [<git.Commit "c78b9c1c0a57cc62505a377726f000b00c2e8f66">,
	#	['    background-color: #FFFFFF;']],
	#  [<git.Commit "b57effdfe706d5b24b53cc780395ea9bfc5fcab8">,
	#	['    padding: 15px;']]
	# ]

	# pprint(blame_infos)

	logging.basicConfig(level=logging.WARNING)
	logging.getLogger('sh').setLevel(logging.WARNING)

	marvin = Marvin()
	file_changes = marvin.analyze_diff(diff_path='338.diff')
	marvin.number_commits = 3
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

	to_query = []
	for author, changes in reviewers.items():
		to_query.append((author, changes[0]['commit']))
	print(to_query)

	# from github3 import GitHub
	# with open('gh_config.json') as f:
	# 	config = json.loads(f.read())
	# gh = GitHub(config['login'], config['password'])





	# single_file_changes = [x for x in file_changes if x['header'].new_path == 'spec/views/work_days/index.html.erb_spec.rb'][0]
	# single_file_changes = [x for x in file_changes if x['header'].new_path == 'app/controllers/work_days_controller.rb'][0]
	# pprint(single_file_changes)
	# pprint(blame)

	# insert_blames = marvin.blame_surrounding_lines(file_changes)
	# delete_blames = marvin.blame_prev_rev_lines(file_changes)
	# pprint(insert_blames)
	# pprint(delete_blames)

	# combined = {
	# 	x: insert_blames.get(x, []) + delete_blames.get(x, [])
	# 	for x in set(insert_blames).union(delete_blames)
	# }
	# pprint(combined)

	# https://api.github.com/repos/hpi-swt2/wimi-portal/commits?path=app/controllers/work_days_controller.rb&sha=feature/288_timesheet
