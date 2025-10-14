import os
import sys
import django
from pathlib import Path

# Ensure the repository root is on sys.path so 'backend' package is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from projects.models import Project
from django.utils import timezone

# Snippet to search for (from user's pasted cover letter)
SNIPPET = 'We are seeking an experienced professional to assist in forming a USA-based company and obtaining a merchant account'

print('Searching Projects for cover_letter containing snippet...')
qs = Project.objects.filter(cover_letter__icontains=SNIPPET)
if not qs.exists():
    print('No exact matches found. Trying a shorter snippet search...')
    short = 'forming a USA-based company'
    qs = Project.objects.filter(cover_letter__icontains=short)

if not qs.exists():
    print('No projects found matching the provided cover letter snippet.')
else:
    print(f'Found {qs.count()} matching project(s):')
    for p in qs:
        print('---')
        print('id=', p.id)
        print('title=', p.title)
        print('status=', p.status)
        print('tos_safe=', p.tos_safe)
        print('updated_at=', p.updated_at)
        cl = (p.cover_letter or '').replace('\n', ' ')
        print('cover_letter_snippet=', cl[:400])

# Show the last 50 lines of ai_usage.log if present
logs_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
log_path = os.path.join(logs_dir, 'ai_usage.log')
print('\nChecking ai_usage.log for recent DeepSeak usage (last 2000 chars):')
if os.path.exists(log_path):
    try:
        with open(log_path, 'r', encoding='utf-8') as fh:
            data = fh.read()
            print(data[-2000:])
    except Exception as e:
        print('Could not read log file:', e)
else:
    print('No ai_usage.log found at', log_path)
