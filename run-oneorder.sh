#!/usr/bin/env bash
# OneOrder: test and run helper (backend + frontend).
#
#   ./run-oneorder.sh         same as `start`: both servers up, ready to try in the browser   (default)
#   ./run-oneorder.sh start   start both servers for you to use (Ctrl-C stops them)
#   ./run-oneorder.sh test    pytest, then frontend type check, lint and build
#   ./run-oneorder.sh smoke   start both servers on a throw-away database and walk the whole flow
#                             through the UI proxy: upload, approve, plan, confirm, ERP, stock, rules
#   ./run-oneorder.sh all     test, then smoke
#
# `start` reads .env. With a Gemini/Claude key in .env it runs the LIVE AI, so any photo can be read;
# without a key it falls back to demo (recorded fixtures for the files in samples/ only).
# `test` and `smoke` always use demo, so results never depend on a key or on quota.
#
# Options (environment variables):
#   AI_MODE=demo|live  force the mode for `start` (default: live if a key is configured, else demo)
#   FRESH=1            with `start`: use an empty temporary database instead of ./oneorder.db
#   BACKEND_PORT=8000  FRONTEND_PORT=5173     (smoke defaults to 8100 / 5273 so it never clashes with `start`)
#
# Exit code is 0 only if every step passed.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

MODE="${1:-start}"
case "$MODE" in test|smoke|all|start) ;; -h|--help|help) sed -n '2,22p' "$0"; exit 0 ;; *) echo "Unknown mode '$MODE'. Use: test | smoke | all | start" >&2; exit 2 ;; esac

if [ -t 1 ]; then RED=$'\e[31m'; GREEN=$'\e[32m'; YELLOW=$'\e[33m'; BOLD=$'\e[1m'; DIM=$'\e[2m'; RESET=$'\e[0m'; else RED=; GREEN=; YELLOW=; BOLD=; DIM=; RESET=; fi

LOG_DIR="$(mktemp -d -t oneorder-run.XXXXXX)"
PIDS=()
RESULTS=()
FAILED=0

say()  { printf '%s\n' "$*"; }
head_() { printf '\n%s== %s ==%s\n' "$BOLD" "$*" "$RESET"; }

cleanup() {
  local pid
  for pid in "${PIDS[@]:-}"; do
    [ -n "$pid" ] && kill -TERM -- "-$pid" 2>/dev/null || true   # each server runs in its own process group
  done
  sleep 1
  for pid in "${PIDS[@]:-}"; do
    [ -n "$pid" ] && kill -KILL -- "-$pid" 2>/dev/null || true   # anything that ignored TERM
  done
}
trap cleanup EXIT
trap 'echo; echo "Interrupted."; exit 130' INT TERM

record() {  # record <name> <status 0|1>
  if [ "$2" -eq 0 ]; then RESULTS+=("${GREEN}PASS${RESET}  $1"); else RESULTS+=("${RED}FAIL${RESET}  $1"); FAILED=1; fi
}

# step <name> <command...>: run a command, keep its output in a log, show the tail on failure.
step() {
  local name="$1"; shift
  local log="$LOG_DIR/$(echo "$name" | tr -c 'A-Za-z0-9' '_').log"
  printf '%s-> %s%s ' "$DIM" "$name" "$RESET"
  if "$@" >"$log" 2>&1; then
    say "${GREEN}ok${RESET}"; record "$name" 0
  else
    say "${RED}failed${RESET}"; tail -n 25 "$log" | sed 's/^/     /'; say "     ${DIM}full log: $log${RESET}"; record "$name" 1
  fi
}

# ---------------------------------------------------------------------------------------- setup

PY=""
setup_python() {
  command -v python3 >/dev/null || { say "${RED}python3 not found${RESET}"; exit 1; }
  if [ ! -x .venv/bin/python ]; then
    say "Creating .venv ..."; python3 -m venv .venv || exit 1
  fi
  PY="$ROOT/.venv/bin/python"
  if ! "$PY" -c "import fastapi, sqlalchemy, holidays, sklearn, openpyxl, pytest" 2>/dev/null; then
    say "Installing backend requirements ..."; "$PY" -m pip install -q -r requirements.txt || exit 1
  fi
}

setup_node() {
  command -v node >/dev/null && command -v npm >/dev/null || { say "${RED}node/npm not found${RESET}"; exit 1; }
  if [ ! -d frontend/node_modules ]; then
    say "Installing frontend dependencies ..."; (cd frontend && npm install --silent) || exit 1
  fi
}

# ---------------------------------------------------------------------------------------- tests

run_tests() {
  head_ "Backend tests"
  step "pytest (demo AI)" env AI_MODE=demo "$PY" -m pytest -q
  head_ "Frontend checks"
  step "TypeScript type check" bash -c "cd frontend && npx tsc -b"
  step "ESLint"               bash -c "cd frontend && npm run lint --silent"
  step "Production build"     bash -c "cd frontend && npm run build --silent"
}

# ---------------------------------------------------------------------------------------- servers

