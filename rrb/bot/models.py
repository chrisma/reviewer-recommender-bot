from django.db import models
from jsonfield import JSONField

# Create your models here.
class GitHubPullRequest(models.Model):
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