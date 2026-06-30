import urllib.request
req = urllib.request.Request('http://localhost:8000/api/leads/', method='DELETE')
try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except Exception as e:
    print(f"Error: {e}")
