import os
import django
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

c = Client()
# create a dummy project if none exists
from projects.models import Project
p = Project.objects.first()
if not p:
    p = Project(title='Test project', description='Test desc', skills_required='Data Entry')
    p.save()

url = f"/api/projects/{p.id}/generate_cover/"
resp = c.post(url, {'skills': p.skills_required, 'mode': 'deepseak'})
print('status_code=', resp.status_code)
print('content=', resp.content.decode('utf-8'))
