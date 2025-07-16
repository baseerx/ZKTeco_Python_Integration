import requests

url = "http://127.0.0.1:9000/clear_old_attendance"

# Always clear the log file
with open("app.log", "w") as log_file:
    log_file.truncate(0)

try:
    response = requests.get(url)
    print(f"Response [{response.status_code}]: {response.text}")
except Exception as e:
    print(f"Error occurred: {e}")
