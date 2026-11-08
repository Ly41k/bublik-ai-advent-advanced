#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
unset OPENAI_API_KEY OPENAI_PROJECT_ID OPENAI_ORG_ID OPENAI_CUSTOM_HEADERS OPENAI_ADMIN_KEY OPENAI_WEBHOOK_SECRET
export GATEWAY_PROVIDER=mock
export LIVE_ENABLED=false
umask 077
mkdir -p .private
chmod 700 .private
export GATEWAY_AUDIT_PATH="$(pwd)/.private/gateway-audit.jsonl"
exec python -m uvicorn redteam_api:app --host 127.0.0.1 --port 8091 --workers 1 --no-proxy-headers --no-access-log --log-level warning
