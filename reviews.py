import codecs, json, os, codecs
from pprint import pprint
from git import Repo
from git.remote import RemoteProgress
from requests import get
import whatthepatch
# from unidiff import PatchSet

class Marvin(object):
	"""Merely A ReView INcentivizer """
	def __init__(self, pull_request, repo_storage_path):
		class ProgressHandler(RemoteProgress):
			def line_dropped(self, line):
				print(line)
			def update(self, *args):
				print(self._cur_line)
		print('Marvin started!')
		self.repo_storage_path = os.path.abspath(repo_storage_path)
		print('Storing repos to:', self.repo_storage_path)
		self.ProgressHandler = ProgressHandler()
		repo_info = self._parse_github_pull_request(pull_request)
		print('Repo info:', repo_info)
		# self.repo = self._get_repo(**repo_info)
		self.diff = self.analyze_diff(pull_request['diff_url'])

	def _parse_github_pull_request(self, pull_request):
		print('PR', pull_request['number'], ':', pull_request['title'])
		print('html_url:', pull_request['html_url'])
		clone_url = pull_request['head']['repo']['clone_url']
		full_name = pull_request['head']['repo']['full_name']
		branch = pull_request['head']['ref']
		return {'full_name': full_name, 
				'clone_url': clone_url,
				'branch': branch}

	def _get_repo(self, full_name, clone_url=None, branch=None):
		repo_path = os.path.join(self.repo_storage_path, full_name)
		if os.path.isdir(os.path.join(repo_path, '.git')):
			print(full_name, 'was already cloned.')
			return Repo(repo_path)
		else:
			return self._clone_repo(clone_url, full_name, branch)

	def _clone_repo(self, clone_url, full_name, branch):
		# depth = 1
		return Repo.clone_from(clone_url, clone_path,
			progress=self.ProgressHandler,
			branch=branch)
			# depth=depth)

class Helper(object):
	def analyze_diff(self, diff_url=None, diff_path=None):
		if diff_url is not None:
			print('Fetching diff from:', diff_url)
			diff = get(diff_url).text
		elif diff_path is not None:
			print('Reading local diff from:', diff_path)
			with open(diff_path) as f:
				diff = f.read()
		else:
			raise Exception('Have to provide either diff_url or diff_path parameter!')
		return self.process_diff(diff)

	def process_diff(self, diff):
		def status(change):
			if change[0] is None:
				return 'insert'
			elif change[1] is None:
				return 'delete'
			else:
				return 'equal'

		hunk = list(whatthepatch.parse_patch(diff))
		hunk = hunk[1]
		# import pdb; pdb.set_trace()
		out = []
		in_changeset = False
		for change in hunk.changes:
			if status(change) == 'insert' and not in_changeset:
				in_changeset = True
				out.append({'start':change[1], 'type':'insert'})
			elif status(change) == 'delete' and not in_changeset:
				in_changeset = True
				out.append({'start':change[0], 'type':'delete'})
			elif status(change) == 'equal' and in_changeset:
				in_changeset = False
				if out[-1]['type'] == 'insert':
					out[-1]['end'] = change[1]-1
				else:
					out[-1]['end'] = change[0]-1
		return out


		# for hunk in whatthepatch.parse_patch(diff):
			# print(hunk.changes)


if __name__ == "__main__":
	# print('Using an example pull request')
	# path = '338.json'
	# print('Loading pr from:', path)
	# with codecs.open(path, 'r', encoding='utf-8') as f:
	# 	pr = json.loads(f.read())
	# bot = Marvin(pr, repo_storage_path='repos')

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

	changeset = Helper().analyze_diff(diff_path='338.diff')
	print(changeset)

	# what = list(whatthepatch.parse_patch(text))
	# pprint(what[1].changes)
	# for diff in what:
		# print(diff)
	# import pdb; pdb.set_trace()
	# with codecs.open('338.diff', 'r', encoding='utf-8') as diff:
		# patch = PatchSet(diff)