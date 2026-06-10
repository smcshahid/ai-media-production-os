#!/usr/bin/env bash
KC="sudo -n k3s kubectl"
NS=mediapipeline-mwayolares
POD=$($KC get pods -n "$NS" -l app=media-pipeline -o jsonpath='{.items[0].metadata.name}')
for model in qwen3:14b llama3.1:8b mistral:7b; do
  echo "=== generate $model ==="
  $KC exec -n "$NS" "$POD" -c media-pipeline -- python3 -c "
import json, urllib.request
model='$model'
body=json.dumps({'model':model,'prompt':'Reply with exactly: OK','stream':False,'options':{'num_predict':64,'temperature':0}}).encode()
req=urllib.request.Request('http://ollama.ollamaserver-shared:11434/api/generate',data=body,headers={'Content-Type':'application/json'},method='POST')
try:
    raw=urllib.request.urlopen(req,timeout=120).read()
    d=json.loads(raw)
    print('keys', list(d.keys()))
    print('response', repr(d.get('response',''))[:200])
    print('thinking', repr(d.get('thinking',''))[:100] if 'thinking' in d else 'n/a')
except Exception as e:
    print('ERR', e)
"
done
