import requests
import json
import time

# Give the server a few seconds to start
time.sleep(3)

url = "http://127.0.0.1:8000/api/chat"
payload = {
  "machine_id": 1,
  "question": "What are the common causes of abnormal vibration in industrial equipment and what maintenance actions are recommended?",
  "message": "string",
  "top_k": 5
}
headers = {'Content-Type': 'application/json'}

print(f"POST {url}")
try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
