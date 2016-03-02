import unittest
from reviews import Helper

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
		all_changes = Helper().analyze_diff(diff_path=self.diff_path)
		file_changes = [x['changes'] for x in all_changes if x['header'].new_path == self.file][0]
		self.assertListEqual(file_changes, self.result)

if __name__ == '__main__':
	unittest.main()