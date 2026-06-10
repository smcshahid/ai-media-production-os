#!/usr/bin/env bash
set -uo pipefail
KC="sudo -n k3s kubectl"
NS=mediapipeline-mwayolares
POD=$($KC get pods -n "$NS" -l app=media-pipeline -o jsonpath='{.items[0].metadata.name}')
$KC exec -n "$NS" "$POD" -c media-pipeline -- python3 -c "
import json, time, urllib.request, sys
host='http://ollama.ollamaserver-shared:11434'
model='qwen3:14b'
print('Target:', host, 'model=', model, 'require_live=True')
tags=json.loads(urllib.request.urlopen(host+'/api/tags',timeout=15).read())
names={m.get('name','') for m in tags.get('models',[])}
if model not in names:
    print('FAIL model missing'); sys.exit(1)
print('[check] model present OK')
started=time.monotonic()
body=json.dumps({'model':model,'prompt':'Reply with exactly: OK','stream':False,'options':{'num_predict':128,'temperature':0}}).encode()
req=urllib.request.Request(host+'/api/generate',data=body,headers={'Content-Type':'application/json'},method='POST')
payload=json.loads(urllib.request.urlopen(req,timeout=60).read())
elapsed=time.monotonic()-started
text=str(payload.get('response','')).strip() or str(payload.get('thinking','')).strip()
if not text:
    print('FAIL empty'); sys.exit(1)
if elapsed>=30:
    print('FAIL slow',elapsed); sys.exit(1)
print('[AC] OK response in %.1fs: %r' % (elapsed, text[:80]))
print('PASS - T-06-01 Ollama connectivity and text generation verified (live).')
"
