import requests
import time

url = "http://localhost:8000/api/v1/rag-admin/eval/run"
payload = {
    "name": "测试基准评测运行",
    "max_samples": 20,
    "drama_id": "f1a94b85-5493-4faf-8968-47a97cd7111f",
    "drama_title": "高冷千金"
}

t0 = time.time()
print("Sending request to /api/v1/rag-admin/eval/run...")
try:
    res = requests.post(url, json=payload, timeout=30)
    print("Status:", res.status_code)
    print("Time:", time.time() - t0)
    print("Response text:", res.text[:500])
except Exception as e:
    print("Error:", e)
