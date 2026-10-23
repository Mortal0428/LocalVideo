import requests

res = requests.get("http://localhost:8000/api/v1/rag-admin/dramas")
print("Status:", res.status_code)
dramas = res.json().get("data", [])
for d in dramas:
    print(f"ID: {d.get('id')} | Title: {d.get('title')}")
