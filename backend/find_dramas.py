import requests
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

res = requests.post("http://127.0.0.1:5244/api/auth/login", json={"username": "admin", "password": "123456"})
token = res.json().get("data", {}).get("token")
headers = {"Authorization": token} if token else {}

def list_path(path):
    r = requests.post("http://127.0.0.1:5244/api/fs/list", headers=headers, json={"path": path, "refresh": True})
    items = r.json().get("data", {}).get("content") or []
    print(f"\n=== LIST: {path} ({len(items)} items) ===")
    for item in items:
        name = item.get("name")
        is_dir = item.get("is_dir")
        size = item.get("size", 0)
        print(f"  {'[DIR] ' if is_dir else '[FILE]'} {name} ({size} B)")
        if is_dir:
            sub_r = requests.post("http://127.0.0.1:5244/api/fs/list", headers=headers, json={"path": f"{path}/{name}", "refresh": True})
            sub_items = sub_r.json().get("data", {}).get("content") or []
            print(f"    └── {name} has {len(sub_items)} items:")
            for s in sub_items[:20]:
                print(f"        {'[DIR] ' if s.get('is_dir') else '[FILE]'} {s.get('name')} ({s.get('size')} B)")
                if s.get("is_dir"):
                    sub_r2 = requests.post("http://127.0.0.1:5244/api/fs/list", headers=headers, json={"path": f"{path}/{name}/{s.get('name')}", "refresh": True})
                    sub2_items = sub_r2.json().get("data", {}).get("content") or []
                    for s2 in sub2_items[:10]:
                        print(f"            {'[DIR] ' if s2.get('is_dir') else '[FILE]'} {s2.get('name')}")

list_path("/kuake/红果项目资源目录")
list_path("/kuake/夸克上传文件")
