import unittest, json, codecs, os
from collections import namedtuple
from reviews import Marvin

class TestDiffParsing(unittest.TestCase):
	def setUp(self):
		self.diff_path = 'test.diff'
		self.file = 'test.rb'
		self.result = [
			{'end': 24, 'start': 11, 'type': 'insert'},
			{'end': 27, 'start': 27, 'type': 'insert'},
			{'end': 32, 'start': 32, 'type': 'insert'},
			{'end': 37, 'start': 37, 'type': 'insert'},
			{'end': 68, 'start': 68, 'type': 'insert'},
			{'end': 83, 'start': 83, 'type': 'insert'},
			{'end': 16, 'start': 11, 'type': 'delete'},
			{'end': 20, 'start': 19, 'type': 'delete'},
			{'end': 59, 'start': 59, 'type': 'delete'},
			{'end': 76, 'start': 73, 'type': 'delete'},
			{'end': 78, 'start': 78, 'type': 'delete'}
		]

	def test_real_diff(self):
		all_changes = Marvin().analyze_diff(diff_path=self.diff_path)
		file_changes = [x['changes'] for x in all_changes if x['header'].new_path == self.file][0]
		self.assertListEqual(file_changes, self.result)

class TestPullRequestParsing(unittest.TestCase):
	def setUp(self):
		path = '338.json'
		with codecs.open(path, 'r', encoding='utf-8') as f:
			self.pr = json.loads(f.read())
		self.result = {
			'full_name': 'hpi-swt2/wimi-portal',
			'clone_url': 'https://github.com/hpi-swt2/wimi-portal.git',
			'branch': 'feature/288_timesheet'}

	def test_real_pr(self):
		repo_info = Marvin()._parse_github_pull_request(self.pr)
		self.assertDictEqual(repo_info, self.result)

class TestBlame(unittest.TestCase):
	def setUp(self):
		header = namedtuple('header', ['index_path', 'old_path', 'old_version', 'new_path', 'new_version'])
		self.file_changes = [
			{'changes': [
				{'end': 24, 'start': 11, 'type': 'insert'},
				{'end': 27, 'start': 27, 'type': 'insert'},
				{'end': 32, 'start': 32, 'type': 'insert'},
				{'end': 37, 'start': 37, 'type': 'insert'},
				{'end': 68, 'start': 68, 'type': 'insert'},
				{'end': 83, 'start': 83, 'type': 'insert'},
				{'end': 16, 'start': 11, 'type': 'delete'},
				{'end': 20, 'start': 19, 'type': 'delete'},
				{'end': 59, 'start': 59, 'type': 'delete'},
				{'end': 76, 'start': 73, 'type': 'delete'},
				{'end': 78, 'start': 78, 'type': 'delete'}],
			'header': header(
				index_path=None,
				old_path='app/controllers/work_days_controller.rb',
				old_version='6ace82e',
				new_path='app/controllers/work_days_controller.rb',
				new_version='70629c2')}
		]
		self.result = {'app/controllers/work_days_controller.rb': {
			'04fe0c5b7a3cbad49c6847e302591a1b7c6dc8d9': [82,84],
			'0c82d240f32026caf6c6238d1d7204e7766f723a': [25],
			'2b573f4afeac83a59b741483fc067839d952bd5c': [67],
			'8342fefcf6d5e8cb4d834a95576b4237768fcd80': [10,31,33,36,38,69],
			'b21818bd1be06f959c5fb9916112c6889ab8f9fc': [26,28]}
		}

	def test_real_file_changes(self):
		blame = Marvin().blame_surrounding_lines(self.file_changes)
		self.assertDictEqual(blame, self.result)


if __name__ == '__main__':
	unittest.main()