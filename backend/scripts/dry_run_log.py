from backend.projects.cover_generator import CoverGenerator
import os

cg = CoverGenerator()
logs_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
print('expected logs_dir=', logs_dir)
# create dir and a sample entry
os.makedirs(logs_dir, exist_ok=True)
with open(os.path.join(logs_dir, 'ai_usage.log'), 'a', encoding='utf-8') as fh:
    fh.write('TEST\tdeepseak\t_simulation\n')
print('wrote sample log entry')
