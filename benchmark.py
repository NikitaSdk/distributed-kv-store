import requests
import time
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8000"
TABLE = "test"

def put(i):
    requests.put(
        f"{BASE_URL}/tables/{TABLE}/records/{i}",
        json={"value": f"v{i}"}
    )

def get(i):
    requests.get(
        f"{BASE_URL}/tables/{TABLE}/records/{i}")

start = time.time()

with ThreadPoolExecutor(max_workers=10) as ex:
    for i in range(100):
        ex.submit(put, i)

mid = time.time()

with ThreadPoolExecutor(max_workers=10) as ex:
    for i in range(100):
        ex.submit(get, i)

end = time.time()

print("PUT time:", mid - start)
print("GET time:", end - mid)
print("Throughput ops/sec:", 200 / (end - start))
