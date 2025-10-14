import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from projects.cover_models.ollama_client import OllamaClient
import os

os.environ['OLLAMA_MODEL'] = 'mistral:7b'
client = OllamaClient()
print(f"Model: {client.model}")
print(f"Base URL: {client.base_url}")

try:
    result = client.generate("Write a short cover letter for a Python developer position.", max_tokens=200)
    print("SUCCESS:")
    print(result)
except Exception as e:
    print("ERROR:")
    print(e)