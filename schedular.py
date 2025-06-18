import requests

url = "http://127.0.0.1:9000/get_attendance"

try:
    response = requests.get(url)
    print(f"Response [{response.status_code}]: {response.text}")
except Exception as e:
    print(f"Error occurred: {e}")
