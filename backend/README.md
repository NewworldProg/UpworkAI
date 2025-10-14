# Backend (Django)

Quickstart (Windows PowerShell):

1. Create virtualenv and activate:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install requirements:

```powershell
pip install -r requirements.txt
```

3. Run migrations and start server:

```powershell
python manage.py migrate; python manage.py runserver
```

Environment variables:
- OPENAI_API_KEY (optional) - for cover letter generation
- MONDAY_API_KEY (optional) - for Monday.com integration

Notes:
- If you want to enable OpenAI cover-letter generation, set OPENAI_API_KEY and install the `openai` package.
- Monday.com integration is a stub; to enable real integration, provide MONDAY_API_KEY and implement GraphQL calls in `projects.services.create_monday_task`.

OpenAI configuration:
- `OPENAI_API_KEY` - set to your OpenAI API key to enable generation.
- `OPENAI_MODEL` - optional, model to use (defaults to `gpt-3.5-turbo`). Use `gpt-4` if available.

Background processing recommendation:
- Heavy or rate-limited AI calls should be moved to a background worker (Celery, RQ, or similar). The repository provides `generate_cover_letter` (sync) and `generate_cover_letter_async` placeholder; replace or enqueue these as needed.


Creating admin user:

```powershell
python manage.py createsuperuser
```

Notes about CORS: If you run the frontend on a different port, configure CORS in Django (e.g., install `django-cors-headers`).


