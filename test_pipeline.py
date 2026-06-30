import urllib.request
import json
req = urllib.request.Request(
    "http://localhost:8000/api/leads/auto-generate",
    data=json.dumps({"query": "cafes google maps"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except Exception as e:
    print(f"Error: {e}")
