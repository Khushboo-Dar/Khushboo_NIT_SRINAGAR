import requests
import json
import time

API_URL = "https://khushboo-nit-srinagar.onrender.com/extract-bill-data"
PAYLOAD = {
    "document": "https://templates.invoicehome.com/invoice-template-us-neat-750px.png"
}

print(f"Connecting to: {API_URL}")
print("Waiting for response...")

start_time = time.time()

try:
    response = requests.post(API_URL, json=PAYLOAD, timeout=300)
    duration = time.time() - start_time

    if response.status_code == 200:
        print(f"\nSuccess (Time: {duration:.2f}s)")
        print("=" * 60)
        data = response.json()
        print(json.dumps(data, indent=2))

        if "token_usage" in data and "page_type" in data["data"]["pagewise_line_items"][0]:
            print("\nCheck Passed: token_usage and page_type exist.")
        else:
            print("\nWarning: Response schema may be outdated.")
    else:
        print(f"\nFailed: Status {response.status_code}")
        print("Response:", response.text)

except Exception as e:
    print(f"\nConnection Error: {e}")
