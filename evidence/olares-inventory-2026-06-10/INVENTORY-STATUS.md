# Inventory session status

**Created:** 2026-06-10  
**Completed:** 2026-06-10  
**Execution:** Live collection from Windows → SSH `olares@10.0.0.34` using `olares-one` scripts + k3s in-cluster probes

## Result

**COMPLETE** — see `OLARES-INVENTORY-REPORT.md`

**Decision:** **USE EXISTING** shared Ollama + ComfyUI for M1-DV AI smokes, with operator prep (model pull, ComfyUI launcher + SDXL). Deploy **dedicated** AIMPOS Postgres, MinIO, Redis, Temporal, API, worker.

## Evidence logs

| File | Contents |
|------|----------|
| `logs/00-k3s-inventory.txt` | GPU, disk, k3s pods/services |
| `logs/08-ollama-list.txt` | `ollama list` in shared pod |
| `logs/08-ollama-incluster.txt` | In-cluster HTTP probes from mediapipeline pod |
| `logs/09-comfyui-verify.txt` | `olares-one/scripts/diagnostics/verify-comfyui.sh` |
| `logs/03-mpp-env-verify.txt` | MPP env + partial reachability |
| `logs/probe-incluster.sh` | Reusable in-cluster probe script |
| `logs/run-olares-k3s-inventory.sh` | Host-side inventory (DNS caveat documented) |

## Next step

Operator prep on Olares (items 1–3 in report §9), then schedule **M1-DV session** on Olares per frozen package.
