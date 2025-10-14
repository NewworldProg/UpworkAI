import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from projects.cover_generator import CoverGenerator
cg = CoverGenerator()
try:
    res, provider = cg.generate('Test project description for Ollama', 'python, django', job_title='Test', only_backend='ollama', return_provider=True)
    print('PROVIDER:', provider)
    print('OK:', bool(res))
    if res:
        print(res[:800])
except Exception as e:
    print('ERROR:', e)
