#!/usr/bin/env bash
unzip -p /tmp/path-d-test.zip manifest.json | python3 -c "
import json, sys
m = json.load(sys.stdin)
for f in m['files']:
    if f['stage'] in ('VIDEO', 'NARRATION'):
        print(json.dumps(f, indent=2))
print('manifest_version', m.get('manifest_version'))
"
