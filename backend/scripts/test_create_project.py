import requests
import random
import time

BASE = 'http://127.0.0.1:8000'

def random_text():
    titles = [
        'Build Django REST API for e-commerce',
        'Frontend developer needed for React dashboard',
        'Data engineer for ETL pipeline',
        'Natural language processing expert to match resumes',
    ]
    descs = [
        'We need a developer experienced with Django, DRF, PostgreSQL and Docker. The project includes building endpoints for products, orders and authentication. Experience with Celery is a plus.',
        'Looking for a React developer to implement a modern dashboard. Requirements: React 18, Vite, TypeScript, charts and responsive design.',
        'Create an ETL pipeline to ingest CSV files, transform data and load into a data warehouse. Experience with Airflow or Prefect preferred.',
        'Develop an NLP pipeline to compute semantic similarity between job descriptions and candidate CVs. Use embeddings and cosine similarity.'
    ]
    i = random.randrange(len(titles))
    return titles[i], descs[i]


def main():
    title, description = random_text()
    payload = {
        'title': title,
        'description': description,
        'budget': '$500-$2000',
        'skills_required': 'django,rest,python',
        'deadline': None,
        'url': 'https://example.com/job/{}'.format(int(time.time())),
        'language': 'EN',
        'client': 'TestClient'
    }

    print('Creating project...')
    try:
        r = requests.post(BASE + '/api/projects/', json=payload, timeout=10)
    except Exception as e:
        print('Request failed:', e)
        return
    print('CREATE status:', r.status_code, 'content-type:', r.headers.get('content-type'))
    if 'application/json' in (r.headers.get('content-type') or ''):
        print(r.json())
    else:
        txt = r.text
        print(txt[:1000])
        if len(txt) > 1000:
            print('\n--- response truncated; check server logs for full traceback ---')
    if r.status_code not in (200,201):
        return
    obj = r.json()
    pid = obj.get('id')
    if not pid:
        print('No id returned; exiting')
        return

    print('\nComputing score...')
    try:
        r2 = requests.post(f"{BASE}/api/projects/{pid}/compute_score/", json={'skills': payload['skills_required']}, timeout=10)
    except Exception as e:
        print('Request failed:', e)
        return
    print('SCORE status:', r2.status_code, 'content-type:', r2.headers.get('content-type'))
    if 'application/json' in (r2.headers.get('content-type') or ''):
        print(r2.json())
    else:
        print(r2.text[:1000])


    print('\nGenerating cover letter...')
    try:
        r3 = requests.post(f"{BASE}/api/projects/{pid}/generate_cover/", json={'skills': payload['skills_required']}, timeout=20)
    except Exception as e:
        print('Request failed:', e)
        return
    print('COVER status:', r3.status_code, 'content-type:', r3.headers.get('content-type'))
    if 'application/json' in (r3.headers.get('content-type') or ''):
        print(r3.json())
    else:
        txt = r3.text
        print(txt[:1000])
        if len(txt) > 1000:
            print('\n--- response truncated; check server logs for full traceback ---')

if __name__ == '__main__':
    main()
