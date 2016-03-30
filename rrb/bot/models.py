from django.db import models
from jsonfield import JSONField

class GitHubPullRequest(models.Model):
	"""Encapsulates a Pull Request on Github"""
	created_at = models.DateTimeField(auto_now_add=True)
	reviewer_count = models.IntegerField(blank=True, null=True)
	pull_request_json = JSONField(blank=True, null=True)

	class Meta:
		verbose_name = 'Pull Request'
		verbose_name_plural = 'Pull Requests'

	def __str__(self):
		if self.pull_request_json:
			name = self.pull_request_json['title']
		else:
			name = 'EMPTY'
		return name

class Change(models.Model):
	"""Encapsulates a deletion / insertion"""
	login = models.CharField(max_length=50, blank=True)
	sha = models.CharField(max_length=50, blank=True)
	file_path = models.CharField(max_length=50, blank=True)
	type = models.CharField(max_length=50, blank=True)
	timestamp = models.DateTimeField(blank=True)
	lines = models.TextField(blank=True)
	pull_request = models.ForeignKey(GitHubPullRequest)

	class Meta:
		verbose_name = 'Change'
		verbose_name_plural = 'Changes'

	def __str__(self):
		return login + ' ' + sha