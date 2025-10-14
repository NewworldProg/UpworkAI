import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

from projects.cover_generator import CoverGenerator

# Simple test prompt
PROJECT_DESC = 'We are seeking an experienced professional to assist in forming a USA-based company and obtaining a merchant account for our ecommerce business.'
SKILLS = 'Accounting, e-commerce, payments'

cg = CoverGenerator()

backends = ['openai', 'deepseak', 'local', 'ollama']

logs_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
os.makedirs(logs_dir, exist_ok=True)
log_path = os.path.join(logs_dir, 'backend_test_results.log')

with open(log_path, 'a', encoding='utf-8') as fh:
    fh.write('--- Backend test run ---\n')
    for b in backends:
        fh.write(f'Testing backend: {b}\n')
        try:
            res, provider = cg.generate(PROJECT_DESC, SKILLS, only_backend=b, return_provider=True)
            ok = bool(res and res.strip())
            fh.write(f'  provider={provider} ok={ok}\n')
            if ok:
                fh.write('  sample=' + res.strip()[:400].replace('\n', ' ') + '\n')
        except Exception as e:
            fh.write(f'  ERROR calling {b}: {e}\n')
    fh.write('\n')

print('Wrote results to', log_path)
