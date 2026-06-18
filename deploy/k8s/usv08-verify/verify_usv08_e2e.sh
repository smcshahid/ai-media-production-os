#!/usr/bin/env bash
# US-V08 Character Bible E2E acceptance on Olares (Paths A–E).
# Requires: TOKEN, PGPW, PROJECT env vars; Phase 7 deployed; Alembic 0006.
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
EVID="${EVID_DIR:-/tmp/usv08-evidence}"
mkdir -p "$EVID"

: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
FAIL=0

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/verify_common.sh"
# shellcheck source=/dev/null
source "$LIB"
verify_common_source_helpers
verify_common_acquire_lock

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

path_d_backward_compat() {
  log "========== PATH D: backward compatibility (v1/v2/v3/v4 without characters) =========="
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
    log "PASS PATH D backward compatibility (v2=$found_v2 v3=$found_v3 v4=$found_v4)"
    return 0
  fi
  log "FAIL PATH D missing legacy manifests v2=$found_v2 v3=$found_v3 v4=$found_v4"
  return 1
}

path_e_regression() {
  local run_id="$1"
  log "========== PATH E: platform regression =========="
  if [ -z "$run_id" ]; then log "FAIL PATH E no reference run"; return 1; fi

  curl -sf -m 30 "$API/audit?project_id=$PROJECT&limit=20" -H "$AUTH" > "$EVID/path-E-audit.json" || return 1
  curl -sf -m 30 "$API/assets/history?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-E-history.json" || return 1
  curl -sf -m 30 "$API/lineage/$run_id" -H "$AUTH" > "$EVID/path-E-lineage.json" || return 1
  curl -sf -m 30 "$API/pipeline/runs?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-E-runs.json" || return 1
  curl -sf -m 30 "$API/characters?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-E-characters.json" || return 1

  local audit_count run_count ep_count char_count
  audit_count=$(grep -c '"event_type"' "$EVID/path-E-audit.json" || echo 0)
  run_count=$(grep -c '"run_id"' "$EVID/path-E-runs.json" || echo 0)
  ep_count=$(psql -c "SELECT COUNT(*) FROM episodes WHERE project_id='$PROJECT';")
  char_count=$(psql -c "SELECT COUNT(*) FROM characters WHERE project_id='$PROJECT';")
  log "audit=$audit_count runs=$run_count episodes=$ep_count characters=$char_count"
  if [ "${audit_count:-0}" -lt 1 ]; then log "FAIL PATH E audit empty"; return 1; fi
  if [ "${run_count:-0}" -lt 1 ]; then log "FAIL PATH E run history empty"; return 1; fi
  if [ "${char_count:-0}" -lt 1 ]; then log "FAIL PATH E characters empty"; return 1; fi
  log "PASS PATH E platform regression"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  exec 9>"$EVID/.e2e.lock"
  if ! flock -n 9; then
    log "FAIL another US-V08 E2E instance holds $EVID/.e2e.lock"
    exit 1
  fi

  log "US-V08 E2E start PROJECT=$PROJECT API=$API"
  PATH_A_RESULT=""
  PATH_B_RESULT=""
  PATH_C1_RESULT=""
  PATH_C2_RESULT=""

  if [ -n "${USV08_ONLY_PATH:-}" ]; then
    case "$USV08_ONLY_PATH" in
      C1) PATH_C1_RESULT=$(run_character_path C1 1 3 "US-V08 Path C1 Episode") || FAIL=1 ;;
      C2) PATH_C2_RESULT=$(run_character_path C2 1 3 "US-V08 Path C2 Episode") || FAIL=1 ;;
      A) PATH_A_RESULT=$(run_character_path A 1 1 "US-V08 Path A Episode") || FAIL=1 ;;
      B) PATH_B_RESULT=$(run_character_path B 3 3 "US-V08 Path B Episode") || FAIL=1 ;;
      *) log "FAIL unknown USV08_ONLY_PATH=$USV08_ONLY_PATH"; FAIL=1 ;;
    esac
    {
      echo "PATH_A=$PATH_A_RESULT"
      echo "PATH_B=$PATH_B_RESULT"
      echo "PATH_C1=$PATH_C1_RESULT"
      echo "PATH_C2=$PATH_C2_RESULT"
      echo "FAIL=$FAIL"
    } > "$EVID/summary.txt"
    log "DONE FAIL=$FAIL (only=$USV08_ONLY_PATH)"
    exit $FAIL
  fi

  PATH_A_RESULT=$(run_character_path A 1 1 "US-V08 Path A Episode") || FAIL=1
  PATH_B_RESULT=$(run_character_path B 3 3 "US-V08 Path B Episode") || FAIL=1

  log "========== PATH C: multi-episode with 3 characters =========="
  PATH_C1_RESULT=$(run_character_path C1 1 3 "US-V08 Path C Episode 1") || FAIL=1
  PATH_C2_RESULT=$(run_character_path C2 1 3 "US-V08 Path C Episode 2") || FAIL=1

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

  path_d_backward_compat || FAIL=1

  ref_run=$(echo "$PATH_A_RESULT" | tail -1 | cut -d'|' -f1)
  path_e_regression "$ref_run" || FAIL=1

  {
    echo "PATH_A=$PATH_A_RESULT"
    echo "PATH_B=$PATH_B_RESULT"
    echo "PATH_C1=$PATH_C1_RESULT"
    echo "PATH_C2=$PATH_C2_RESULT"
    echo "FAIL=$FAIL"
  } > "$EVID/summary.txt"

  log "DONE FAIL=$FAIL"
  exit $FAIL
fi
