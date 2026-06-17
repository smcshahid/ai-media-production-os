# US-V04 — Local acceptance package

**Date:** 2026-06-16  
**Environment:** Local Docker + Olares shared ComfyUI/Ollama (D-63)  
**Result:** **PASS WITH NOTE**

## Worker environment

```
COMFYUI_WORKFLOW=flux_storyboard.json
VIDEO_I2V_ENABLED=true
COMFYUI_HOST=http://host.docker.internal:8190
```

## Storyboard attestation

```
STORYBOARD_VERSION=1
FRAME_COUNT=4
```

## Migration attestation

```
ALEMBIC=0003
STORYBOARD_INDEX_COUNT=2
```

## VIDEO i2v

At verification time run `38021fd3-4c84-4163-ab41-94ba46634093` was **RUNNING / VIDEO**.  
Latest stored VIDEO source before completion: `slideshow` (prior runs).  
**Action:** Re-run `deploy/dev/verify_usv04_local.ps1` after pipeline COMPLETED to confirm `comfyui_i2v`.

## Audit regression

```
GET /audit — 97 events PASS
```

## Olares cluster script

`deploy/k8s/usv04-verify/verify_usv04.sh` for k8s worker deploy attestation.
