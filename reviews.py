import codecs, json, os
from pprint import pprint
from git import Repo
from git.remote import RemoteProgress

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
		pr_info = self._parse_github_pull_request(pull_request)
		print('PR infos:', pr_info)
		self.repo = self._get_repo(**pr_info)

	def _parse_github_pull_request(self, pull_request):
		print('number:', pull_request['number'])
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

if __name__ == "__main__":
	print('Using an example pull request')
	path = '338.json'
	print('Loading pr from:', path)
	with codecs.open(path, 'r', encoding='utf-8') as f:
		pr = json.loads(f.read())
	bot = Marvin(pr, repo_storage_path='repos')

	print('*'*20)
	print(bot.repo.working_dir)
	print(bot.repo.description)
	print(bot.repo.active_branch)