port_busy() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }

wait_for() {  # wait_for <url> <seconds>
  local i
  for ((i = 0; i < $2 * 2; i++)); do
    curl -fsS -o /dev/null "$1" 2>/dev/null && return 0
    sleep 0.5
  done
  return 1
}

start_servers() {  # start_servers <backend_port> <frontend_port> <database_url> <ai_mode>
  local bport="$1" fport="$2" dburl="$3" aimode="$4"
  for p in "$bport" "$fport"; do
    if port_busy "$p"; then say "${RED}Port $p is already in use.${RESET} Stop what is running there or set BACKEND_PORT / FRONTEND_PORT."; return 1; fi
  done

  DATABASE_URL="$dburl" AI_MODE="$aimode" setsid "$PY" -m uvicorn backend.main:app --port "$bport" >"$LOG_DIR/backend.log" 2>&1 &
  PIDS+=("$!")
  if ! wait_for "http://127.0.0.1:$bport/api/health" 30; then
    say "${RED}Backend did not start.${RESET}"; tail -n 20 "$LOG_DIR/backend.log" | sed 's/^/     /'; return 1
  fi

  # exec so the PID we keep is the process-group leader that `cleanup` signals
  BACKEND_URL="http://127.0.0.1:$bport" setsid bash -c 'cd frontend && exec npm run dev -- --host 127.0.0.1 --port "$0" --strictPort' "$fport" >"$LOG_DIR/frontend.log" 2>&1 &
  PIDS+=("$!")
  if ! wait_for "http://127.0.0.1:$fport/" 40; then
    say "${RED}Frontend did not start.${RESET}"; tail -n 20 "$LOG_DIR/frontend.log" | sed 's/^/     /'; return 1
  fi
  say "Backend  http://127.0.0.1:$bport   Frontend  http://127.0.0.1:$fport   ${DIM}(logs: $LOG_DIR)${RESET}"
}

# ---------------------------------------------------------------------------------------- smoke

# json <expr>: read JSON on stdin, print an expression over it (variable d). Exit 1 if the expression is falsy/empty.
json() { "$PY" -c "import sys,json; d=json.load(sys.stdin); r=($1); print(r); sys.exit(0 if r not in (None,'',False,[],{}) else 1)"; }

smoke() {
  head_ "Smoke test: whole flow through the UI proxy"
  local bport="${BACKEND_PORT:-8100}" fport="${FRONTEND_PORT:-5273}"
  local db="sqlite:///$LOG_DIR/smoke.db"
  start_servers "$bport" "$fport" "$db" demo || { record "start servers" 1; return; }
  record "start servers" 0

  local api="http://127.0.0.1:$fport"   # everything goes through the Vite proxy, like the browser
  local order_id=""

  step "frontend serves the app"       bash -c "curl -fsS $api/ | grep -q '<div id=\"root\">'"
  step "health reports the AI mode"    bash -c "curl -fsS $api/api/health | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d[\"status\"]==\"ok\" and d[\"ai_mode\"] in (\"demo\",\"live\") else 1)'"
  step "sample inbox lists messages"   bash -c "curl -fsS $api/api/inbox | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if len(d)>=3 else 1)'"
  step "rules readable"                bash -c "curl -fsS $api/api/rules | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d[\"vehicles\"] else 1)'"
  step "group stock for 3 countries"   bash -c "curl -fsS $api/api/stock | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d[\"total\"]>100 and set(d[\"summary\"])=={\"DK\",\"SE\",\"NO\"} else 1)'"
  step "DK ERP returns native CSV"     bash -c "curl -fsS $api/mock-erp/dk/stock | head -1 | grep -q '^varenr,lager_kode,beholdning,reserveret,enhed'"

  # --- the order flow ---
  local resp
  resp="$(curl -fsS -F "file=@samples/emails/dk_order.txt" "$api/api/intake" 2>"$LOG_DIR/intake.err")" && order_id="$(printf '%s' "$resp" | json 'd["id"]')"
  if [ -n "$order_id" ]; then say "${DIM}-> upload order (id $order_id)${RESET} ${GREEN}ok${RESET}"; record "upload order" 0; else say "-> upload order ${RED}failed${RESET}"; record "upload order" 1; return; fi

  step "original file stored"          bash -c "curl -fsS $api/api/orders/$order_id/source | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d[\"kind\"]==\"text\" and \"Sundkaj\" in d[\"text\"] else 1)'"
  step "customer phone extracted and stored" bash -c "curl -fsS $api/api/orders/$order_id | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d[\"customer_phone\"]==\"+4500000001\" else 1)'"
  step "stock pre-check per line"      bash -c "curl -fsS $api/api/orders/$order_id/availability | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d and all(r[\"status\"]==\"ok\" for r in d) else 1)'"

  local body
  body="$(curl -fsS "$api/api/orders/$order_id" | "$PY" -c "import sys,json; o=json.load(sys.stdin); print(json.dumps({'corrections':[{'line_index':l['line_index'],'sku':l['matched_sku'],'confirmed':True} for l in o['lines']]}))")"
  step "approve OCR result"            bash -c "curl -fsS -X POST -H 'Content-Type: application/json' -d '$body' $api/api/orders/$order_id/approve | python3 -c 'import sys,json; sys.exit(0 if json.load(sys.stdin)[\"status\"]==\"approved\" else 1)'"
  step "plan with ETA P50 <= P90"      bash -c "curl -fsS -X POST -H 'Content-Type: application/json' -d '{}' $api/api/orders/$order_id/plan | python3 -c 'import sys,json; d=json.load(sys.stdin); e=d[\"order_eta\"]; sys.exit(0 if d[\"shipments\"] and e[\"p50_date\"]<=e[\"p90_date\"] else 1)'"
  step "confirm order"                 bash -c "curl -fsS -X POST -H 'Content-Type: application/json' -d '{\"allow_partial\":true,\"accept_late_risk\":true}' $api/api/orders/$order_id/confirm | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d[\"status\"]==\"confirmed\" and d[\"reservations\"] else 1)'"
  step "reservation written to the ERP" bash -c "curl -fsS $api/mock-erp/dk/reservations | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if any(r[\"order_ref\"]==\"$order_id\" for r in d) else 1)'"
  step "confirm twice is refused"      bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' $api/api/orders/$order_id/confirm)\" = 409 ]"
  step "orders list shows the order"   bash -c "curl -fsS $api/api/orders | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if any(o[\"id\"]==\"$order_id\" and o[\"status\"]==\"confirmed\" and o[\"risk\"] for o in d) else 1)'"
  step "import from sample inbox"      bash -c "curl -fsS -X POST -H 'Content-Type: application/json' -d '{\"id\":\"emails/se_order.txt\"}' $api/api/inbox/import | python3 -c 'import sys,json; sys.exit(0 if json.load(sys.stdin)[\"lines\"] else 1)'"
  step "app routes load (SPA)"         bash -c "for p in orders stock rules orders/$order_id; do curl -fsS $api/\$p | grep -q '<div id=\"root\">' || exit 1; done"
}

