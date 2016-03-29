from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe

from .models import GitHubPullRequest

# Register your models here.

class FancyDictWidget(forms.Textarea):
    class Media:
        js = ('prettyprint.js',)

    def __init__(self, *args, **kwargs):
        self.selector = kwargs.pop('selector')
        super(FancyDictWidget, self).__init__(*args, **kwargs)
    
    def render(self, name, value, attrs):
        output = super(FancyDictWidget, self).render(name, value, attrs)
        script = ''
        if self.selector is not None:
            script += u'<script type="text/javascript">\n'
            script += u'  (function($) {{\n'
            script += u'    $(document).ready(function(){{\n'
            script += u'      var {selector}_config = {{expanded: false, maxDepth: 1}};\n'
            script += u'      var {selector}_node = $("[name={selector}]");\n'
            script += u'      var {selector}_table = prettyPrint(JSON.parse({selector}_node.val()), {selector}_config);\n'
            script += u'      {selector}_node.siblings("p.help").remove();\n'
            script += u'      {selector}_node.css("display", "none");\n'
            script += u'      {selector}_node.before({selector}_table);\n'
            script += u'    }});\n'
            script += u'  }})(django.jQuery);\n'
            script += u'</script>'
            script = script.format(selector=self.selector)
        return mark_safe(output + script)

class FancyDictForm(forms.ModelForm):
    class Meta:
        fields = '__all__'
        model = GitHubPullRequest
        widgets = {
            'pull_request_json': FancyDictWidget(selector="pull_request_json")
        }

class GitHubPullRequestAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at","id",)
    form = FancyDictForm

admin.site.register(GitHubPullRequest, GitHubPullRequestAdmin)