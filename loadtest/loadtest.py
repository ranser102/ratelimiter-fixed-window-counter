import requests
import threading
import time
import random


def make_request(url):
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.text}")

def simulate_load(url, num_users, request_rate, duration_in_seconds=60):
    start_time = time.time()
    end_time = start_time + duration_in_seconds
    threads = []
    while time.time() < end_time:
        for _ in range(num_users):
            thread = threading.Thread(target=make_request, args=(random.choice(urls),))
            threads.append(thread)
            thread.start()
            time.sleep(1 / request_rate) # Sleep for the request rate

        for thread in threads:
            thread.join()

        # Continue making requests until the duration is reached
        pass

if __name__ == "__main__":
    urls = [
        "http://127.0.0.1:9001/ratelimit?max_limit=3&key=azure&interval=10",
        "http://127.0.0.1:9002/ratelimit?max_limit=3&key=gcp&interval=10",
        "http://127.0.0.1:9003/ratelimit?max_limit=3&key=aws&interval=10",
        "http://127.0.0.1:9001/ratelimit?max_limit=3&key=oracle&interval=10",
        "http://127.0.0.1:9002/ratelimit?max_limit=3&key=ibm&interval=10"
    ]

    num_users = 1000
    request_rate = 100  # Requests per second
    duration_in_seconds = 60

    simulate_load(urls, num_users, request_rate, duration_in_seconds)
