import requests
import time

url = "http://localhost:8000/api/v1/videos/home-feed"
t0 = time.time()
r1 = requests.get(url)
t1 = time.time()
print(f"First request status: {r1.status_code}, time: {(t1 - t0)*1000:.2f}ms, videos count: {len(r1.json()['data']['videos'])}")

t2 = time.time()
r2 = requests.get(url)
t3 = time.time()
print(f"Second request (Redis Hit) status: {r2.status_code}, time: {(t3 - t2)*1000:.2f}ms")
