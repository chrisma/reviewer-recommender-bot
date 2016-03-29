from django.db import models
from jsonfield import JSONField

# Create your models here.
class GitHubPullRequest(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	reviewer_count = models.IntegerField()
	# blank=True, null=True
	pull_request_json = JSONField(default={})
	diff = models.TextField(blank=True)

	class Meta:
		verbose_name = 'Pull Request'
		verbose_name_plural = 'Pull Requests'

	def __str__(self):
		return str(self.created_at) + str(self.reviewer_count)