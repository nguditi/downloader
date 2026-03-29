import json, time, urllib.request

req = urllib.request.Request('http://127.0.0.1:8001/api/v1/resolve', 
    data=json.dumps({'url':'https://www.youtube.com/shorts/Mq_M1anLvTg'}).encode(),
    headers={'Content-Type':'application/json'}, method='POST')
info = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
print(f'YT Shorts: {info["title"][:50]} | {info["duration_seconds"]}s')

req2 = urllib.request.Request('http://127.0.0.1:8001/api/v1/download',
    data=json.dumps({'url':info['canonical_url'],'format_id':'mp4-720p','agreed_to_terms':True}).encode(),
    headers={'Content-Type':'application/json'}, method='POST')
job = json.loads(urllib.request.urlopen(req2, timeout=30).read().decode())

for i in range(60):
    s = json.loads(urllib.request.urlopen(f'http://127.0.0.1:8001/api/v1/download/{job["job_id"]}', timeout=30).read().decode())
    if s['status'] in ('completed','failed'): break
    time.sleep(1)

print(f'Download: {s["status"]} {s["progress"]}%')
