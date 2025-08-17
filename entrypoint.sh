#!/bin/bash
set -e

# --- initialize DB objects (sleep 5m before exit on failure) ---
if ! python -c "from db import initializeDbObjects; initializeDbObjects()"; then
  echo "DB initialization failed; sleeping 5 minutes before restart..." >&2
  sleep 300
  exit 1
fi

# Forward TERM/INT to the gunicorn child so it can shutdown cleanly
child_pid=0
term_handler() {
  if [ "$child_pid" -ne 0 ] 2>/dev/null; then
    kill -TERM "$child_pid" 2>/dev/null || true
    wait "$child_pid" 2>/dev/null || true
  fi
  exit 0
}
trap term_handler SIGTERM SIGINT

# --- run app in foreground, capture exit code ---
gunicorn --chdir /app/web --bind 0.0.0.0:8202 app:app &
child_pid=$!
wait "$child_pid"
code=$?

# If Gunicorn exited cleanly, exit immediately (no restart)
if [ "$code" -eq 0 ]; then
  exit 0
fi

# Crash path: pause 5 minutes before letting Docker restart the container
echo "Gunicorn exited with code $code; sleeping 5 minutes before restart..." >&2
sleep 300
exit "$code"
