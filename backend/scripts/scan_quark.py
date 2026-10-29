import requests
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

def scan():
    res = requests.post("http://127.0.0.1:5244/api/auth/login", json={"username": "admin", "password": "123456"})
    token = res.json().get("data", {}).get("token")
    headers = {"Authorization": token} if token else {}

    def explore(path, depth=0):
        if depth > 3:
            return
        r = requests.post("http://127.0.0.1:5244/api/fs/list", headers=headers, json={"path": path, "page": 1, "per_page": 200, "refresh": True})
        items = r.json().get("data", {}).get("content") or []
        indent = "  " * depth
        print(f"{indent}=== {path} ({len(items)} items) ===")
        for item in items:
            name = item.get("name")
            is_dir = item.get("is_dir")
            size = item.get("size", 0)
            tag = "[DIR]" if is_dir else "[FILE]"
            print(f"{indent}  {tag} {name} ({size} B)")
            if is_dir:
                explore(f"{path}/{name}".replace("//", "/"), depth + 1)

    explore("/kuake")

if __name__ == "__main__":
    scan()
