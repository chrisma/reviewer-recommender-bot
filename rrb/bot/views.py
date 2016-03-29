from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from pprint import pprint
import json
import logging
from .models import GitHubPullRequest

@csrf_exempt
def pull_request(request):
	if request.method != 'POST':
		return HttpResponse("HALLO")

	body = json.loads(request.body.decode('utf-8'))
	if body['action'] == 'opened':
		logging.info('Open PR: ' + body['pull_request']['html_url'])
		pr = GitHubPullRequest(reviewer_count=2, pull_request_json=body['pull_request'])
		pr.save()
		return HttpResponse("Thanks")

