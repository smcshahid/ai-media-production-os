#!/usr/bin/env python3
"""US-V03 cross-feature validation matrix XF-01..06 (read-only)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

FAIL = 0


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {os.environ['TOKEN']}"}


def api_get(path: str) -> tuple[int, bytes]:
    url = f"{os.environ['API']}{path}"
    req = urllib.request.Request(url, headers=auth_headers())
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.status, resp.read()


def psql(query: str) -> str:
    ns = os.environ.get("NS", "aimpos-mwayolares")
    k = os.environ.get("K", "sudo k3s kubectl")
    pgpw = os.environ["PGPW"]
    cmd = (
        f"{k} exec -i aimpos-postgres-0 -n {ns} -- "
        f"env PGPASSWORD={pgpw} psql -U aimpos -d aimpos_spark -t -A -c {query!r}"
    )
    return subprocess.check_output(cmd, shell=True, text=True).strip()


def check(name: str, ok: bool, detail: str = "") -> None:
    global FAIL
    token = f"{name}=PASS" if ok else f"{name}=FAIL"
    print(token, detail)
    if not ok:
        FAIL = 1


def main() -> int:
    project_id = os.environ["PROJECT_ID"]
    run_id = os.environ["RUN_ID"]
    export_zip = os.environ.get("EXPORT_ZIP", "/tmp/usv03-export.zip")

    rows_before = int(os.environ.get("ROWS_BEFORE", psql("SELECT COUNT(*) FROM asset_versions;")))

    # Fetch lineage + history
    lh, lineage_raw = api_get(f"/lineage/{run_id}")
    hh, history_raw = api_get(f"/assets/history?project_id={project_id}")
    lineage = json.loads(lineage_raw)
    history = json.loads(history_raw)

    lineage_ids = {n["asset_id"] for n in lineage["nodes"]}
    history_ids: set[str] = set()
    history_by_id: dict[str, dict] = {}
    history_total = 0
    for stage in history["stages"]:
        for v in stage["versions"]:
            history_ids.add(v["asset_id"])
            history_by_id[v["asset_id"]] = v
            history_total += 1

    # XF-01: lineage ⊆ history
    missing = lineage_ids - history_ids
    check("XF-01", not missing, f"missing={missing}")

    # XF-02: history count >= lineage nodes
    check("XF-02", history_total >= len(lineage["nodes"]), f"history={history_total} lineage_nodes={len(lineage['nodes'])}")

    # XF-03: export manifest hashes ⊆ history
    xf03_ok = True
    if lh == 200 and Path(export_zip).exists():
        with zipfile.ZipFile(export_zip) as zf:
            manifest = json.loads(zf.read("manifest.json"))
            for rec in manifest["files"]:
                data = zf.read(rec["path"])
                digest = hashlib.sha256(data).hexdigest()
                if digest != rec["content_hash"]:
                    xf03_ok = False
                    print(f"XF-03 hash mismatch path={rec['path']}")
                    break
                aid = rec.get("asset_id")
                if aid and aid in history_by_id:
                    if history_by_id[aid].get("content_hash") != rec["content_hash"]:
                        xf03_ok = False
                        print(f"XF-03 history hash mismatch asset={aid}")
                        break
        check("XF-03", xf03_ok)
    else:
        check("XF-03", False, "export zip missing or lineage failed")

    # XF-04: REST status available (WS parity attested in us21 verify)
    rh, rest_raw = api_get(f"/pipeline/status?project_id={project_id}")
    rest = json.loads(rest_raw)
    check("XF-04", rh == 200 and "status" in rest, f"http={rh} status={rest.get('status')}")

    # XF-05: COMPLETED surfaces readable
    eh, _ = api_get(f"/export/{run_id}")
    check("XF-05", lh == 200 and hh == 200 and eh == 200, f"lineage={lh} history={hh} export={eh}")

    # XF-06: no writes
    rows_after = int(psql("SELECT COUNT(*) FROM asset_versions;"))
    check("XF-06", rows_before == rows_after, f"before={rows_before} after={rows_after}")

    print(f"DONE XF_FAIL={FAIL}")
    return FAIL


if __name__ == "__main__":
    raise SystemExit(main())
