import requests
import sys

sys.stdout.reconfigure(encoding="utf-8")

r = requests.get("http://127.0.0.1:8000/api/v1/videos/home-feed")
print("Status code:", r.status_code)
data = r.json()
carousels = data.get("data", {}).get("carousels", [])
videos = data.get("data", {}).get("videos", [])
print(f"Total carousels: {len(carousels)}")
for c in carousels:
    print(f"  [Carousel] {c.get('title')} -> video_id: {c.get('video_id')}")

print(f"\nTotal video cards: {len(videos)}")
for v in videos:
    print(f"  [Card] {v.get('title')} ({v.get('category')}) - {v.get('duration_str')}")
