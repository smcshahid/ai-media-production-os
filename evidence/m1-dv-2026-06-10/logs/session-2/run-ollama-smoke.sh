#!/usr/bin/env bash
set -uo pipefail
KC="sudo -n k3s kubectl"
NS=mediapipeline-mwayolares
POD=$($KC get pods -n "$NS" -l app=media-pipeline -o jsonpath='{.items[0].metadata.name}')
echo "pod=$POD"
$KC exec -n "$NS" "$POD" -c media-pipeline -- python3 -c "
import json, time, urllib.request
host = 'http://ollama.ollamaserver-shared:11434'
model = 'qwen3:14b'
tags = json.loads(urllib.request.urlopen(host+'/api/tags', timeout=15).read())
names = {m.get('name','') for m in tags.get('models',[])}
if model not in names:
    raise SystemExit('FAIL model '+model+' not in '+str(names))
started = time.monotonic()
body = json.dumps({'model': model, 'prompt': 'Reply with exactly: OK', 'stream': False, 'options': {'num_predict': 8, 'temperature': 0}}).encode()
req = urllib.request.Request(host+'/api/generate', data=body, headers={'Content-Type':'application/json'}, method='POST')
resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
elapsed = time.monotonic()-started
text = str(resp.get('response','')).strip()
if not text:
    raise SystemExit('FAIL empty response')
print('PASS ollama model='+model+' elapsed=%.1fs response=%r' % (elapsed, text[:60]))
"
