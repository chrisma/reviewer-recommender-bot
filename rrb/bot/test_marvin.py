import unittest, json, codecs, os
from marvin import Marvin

repo_storage_dir = '/home/christoph/git/reviewer-recommender-bot/repos'

class MarvinTest(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		super(MarvinTest, self).__init__(*args, **kwargs)
		self.test_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_data')
		self.marvin = Marvin(repo_dir=repo_storage_dir)

	def read(self, file):
		with open(os.path.join(self.test_data_dir, file), 'rb') as f:
			return f.read()

class TestDiffModifiedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('modify.diff'))
		self.line_number = 40

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 1)

	def test_header(self):
		header = self.file_changes[0]['header']
		self.assertEqual(header.old_path, 'Gemfile')
		self.assertEqual(header.new_path, 'Gemfile')

	def test_changes(self):
		changes = self.file_changes[0]['changes']
		actual = [	{'start': self.line_number, 'type': 'insert', 'end': self.line_number},
					{'start': self.line_number, 'type': 'delete', 'end': self.line_number}]
		self.assertCountEqual(actual, changes)

class TestDiffAppendedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('append.diff'))
		self.line_number = 113

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 1)

	def test_header(self):
		header = self.file_changes[0]['header']
		self.assertEqual(header.old_path, 'Gemfile')
		self.assertEqual(header.new_path, 'Gemfile')

	def test_changes(self):
		changes = self.file_changes[0]['changes']
		actual = [{'start': self.line_number, 'end': self.line_number, 'type': 'insert'}]
		self.assertCountEqual(actual, changes)

class TestDiffMultipleAppendedLines(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('multiple_appends.diff'))

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 2)

	def test_header(self):
		headers_old_paths = [change['header'].old_path for change in self.file_changes]
		self.assertCountEqual(['Gemfile', 'README.md'], headers_old_paths)
		headers_new_paths = [change['header'].new_path for change in self.file_changes]
		self.assertCountEqual(['Gemfile', 'README.md'], headers_new_paths)

	def test_change_file1(self):
		file1_changes = [c['changes'] for c in self.file_changes if c['header'].new_path=='Gemfile'].pop()
		# lines 117 to 125 appended
		file1_actual = [{'start': 117, 'end': 125, 'type': 'insert'}]
		self.assertCountEqual(file1_actual, file1_changes)

	def test_change_file2(self):
		file2_changes = [c['changes'] for c in self.file_changes if c['header'].new_path=='README.md'].pop()
		# lines 115 to 127 appended
		file2_actual = [{'start': 115, 'end': 127, 'type': 'insert'}]
		self.assertCountEqual(file2_actual, file2_changes)

class TestDiffPrependedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('prepend.diff'))
		self.line_number = 1

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 1)

	def test_header(self):
		header = self.file_changes[0]['header']
		self.assertEqual(header.old_path, 'Gemfile')
		self.assertEqual(header.new_path, 'Gemfile')

	def test_changes(self):
		changes = self.file_changes[0]['changes']
		actual = [{'start': self.line_number, 'end': self.line_number, 'type': 'insert'}]
		self.assertCountEqual(actual, changes)

class TestDiffDeletedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('delete.diff'))
		self.line_number = 37

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 1)

	def test_header(self):
		header = self.file_changes[0]['header']
		self.assertEqual(header.old_path, 'Gemfile')
		self.assertEqual(header.new_path, 'Gemfile')

	def test_changes(self):
		changes = self.file_changes[0]['changes']
		actual = [{'start': self.line_number, 'end': self.line_number, 'type': 'delete'}]
		self.assertCountEqual(actual, changes)

class TestDiffMultipleEdits(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('multiple_edits.diff'))

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 1)

	def test_header(self):
		header = self.file_changes[0]['header']
		self.assertEqual(header.old_path, 'Gemfile')
		self.assertEqual(header.new_path, 'Gemfile')

	def test_prepend(self):
		changes = self.file_changes[0]['changes']
		# line 1 prepended
		self.assertIn({'start': 1, 'end': 1, 'type': 'insert'}, changes)

	def test_modify(self):
		changes = self.file_changes[0]['changes']
		#line 58 (now 59) modified
		actual = [	{'start': 58, 'end': 58, 'type': 'delete'},
					{'start': 59, 'end': 59, 'type': 'insert'}]
		for elem in actual:
			self.assertIn(elem, changes)

	def test_append(self):
		changes = self.file_changes[0]['changes']
		#lines 118, 119 appended.
		self.assertIn({'start': 118, 'end': 119, 'type': 'insert'}, changes)

class TestDiffMultipleFiles(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('multiple_files.diff'))

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 2)

	def test_header(self):
		headers_old_paths = [change['header'].old_path for change in self.file_changes]
		self.assertCountEqual(['Gemfile', 'README.md'], headers_old_paths)
		headers_new_paths = [change['header'].new_path for change in self.file_changes]
		self.assertCountEqual(['Gemfile', 'README.md'], headers_new_paths)

	def test_changes_file1(self):
		file1_changes = [c['changes'] for c in self.file_changes if c['header'].new_path=='Gemfile'].pop()
		# line 1 prepended, line 37 (now 38) and line 40 (now 41) modified
		file1_actual = [{'start': 1, 'end': 1, 'type': 'insert'},
					{'start': 37, 'end': 37, 'type': 'delete'},
					{'start': 38, 'end': 38, 'type': 'insert'},
					{'start': 40, 'end': 40, 'type': 'delete'},
					{'start': 41, 'end': 41, 'type': 'insert'}]
		self.assertCountEqual(file1_actual, file1_changes)

	def test_changes_file2(self):
		file2_changes = [c['changes'] for c in self.file_changes if c['header'].new_path=='README.md'].pop()
		# Inserted lines 25 and 26
		file2_actual = [{'start': 25, 'end': 26, 'type': 'insert'}]
		self.assertCountEqual(file2_actual, file2_changes)

class TestDiffLarge(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('pr_338.diff'))

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 15)

	def test_selected_changes(self):
		changes = [c['changes'] for c in self.file_changes if c['header'].new_path=='app/controllers/work_days_controller.rb'].pop()
		actual = [
			{'end': 16, 'start': 11, 'type': 'delete'},
			{'end': 24, 'start': 11, 'type': 'insert'},
			{'end': 20, 'start': 19, 'type': 'delete'},
			{'end': 27, 'start': 27, 'type': 'insert'},
			{'end': 32, 'start': 32, 'type': 'insert'},
			{'end': 37, 'start': 37, 'type': 'insert'},
			{'end': 59, 'start': 59, 'type': 'delete'},
			{'end': 68, 'start': 68, 'type': 'insert'},
			{'end': 76, 'start': 73, 'type': 'delete'},
			{'end': 78, 'start': 78, 'type': 'delete'},
			{'end': 83, 'start': 83, 'type': 'insert'}
		]
		self.assertCountEqual(actual, changes)

if __name__ == '__main__':
	unittest.main()