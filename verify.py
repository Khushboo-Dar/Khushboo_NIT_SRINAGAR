import requests
import json

file_name = "train_sample_14.pdf"
url = "http://localhost:8000/extract-bill-data"
payload = {"document": f"http://localhost:9000/{file_name}"}

print(f"Testing {file_name}...")
res = requests.post(url, json=payload)

if res.status_code == 200:
    print("Success")
    print(json.dumps(res.json(), indent=2))
else:
    print(f"Error {res.status_code}: {res.text}")
