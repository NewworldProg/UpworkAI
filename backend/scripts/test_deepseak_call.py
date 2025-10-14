from backend.projects.deepseak_client import DeepSeakClient

c = DeepSeakClient()
print('api_url=', c.api_url)
try:
    r = c.generate('Hello world', max_tokens=10, temperature=0.1)
    print('RESP=', r)
except Exception as e:
    print('ERR:', e)
