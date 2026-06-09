# deploy/ — Infrastructure as Files

Docker-first. Compose is the primary local + Olares-lab entry point.

| Path | Purpose | Lands in |
|------|---------|----------|
| `compose/docker-compose.yml` | Sprint-0 stack: postgresql, minio, redis, api | T-02-02 |
| `compose/docker-compose.dev.yml` | Hot-reload bind mounts | T-02-02 |
| `init/postgres/` | Extensions / DB init | T-02-02 |
| `init/minio/` | Bucket creation | T-02-03 |
| `docker/` | Service Dockerfiles | per service |

Full 9-service stack (adds ollama, comfyui, temporal, worker, web) arrives in **Sprint 1 (US-02)**. Helm/Olares K8s is Phase 0.5 — deferred.
