#!/bin/bash
set -e

RELOAD_FLAG=""
if [ "${RELOAD:-false}" = "true" ]; then
  RELOAD_FLAG="--reload"
fi

exec uvicorn src.main:app --host 0.0.0.0 --port 8000 $RELOAD_FLAG
