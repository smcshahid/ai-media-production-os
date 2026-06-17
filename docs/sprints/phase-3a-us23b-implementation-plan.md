# US-23b — Audit Browser (implementation plan)

**Status:** **IMPLEMENTED**  
**Decision:** D-64

## Scope

| In scope | Out of scope |
|----------|--------------|
| `GET /audit` read API | Schema migration |
| `AuditTrailViewer` web UI | Audit export CSV |
| Repository `list_for_project` | Event replay / WS fan-out |

## API contract

```
GET /audit?project_id={uuid}&pipeline_run_id={uuid?}
→ AuditTrailResponse { project_id, pipeline_run_id, events[] }
```

## Files

- `api/app/domain/audit/` — types + service  
- `api/app/routes/audit.py` — route  
- `api/app/infrastructure/db/repositories/audit_event.py` — query  
- `web/src/components/AuditTrailViewer.tsx`  
- `web/src/routes/AuditPage.tsx` — replaces placeholder  
- `deploy/k8s/us23b-verify/verify_us23b.sh`

## Verification

- `api/tests/unit/test_audit_trail.py` (3 tests)  
- Olares/local: SQL row parity, run filter, no writes
