#!/usr/bin/env bash
# US-V08B Character Bible Hardening E2E acceptance on Olares (Paths A–F).
# Requires: TOKEN, PGPW, PROJECT env vars; Phase 7.5 deployed; Alembic 0007.
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
EVID="${EVID_DIR:-/tmp/usv08b-evidence}"
mkdir -p "$EVID"

: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
FAIL=0

log() { echo "$(date -Iseconds) $*" >> "$EVID/e2e-olares.log"; echo "$(date -Iseconds) $*" >&2; }

psql() {
  $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"
}

poll_until() {
  local want_status="$1" want_stage="$2" want_scene="${3:-}" episode_id="${4:-}" max="${5:-1200}"
  local deadline=$(( $(date +%s) + max ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    local url="$API/pipeline/status?project_id=$PROJECT"
    if [ -n "$episode_id" ]; then url="${url}&episode_id=${episode_id}"; fi
    local body
    body=$(curl -sf -m 20 "$url" -H "$AUTH" || echo '{}')
    local st stg scn
    st=$(echo "$body" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
    stg=$(echo "$body" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
    scn=$(echo "$body" | sed -n 's/.*"current_scene_index":\([0-9]*\).*/\1/p')
    log "  poll status=$st stage=${stg:-null} scene=${scn:-null} ep=${episode_id:-legacy}"
    if [ "$st" = "FAILED" ]; then log "FAIL pipeline FAILED: $body"; return 1; fi
    if [ "$st" = "$want_status" ]; then
      if [ -n "$want_stage" ] && [ "$stg" != "$want_stage" ]; then sleep 10; continue; fi
      if [ -n "$want_scene" ] && [ "$scn" != "$want_scene" ]; then sleep 10; continue; fi
      return 0
    fi
    sleep 15
  done
  log "FAIL poll timeout want=$want_status/$want_stage scene=$want_scene"
  return 1
}

approve() {
  local stage="$1"
  curl -sf -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","stage":"'"$stage"'","decision":"APPROVED"}' >> "$EVID/e2e-olares.log" 2>&1
  echo >> "$EVID/e2e-olares.log"
}

terminate_workflow() {
  local wf="$1"
  [ -n "$wf" ] || return 0
  log "terminating temporal workflow $wf"
  $K exec deploy/temporal -n "$NS" -- tctl --address temporal:7233 workflow terminate \
    -w "$wf" -r "US-V08 verification cleanup" >> "$EVID/e2e-olares.log" 2>&1 || true
}

cancel_active_runs() {
  local wf_ids
  log "Cancelling non-terminal active runs for project"
  wf_ids=$(psql -c "
    SELECT COALESCE(temporal_workflow_id, 'spark-pipeline-' || id::text)
    FROM pipeline_runs
    WHERE project_id='$PROJECT' AND status IN ('PENDING','RUNNING','AWAITING_APPROVAL');
  " || true)
  for wf in $wf_ids; do
    terminate_workflow "$wf"
  done
  psql -c "
    UPDATE pipeline_runs SET status='CANCELLED', current_stage=NULL, updated_at=NOW()
    WHERE project_id='$PROJECT' AND status IN ('PENDING','RUNNING','AWAITING_APPROVAL');
  " >> "$EVID/e2e-olares.log" 2>&1 || true
  wait_for_project_idle 120
}

wait_for_project_idle() {
  local max="${1:-120}" i count
  for i in $(seq 1 "$max"); do
    count=$(psql -c "
      SELECT COUNT(*) FROM pipeline_runs
      WHERE project_id='$PROJECT' AND status IN ('PENDING','RUNNING','AWAITING_APPROVAL');
    " || echo 1)
    if [ "${count:-1}" = "0" ]; then
      log "project idle (no active runs)"
      return 0
    fi
    log "waiting for idle active_runs=$count (${i}/${max})"
    sleep 5
  done
  log "WARN project still has active runs after ${max} polls"
  return 1
}

submit_idea() {
  local label="$1" scene_count="$2" char_hint="$3"
  local paragraph
  case "$scene_count" in
    1) paragraph="Character continuity test: ${char_hint} Write exactly one scene with clear dialogue naming each character." ;;
    3) paragraph="Character continuity test: ${char_hint} Write exactly three scenes with clear dialogue naming each character in every scene." ;;
    *) paragraph="Character continuity test: ${char_hint} Clear dialogue naming each character." ;;
  esac
  curl -sf -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","title":"US-V08 '"$label"'","paragraph":"'"$paragraph"'","style_note":"character bible test"}' \
    >> "$EVID/e2e-olares.log" 2>&1
  echo >> "$EVID/e2e-olares.log"
}

create_episode() {
  local title="$1"
  local resp ep_id ep_num
  resp=$(curl -sf -m 30 -X POST "$API/episodes" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","title":"'"$title"'"}')
  ep_id=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['episode']['id'])")
  ep_num=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['episode']['episode_number'])")
  log "created episode id=$ep_id number=$ep_num title=$title"
  echo "$resp" > "$EVID/episode-${ep_num}-create.json"
  echo "$ep_id|$ep_num"
}

cleanup_project_characters() {
  local count
  count=$(psql -c "SELECT COUNT(*) FROM characters WHERE project_id='$PROJECT';")
  psql -c "DELETE FROM characters WHERE project_id='$PROJECT';" >> "$EVID/e2e-olares.log" 2>&1 || true
  log "cleaned project characters (was $count)"
}

create_character() {
  local suffix="$1" name="$2" role="$3" visual="$4" personality="$5"
  local resp http body char_id
  resp=$(curl -s -m 30 -w "\nHTTP:%{http_code}" -X POST "$API/characters" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","name":"'"$name"'","role":"'"$role"'","description":"US-V08 '"$suffix"' character","visual_traits":"'"$visual"'","personality_notes":"'"$personality"'"}')
  http=$(echo "$resp" | sed -n 's/.*HTTP:\([0-9]*\).*/\1/p')
  body=$(echo "$resp" | sed '/HTTP:/d')
  if [ "$http" != "201" ]; then
    log "FAIL create character name=$name http=$http body=$(echo "$body" | head -c 200)"
    echo ""
    return 1
  fi
  char_id=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin)['character']['id'])")
  log "created character id=$char_id name=$name"
  echo "$body" > "$EVID/character-${suffix}-${name}.json"
  echo "$char_id"
}

seed_characters() {
  local label="$1" count="$2" attempt="$3"
  local ids=() i names roles visuals personalities
  names=(Maya Eli Jordan)
  roles=(protagonist mentor ally)
  visuals=("silver lab coat" "weathered field jacket" "bright orange scarf")
  personalities=("curious analytical" "calm pragmatic" "optimistic energetic")
  for i in $(seq 1 "$count"); do
    local idx=$((i - 1))
    local cid unique_name
    unique_name="${names[$idx]}-${label}-a${attempt}"
    cid=$(create_character "${label}-${i}-a${attempt}" "$unique_name" "${roles[$idx]}" "${visuals[$idx]}" "${personalities[$idx]}") || return 1
    if [ -z "$cid" ]; then log "FAIL seed_characters empty id"; return 1; fi
    ids+=("$cid")
  done
  local json="["
  local first=1
  for cid in "${ids[@]}"; do
    [ "$first" = "1" ] || json+=","
    json+="\"$cid\""
    first=0
  done
  json+="]"
  echo "$json"
}

verify_character_export() {
  local label="$1" run_id="$2" episode_id="$3" episode_num="$4" scene_count="$5" char_count="$6"
  local zip="$EVID/path-${label}-export.zip"
  local ep_prefix
  ep_prefix=$(printf "episodes/episode_%02d" "$episode_num")

  curl -sf -m 120 "$API/export/$run_id" -H "$AUTH" -o "$zip"
  unzip -p "$zip" manifest.json > "$EVID/path-${label}-manifest.json"

  local mv narr_count ep_status
  mv=$(python3 -c "import json; print(json.load(open('$EVID/path-${label}-manifest.json')).get('manifest_version',''))")
  log "export manifest_version=$mv size=$(wc -c < "$zip") chars=$char_count"

  if [ "$mv" != "5" ]; then log "FAIL PATH $label expected manifest v5 got $mv"; return 1; fi
  if ! python3 -c "
import json
m=json.load(open('$EVID/path-${label}-manifest.json'))
chars=m.get('characters') or []
assert len(chars)==$char_count, f'expected $char_count characters got {len(chars)}'
for c in chars:
    assert c.get('name'), c
"; then
    log "FAIL PATH $label manifest characters validation"; return 1
  fi
  if ! grep -q "\"episode_number\": $episode_num" "$EVID/path-${label}-manifest.json"; then
    log "FAIL PATH $label manifest missing episode_number=$episode_num"; return 1
  fi
  if ! grep -q "$ep_prefix" "$EVID/path-${label}-manifest.json"; then
    log "FAIL PATH $label manifest missing $ep_prefix paths"; return 1
  fi

  narr_count=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='NARRATION' AND pipeline_run_id='$run_id';")
  log "NARRATION assets for run: $narr_count (expect >= $scene_count)"
  if [ "${narr_count:-0}" -lt "$scene_count" ]; then
    log "FAIL PATH $label insufficient NARRATION assets"; return 1
  fi

  ep_status=$(psql -c "SELECT status FROM episodes WHERE id='$episode_id';")
  log "episode status=$ep_status (expect COMPLETED)"
  if [ "$ep_status" != "COMPLETED" ]; then
    log "FAIL PATH $label episode not COMPLETED"; return 1
  fi

  run_chars=$(psql -c "SELECT COALESCE(json_array_length(character_ids::json), 0) FROM pipeline_runs WHERE id='$run_id';")
  log "run character_ids count=$run_chars (expect $char_count)"
  if [ "${run_chars:-0}" != "$char_count" ]; then
    log "FAIL PATH $label run character_ids mismatch"; return 1
  fi

  local snap_len
  snap_len=$(psql -c "SELECT COALESCE(json_array_length(character_snapshot::json), 0) FROM pipeline_runs WHERE id='$run_id';")
  log "run character_snapshot count=$snap_len (expect $char_count)"
  if [ "${snap_len:-0}" != "$char_count" ]; then
    log "FAIL PATH $label run character_snapshot missing"; return 1
  fi

  curl -sf -m 30 "$API/audit?project_id=$PROJECT&pipeline_run_id=$run_id&limit=50" -H "$AUTH" \
    > "$EVID/path-${label}-audit.json"
  curl -sf -m 30 "$API/assets/history?project_id=$PROJECT&pipeline_run_id=$run_id" -H "$AUTH" \
    > "$EVID/path-${label}-history.json"
  curl -sf -m 30 "$API/lineage/$run_id" -H "$AUTH" > "$EVID/path-${label}-lineage.json"
  curl -sf -m 30 "$API/pipeline/runs?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-${label}-runs.json"

  log "PASS PATH $label character run $run_id ep=$episode_num chars=$char_count"
  return 0
}

run_character_path() {
  local label="$1" scene_count="$2" char_count="$3" ep_title="$4"
  local attempt ep_info episode_id episode_num run_id start http s ok char_json char_hint

  case "$char_count" in
    1) char_hint="Protagonist Maya explores bioluminescent coral." ;;
    3) char_hint="Maya, mentor Eli, and ally Jordan explore bioluminescent coral together." ;;
    *) char_hint="Characters explore bioluminescent coral." ;;
  esac

  for attempt in 1 2 3 4 5; do
    log "========== PATH $label: ${char_count} char(s) ${scene_count}-scene (attempt $attempt) =========="
    cancel_active_runs
    cleanup_project_characters
    char_json=$(seed_characters "$label" "$char_count" "$attempt") || continue
    ep_info=$(create_episode "$ep_title")
    episode_id="${ep_info%%|*}"
    episode_num="${ep_info#*|}"
    if [ -z "$episode_id" ] || [ -z "$episode_num" ]; then
      log "WARN episode creation failed attempt $attempt"; continue
    fi

    submit_idea "$label" "$scene_count" "$char_hint"

    start=$(curl -s -m 30 -w "\nHTTP:%{http_code}" -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
      -d '{"project_id":"'"$PROJECT"'","scene_count":'"$scene_count"',"episode_id":"'"$episode_id"'","character_ids":'"$char_json"'}')
    http=$(echo "$start" | sed -n 's/.*HTTP:\([0-9]*\).*/\1/p')
    run_id=$(echo "$start" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
    log "start http=$http run_id=$run_id episode_id=$episode_id chars=$char_count"
    echo "$start" > "$EVID/path-${label}-start-attempt${attempt}.json"
    if [ "$http" != "201" ]; then
      log "WARN pipeline start failed attempt $attempt body=$(echo "$start" | head -1)"
      continue
    fi

    poll_until AWAITING_APPROVAL STORY "" "$episode_id" 900 || continue
    approve STORY
    poll_until AWAITING_APPROVAL SCRIPT "" "$episode_id" 900 || continue
    approve SCRIPT

    ok=1
    for s in $(seq 1 "$scene_count"); do
      log "--- Scene $s / $scene_count STORYBOARD ---"
      poll_until AWAITING_APPROVAL STORYBOARD "$s" "$episode_id" 2400 || { ok=0; break; }
      approve STORYBOARD
      log "--- Scene $s / $scene_count VIDEO (narration) ---"
      poll_until AWAITING_APPROVAL VIDEO "$s" "$episode_id" 5400 || { ok=0; break; }
      approve VIDEO
    done
    [ "$ok" = "1" ] || continue

    poll_until COMPLETED "" "" "$episode_id" 120 || continue
    if verify_character_export "$label" "$run_id" "$episode_id" "$episode_num" "$scene_count" "$char_count"; then
      echo "$run_id|$episode_id|$episode_num"
      return 0
    fi
  done
  log "FAIL PATH $label after 5 attempts"
  return 1
}

