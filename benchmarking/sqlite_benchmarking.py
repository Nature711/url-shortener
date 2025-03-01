import time
import random
import string
import requests

BASE_URL_V1 = "http://127.0.0.1:5002"  # File-based version
BASE_URL_V2 = "http://127.0.0.1:5003"  # SQLite-based version

N = 10000  # Number of requests for benchmarking

# Generate random URLs
def random_url():
    return "example.com/" + "".join(random.choices(string.ascii_letters, k=10))

urls = [random_url() for _ in range(N)]


### **File-based service test (service-v1-1.py)**
print("\n### Testing File-based Service ###")

# Insert URLs
start_time = time.time()
for url in urls:
    requests.post(f"{BASE_URL_V1}/create", params={"long_url": url})
file_insert_time = time.time() - start_time

# Read URLs
start_time = time.time()
for url in urls:
    short_url = requests.post(f"{BASE_URL_V1}/create", params={"long_url": url}).json().get("short_url")
    requests.get(f"{BASE_URL_V1}/get", params={"short_url": short_url})
file_read_time = time.time() - start_time


### **SQLite-based service test (service-v2.py)**
print("\n### Testing SQLite-based Service ###")

# Insert URLs
start_time = time.time()
for url in urls:
    requests.post(f"{BASE_URL_V2}/create", params={"long_url": url})
sqlite_insert_time = time.time() - start_time

# Read URLs
start_time = time.time()
for url in urls:
    short_url = requests.post(f"{BASE_URL_V2}/create", params={"long_url": url}).json().get("short_url")
    requests.get(f"{BASE_URL_V2}/get", params={"short_url": short_url})
sqlite_read_time = time.time() - start_time


### **Results**
print("\n### Benchmark Results ###")
print(f"File-based Insert Time: {file_insert_time:.4f}s")
print(f"File-based Read Time: {file_read_time:.4f}s")
print(f"SQLite Insert Time: {sqlite_insert_time:.4f}s")
print(f"SQLite Read Time: {sqlite_read_time:.4f}s")
