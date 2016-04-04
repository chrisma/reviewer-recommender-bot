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

class TestDiffParsingWithModifiedLine(MarvinTest):
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

class TestDiffParsingWithAppendedLine(MarvinTest):
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

class TestDiffParsingWithPrependedLine(MarvinTest):
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

class TestDiffParsingWithDeletedLine(MarvinTest):
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

if __name__ == '__main__':
	unittest.main()