import json
import time
import urllib.request

test_urls = [
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "YouTube"),
    ("https://www.tiktok.com/@tiktok/video/7200488904919060778", "TikTok (if available)"),
]

for url, label in test_urls:
    print(f"\n{'='*60}")
    print(f"Testing: {label}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        # Resolve
        req = urllib.request.Request(
            "http://127.0.0.1:8001/api/v1/resolve",
            data=json.dumps({"url": url}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        info = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
        print(f"Platform: {info['platform']}")
        print(f"Title: {info['title'][:60]}")
        print(f"Duration: {info['duration_seconds']}s")
        print(f"Thumbnail: {info['thumbnail_url'][:80]}")
        
        # Download
        print("Starting download...")
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
            print(f"  [{i}] {status['status']} {status['progress']}%", end="\r")
            if status["status"] in ("completed", "failed"):
                break
            time.sleep(1)
        
        print()
        print(f"Final Status: {status['status']}")
        if status.get("error"):
            print(f"Error: {status['error']}")
        else:
            print(f"File: {status.get('file_name')}")
    except Exception as e:
        print(f"Error: {e}")