# ---------------------------------------------------------------------------------------- start

# Value of KEY from the environment, else from .env (empty if unset). Never printed.
conf() { local v="${!1:-}"; [ -z "$v" ] && [ -f .env ] && v="$(grep -E "^$1=" .env | tail -1 | cut -d= -f2-)"; printf '%s' "$v"; }

# live if the chosen provider has a key; demo otherwise. AI_MODE in the environment wins.
pick_ai_mode() {
  [ -n "${AI_MODE:-}" ] && { printf '%s' "$AI_MODE"; return; }
  local provider; provider="$(conf AI_PROVIDER)"; provider="${provider:-gemini}"
  if [ "$provider" = claude ]; then [ -n "$(conf ANTHROPIC_API_KEY)" ] && { printf live; return; }
  else { [ -n "$(conf GEMINI_API_KEY)" ] || [ -n "$(conf GOOGLE_API_KEY)" ]; } && { printf live; return; }; fi
  printf demo
}

serve() {
  head_ "Starting OneOrder"
  local bport="${BACKEND_PORT:-8000}" fport="${FRONTEND_PORT:-5173}" db="${DATABASE_URL:-sqlite:///$ROOT/oneorder.db}"
  if [ "${FRESH:-0}" = "1" ]; then db="sqlite:///$LOG_DIR/fresh.db"; say "${YELLOW}FRESH=1: using an empty temporary database${RESET}"; fi
  local aimode; aimode="$(pick_ai_mode)"
  start_servers "$bport" "$fport" "$db" "$aimode" || exit 1
  local actual; actual="$(curl -fsS "http://127.0.0.1:$bport/api/health" | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["ai_mode"])' 2>/dev/null)"
  if [ "$actual" = live ]; then
    say "AI: ${GREEN}live${RESET} (provider $(conf AI_PROVIDER), model $(conf AI_MODEL)); any photo, spreadsheet or email can be read."
  else
    say "AI: ${YELLOW}demo${RESET}: only the files in samples/ can be read. Add a key to .env for live reading."
  fi
  say "${BOLD}Open http://127.0.0.1:$fport${RESET}   (Ctrl-C to stop)"
  while true; do sleep 3600 & wait $!; done
}

# ---------------------------------------------------------------------------------------- main

setup_python
case "$MODE" in test|all|smoke) setup_node ;; start) setup_node ;; esac

[ "$MODE" = test  ] || [ "$MODE" = all ] && run_tests
[ "$MODE" = smoke ] || [ "$MODE" = all ] && smoke
[ "$MODE" = start ] && serve

head_ "Summary"
printf '%s\n' "${RESULTS[@]}"
if [ "$FAILED" -eq 0 ]; then say "${GREEN}${BOLD}All steps passed.${RESET}"; else say "${RED}${BOLD}Some steps failed.${RESET} Logs: $LOG_DIR"; fi
exit "$FAILED"
