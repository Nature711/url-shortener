import time
import random
import string
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor

def random_url():
    """Generate a random URL."""
    return "example.com/" + "".join(random.choices(string.ascii_letters, k=10))


def insert_url(base_url, url):
    """Send a POST request to shorten a URL."""
    try:
        response = requests.post(f"{base_url}/create", params={"long_url": url}, timeout=3)
        if response.status_code == 200:
            return response.json().get("short_url")
    except requests.exceptions.RequestException:
        return None


def fetch_url(base_url, short_url):
    """Send a GET request to retrieve the original URL."""
    try:
        response = requests.get(f"{base_url}/get", params={"short_url": short_url}, timeout=3)
        if response.status_code == 200:
            return response.json().get("long_url")
    except requests.exceptions.RequestException:
        return None


def benchmark_service(base_url, num_requests):
    print(f"\n### Benchmarking {base_url} | {num_requests} Requests | Parallel Execution ###")

    urls = [random_url() for _ in range(num_requests)]

    # Insert URLs (Parallel)
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        short_urls = list(executor.map(lambda url: insert_url(base_url, url), urls))
    insert_time = time.time() - start_time

    # Read URLs (Parallel)
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        long_urls = list(executor.map(lambda short: fetch_url(base_url, short), short_urls))
    read_time = time.time() - start_time

    # Print Results
    print("\n### Benchmark Results ###")
    print(f"📌 Insert: {insert_time:.4f}s | Avg: {insert_time / num_requests:.6f}s per request")
    print(f"📌 Read: {read_time:.4f}s | Avg: {read_time / num_requests:.6f}s per request")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark a URL shortener service.")
    parser.add_argument("--p", type=str, required=True, help="Port of the service (e.g., 5003)")
    parser.add_argument("--n", type=int, default=1000, help="Number of requests to send (default: 1000)")

    args = parser.parse_args()

    base_url = f'http://127.0.0.1:{args.p}' 

    args = parser.parse_args()
    benchmark_service(base_url, args.n)