path_d_edit_lifecycle() {
  log "========== PATH D: character edit lifecycle =========="
  local attempt char_json char_id orig_name ep_info episode_id episode_num run1 run2
  local start http ok s zip

  for attempt in 1 2 3; do
    cancel_active_runs
    cleanup_project_characters
    char_json=$(seed_characters D 1 "$attempt") || continue
    char_id=$(echo "$char_json" | python3 -c "import sys,json; print(json.load(sys.stdin)[0])")
    orig_name=$(psql -c "SELECT name FROM characters WHERE id='$char_id';")
    [ -n "$orig_name" ] || continue

    ep_info=$(create_episode "US-V08B Path D Run1")
    episode_id="${ep_info%%|*}"
    episode_num="${ep_info#*|}"
    submit_idea "D1" 1 "Protagonist ${orig_name} explores bioluminescent coral."
    start=$(curl -s -m 30 -w "\nHTTP:%{http_code}" -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
      -d '{"project_id":"'"$PROJECT"'","scene_count":1,"episode_id":"'"$episode_id"'","character_ids":'"$char_json"'}')
    http=$(echo "$start" | sed -n 's/.*HTTP:\([0-9]*\).*/\1/p')
    run1=$(echo "$start" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
    [ "$http" = "201" ] && [ -n "$run1" ] || continue
    poll_until AWAITING_APPROVAL STORY "" "$episode_id" 900 || continue
    approve STORY
    poll_until AWAITING_APPROVAL SCRIPT "" "$episode_id" 900 || continue
    approve SCRIPT
    poll_until AWAITING_APPROVAL STORYBOARD 1 "$episode_id" 2400 || continue
    approve STORYBOARD
    poll_until AWAITING_APPROVAL VIDEO 1 "$episode_id" 5400 || continue
    approve VIDEO
    poll_until COMPLETED "" "" "$episode_id" 120 || continue
    verify_character_export D1 "$run1" "$episode_id" "$episode_num" 1 1 || continue

    edited_name="${orig_name}-Edited"
    curl -sf -m 30 -X PATCH "$API/characters/$char_id?project_id=$PROJECT" -H "$AUTH" -H 'Content-Type: application/json' \
      -d '{"name":"'"$edited_name"'","visual_traits":"edited silver lab coat"}' >> "$EVID/e2e-olares.log" 2>&1

    ep_info=$(create_episode "US-V08B Path D Run2")
    episode_id="${ep_info%%|*}"
    episode_num="${ep_info#*|}"
    submit_idea "D2" 1 "Protagonist ${edited_name} explores bioluminescent coral."
    start=$(curl -s -m 30 -w "\nHTTP:%{http_code}" -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
      -d '{"project_id":"'"$PROJECT"'","scene_count":1,"episode_id":"'"$episode_id"'","character_ids":'"$char_json"'}')
    http=$(echo "$start" | sed -n 's/.*HTTP:\([0-9]*\).*/\1/p')
    run2=$(echo "$start" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
    [ "$http" = "201" ] && [ -n "$run2" ] || continue
    poll_until AWAITING_APPROVAL STORY "" "$episode_id" 900 || continue
    approve STORY
    poll_until AWAITING_APPROVAL SCRIPT "" "$episode_id" 900 || continue
    approve SCRIPT
    poll_until AWAITING_APPROVAL STORYBOARD 1 "$episode_id" 2400 || continue
    approve STORYBOARD
    poll_until AWAITING_APPROVAL VIDEO 1 "$episode_id" 5400 || continue
    approve VIDEO
    poll_until COMPLETED "" "" "$episode_id" 120 || continue
    verify_character_export D2 "$run2" "$episode_id" "$episode_num" 1 1 || continue

    if ! python3 -c "
import json
m1=json.load(open('$EVID/path-D1-manifest.json'))
m2=json.load(open('$EVID/path-D2-manifest.json'))
n1=m1['characters'][0]['name']
n2=m2['characters'][0]['name']
assert n1 == '''$orig_name''', n1
assert n2 == '''$edited_name''', n2
"; then
      log "FAIL PATH D snapshot names run1=$orig_name run2=$edited_name"; return 1
    fi

    curl -sf -m 120 "$API/export/$run1" -H "$AUTH" -o "$EVID/path-D-run1-export.zip"
    unzip -p "$EVID/path-D-run1-export.zip" manifest.json > "$EVID/path-D-run1-manifest.json"
    curl -sf -m 120 "$API/export/$run2" -H "$AUTH" -o "$EVID/path-D-run2-export.zip"
    unzip -p "$EVID/path-D-run2-export.zip" manifest.json > "$EVID/path-D-run2-manifest.json"
    log "PASS PATH D edit lifecycle run1=$run1 run2=$run2 char=$char_id"
    echo "$run1|$run2|$char_id"
    return 0
  done
  log "FAIL PATH D after 3 attempts"
  return 1
}

path_e_delete_after_export() {
  local run_id="$1" char_id="$2"
  log "========== PATH E: character delete after export =========="
  [ -n "$run_id" ] && [ -n "$char_id" ] || { log "FAIL PATH E missing run/char"; return 1; }

  curl -sf -m 120 "$API/export/$run_id" -H "$AUTH" -o "$EVID/path-E-before-export.zip"
  unzip -p "$EVID/path-E-before-export.zip" manifest.json > "$EVID/path-E-before-manifest.json"

  curl -sf -m 30 -X DELETE "$API/characters/$char_id?project_id=$PROJECT" -H "$AUTH" \
    >> "$EVID/e2e-olares.log" 2>&1 || { log "FAIL PATH E delete character"; return 1; }

  curl -sf -m 120 "$API/export/$run_id" -H "$AUTH" -o "$EVID/path-E-after-export.zip"
  unzip -p "$EVID/path-E-after-export.zip" manifest.json > "$EVID/path-E-after-manifest.json"

  if ! python3 -c "
import json
b=json.load(open('$EVID/path-E-before-manifest.json'))
a=json.load(open('$EVID/path-E-after-manifest.json'))
assert b.get('manifest_version')=='5', b.get('manifest_version')
assert a.get('manifest_version')=='5', a.get('manifest_version')
assert b['characters']==a['characters'], (b['characters'], a['characters'])
"; then
    log "FAIL PATH E export changed after character delete"; return 1
  fi
  log "PASS PATH E delete-after-export run=$run_id char=$char_id"
  return 0
}

path_f_backward_compat() {
  log "========== PATH F: backward compatibility (v1/v2/v3/v4 without characters) =========="
  local legacy_run mv zip found_v4=0 found_v3=0 found_v2=0

  legacy_run=$(psql -c "
    SELECT id::text FROM pipeline_runs
    WHERE project_id='$PROJECT' AND episode_id IS NOT NULL AND status='COMPLETED'
      AND (character_ids IS NULL OR character_ids::text = 'null' OR character_ids::text = '[]')
    ORDER BY updated_at DESC LIMIT 1;
  ")
  if [ -n "$legacy_run" ]; then
    zip="$EVID/path-D-v4-export.zip"
    curl -sf -m 120 "$API/export/$legacy_run" -H "$AUTH" -o "$zip"
    unzip -p "$zip" manifest.json > "$EVID/path-D-v4-manifest.json"
    mv=$(python3 -c "import json; print(json.load(open('$EVID/path-D-v4-manifest.json')).get('manifest_version',''))" 2>/dev/null || true)
    log "v4 episode legacy run=$legacy_run manifest=$mv"
    [ "$mv" = "4" ] && found_v4=1
  fi

  legacy_run=$(psql -c "
    SELECT id::text FROM pipeline_runs
    WHERE project_id='$PROJECT' AND episode_id IS NULL AND status='COMPLETED'
      AND COALESCE(scene_count, 1) = 1
      AND id IN (
        SELECT DISTINCT pipeline_run_id FROM asset_versions
        WHERE stage='NARRATION' AND pipeline_run_id IS NOT NULL
      )
    ORDER BY updated_at DESC LIMIT 1;
  ")
  if [ -n "$legacy_run" ]; then
    zip="$EVID/path-D-v3-export.zip"
    curl -sf -m 120 "$API/export/$legacy_run" -H "$AUTH" -o "$zip"
    unzip -p "$zip" manifest.json > "$EVID/path-D-v3-manifest.json"
    mv=$(python3 -c "import json; print(json.load(open('$EVID/path-D-v3-manifest.json')).get('manifest_version',''))" 2>/dev/null || true)
    log "v3 narrated legacy run=$legacy_run manifest=$mv"
    [ "$mv" = "3" ] && found_v3=1
  fi

  legacy_run=$(psql -c "
    SELECT id::text FROM pipeline_runs
    WHERE project_id='$PROJECT' AND episode_id IS NULL AND status='COMPLETED'
      AND scene_count >= 2
    ORDER BY updated_at DESC LIMIT 1;
  ")
  if [ -n "$legacy_run" ]; then
    zip="$EVID/path-D-v2-export.zip"
    curl -sf -m 120 "$API/export/$legacy_run" -H "$AUTH" -o "$zip"
    unzip -p "$zip" manifest.json > "$EVID/path-D-v2-manifest.json"
    mv=$(python3 -c "import json; print(json.load(open('$EVID/path-D-v2-manifest.json')).get('manifest_version',''))" 2>/dev/null || true)
    log "v2 multi-scene legacy run=$legacy_run manifest=$mv"
    if [ "$mv" = "2" ] || [ "$mv" = "3" ]; then found_v2=1; fi
  fi

  curl -sf -m 30 "$API/characters?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-D-characters.json" || return 1
  curl -sf -m 30 "$API/assets/history?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-D-history.json" || return 1

  if [ "$found_v3" = "1" ] && [ "$found_v2" = "1" ]; then
    log "PASS PATH F backward compatibility (v2=$found_v2 v3=$found_v3 v4=$found_v4)"
    return 0
  fi
  log "FAIL PATH F missing legacy manifests v2=$found_v2 v3=$found_v3 v4=$found_v4"
  return 1
}

path_f_regression() {
  local run_id="$1"
  log "========== PATH F: platform regression =========="
  if [ -z "$run_id" ]; then log "FAIL PATH F no reference run"; return 1; fi

  curl -sf -m 30 "$API/audit?project_id=$PROJECT&limit=20" -H "$AUTH" > "$EVID/path-F-audit.json" || return 1
  curl -sf -m 30 "$API/assets/history?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-F-history.json" || return 1
  curl -sf -m 30 "$API/lineage/$run_id" -H "$AUTH" > "$EVID/path-F-lineage.json" || return 1
  curl -sf -m 30 "$API/pipeline/runs?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-F-runs.json" || return 1
  curl -sf -m 30 "$API/characters?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-F-characters.json" || return 1

  local audit_count run_count ep_count
  audit_count=$(grep -c '"event_type"' "$EVID/path-F-audit.json" || echo 0)
  run_count=$(grep -c '"run_id"' "$EVID/path-F-runs.json" || echo 0)
  ep_count=$(psql -c "SELECT COUNT(*) FROM episodes WHERE project_id='$PROJECT';")
  log "audit=$audit_count runs=$run_count episodes=$ep_count"
  if [ "${audit_count:-0}" -lt 1 ]; then log "FAIL PATH F audit empty"; return 1; fi
  if [ "${run_count:-0}" -lt 1 ]; then log "FAIL PATH F run history empty"; return 1; fi
  path_f_backward_compat || return 1
  log "PASS PATH F platform regression"
  return 0
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  exec 9>"$EVID/.e2e-v08b.lock"
  if ! flock -n 9; then
    log "FAIL another US-V08B E2E instance holds $EVID/.e2e-v08b.lock"
    exit 1
  fi

  log "US-V08B E2E start PROJECT=$PROJECT API=$API"
  PATH_A_RESULT=""
  PATH_B_RESULT=""
  PATH_C1_RESULT=""
  PATH_C2_RESULT=""
  PATH_D_RESULT=""
  PATH_E_RESULT=""

  if [ -n "${USV08B_ONLY_PATH:-}" ]; then
    case "$USV08B_ONLY_PATH" in
      C1) PATH_C1_RESULT=$(run_character_path C1 1 3 "US-V08B Path C1 Episode") || FAIL=1 ;;
      C2) PATH_C2_RESULT=$(run_character_path C2 1 3 "US-V08B Path C2 Episode") || FAIL=1 ;;
      A) PATH_A_RESULT=$(run_character_path A 1 1 "US-V08B Path A Episode") || FAIL=1 ;;
      B) PATH_B_RESULT=$(run_character_path B 3 3 "US-V08B Path B Episode") || FAIL=1 ;;
      D) PATH_D_RESULT=$(path_d_edit_lifecycle) || FAIL=1 ;;
      E)
        ref=$(echo "$PATH_A_RESULT" | tail -1)
        run_id="${ref%%|*}"; char_id=$(psql -c "SELECT id::text FROM characters WHERE project_id='$PROJECT' LIMIT 1;")
        path_e_delete_after_export "$run_id" "$char_id" || FAIL=1
        ;;
      F)
        ref_run=$(psql -c "SELECT id::text FROM pipeline_runs WHERE project_id='$PROJECT' AND status='COMPLETED' ORDER BY updated_at DESC LIMIT 1;")
        path_f_regression "$ref_run" || FAIL=1
        ;;
      *) log "FAIL unknown USV08B_ONLY_PATH=$USV08B_ONLY_PATH"; FAIL=1 ;;
    esac
    {
      echo "PATH_A=$PATH_A_RESULT"
      echo "PATH_B=$PATH_B_RESULT"
      echo "PATH_C1=$PATH_C1_RESULT"
      echo "PATH_C2=$PATH_C2_RESULT"
      echo "PATH_D=$PATH_D_RESULT"
      echo "PATH_E=$PATH_E_RESULT"
      echo "FAIL=$FAIL"
    } > "$EVID/summary.txt"
    log "DONE FAIL=$FAIL (only=$USV08B_ONLY_PATH)"
    exit $FAIL
  fi

  PATH_A_RESULT=$(run_character_path A 1 1 "US-V08B Path A Episode") || FAIL=1
  PATH_B_RESULT=$(run_character_path B 3 3 "US-V08B Path B Episode") || FAIL=1

  log "========== PATH C: multi-episode with 3 characters =========="
  PATH_C1_RESULT=$(run_character_path C1 1 3 "US-V08B Path C Episode 1") || FAIL=1
  PATH_C2_RESULT=$(run_character_path C2 1 3 "US-V08B Path C Episode 2") || FAIL=1

  ep_count=$(psql -c "SELECT COUNT(*) FROM episodes WHERE project_id='$PROJECT';")
  log "PATH C episode count=$ep_count (expect >= 2 for C1+C2)"
  if [ "${ep_count:-0}" -lt 2 ]; then log "FAIL PATH C insufficient episodes"; FAIL=1; fi

  c1_num=$(echo "$PATH_C1_RESULT" | tail -1 | cut -d'|' -f3)
  c2_num=$(echo "$PATH_C2_RESULT" | tail -1 | cut -d'|' -f3)
  if [ -z "$c1_num" ] || [ -z "$c2_num" ]; then
    log "FAIL PATH C incomplete results c1=$c1_num c2=$c2_num"; FAIL=1
  elif [ "$c1_num" = "$c2_num" ]; then
    log "FAIL PATH C episode numbering collision"; FAIL=1
  else
    log "PASS PATH C multi-episode character continuity ep1=$c1_num ep2=$c2_num"
  fi

  PATH_D_RESULT=$(path_d_edit_lifecycle) || FAIL=1
  d_line=$(echo "$PATH_D_RESULT" | tail -1)
  d_run1=$(echo "$d_line" | cut -d'|' -f1)
  d_char=$(echo "$d_line" | cut -d'|' -f3)
  if [ -n "$d_run1" ] && [ -n "$d_char" ]; then
    path_e_delete_after_export "$d_run1" "$d_char" || FAIL=1
  else
    log "FAIL PATH E skipped — PATH D did not return run/char"
    FAIL=1
  fi

  ref_run=$(echo "$PATH_A_RESULT" | tail -1 | cut -d'|' -f1)
  path_f_regression "$ref_run" || FAIL=1

  {
    echo "PATH_A=$PATH_A_RESULT"
    echo "PATH_B=$PATH_B_RESULT"
    echo "PATH_C1=$PATH_C1_RESULT"
    echo "PATH_C2=$PATH_C2_RESULT"
    echo "PATH_D=$PATH_D_RESULT"
    echo "PATH_E=PASS"
    echo "FAIL=$FAIL"
  } > "$EVID/summary.txt"

  log "DONE FAIL=$FAIL"
  exit $FAIL
fi
