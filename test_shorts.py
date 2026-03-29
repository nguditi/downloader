import json
import time
import urllib.request

# Resolve
req = urllib.request.Request(
    "http://127.0.0.1:8001/api/v1/resolve",
    data=json.dumps({"url": "https://www.youtube.com/shorts/Mq_M1anLvTg"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
info = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
print(f"Title: {info['title'][:50]}")
print(f"Thumbnail: {info['thumbnail_url'][:80]}")

# Download
req2 = urllib.request.Request(
    "http://127.0.0.1:8001/api/v1/download",
    data=json.dumps(
        {"url": info["canonical_url"], "format_id": "mp4-720p", "agreed_to_terms": True}
    ).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
job = json.loads(urllib.request.urlopen(req2, timeout=30).read().decode())
job_id = job["job_id"]

# Poll
for i in range(120):
    status = json.loads(
        urllib.request.urlopen(
            f"http://127.0.0.1:8001/api/v1/download/{job_id}", timeout=30
        ).read().decode()
    )
    print(f"[{i}] {status['status']} {status['progress']}%")
    if status["status"] in ("completed", "failed"):
        break
    time.sleep(1)

print(f"Final: {status['status']}")
if status.get("error"):
    print(f"Error: {status['error']}")
