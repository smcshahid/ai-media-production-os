# tests/ — Cross-Service Tests

| Path | Purpose | When |
|------|---------|------|
| `integration/` | Multi-container via compose (mocked AI) | Sprint 1+ |
| `e2e/` | Full pipeline on GPU hardware | manual/nightly; not PR-blocking initially |
| `fixtures/` | Sample idea/story/script inputs | Sprint 3+ |

Fast unit tests are colocated per service (`api/tests/`, `worker/tests/`, `web/src/tests/`), not here.
