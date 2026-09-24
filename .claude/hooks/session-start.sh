#!/bin/bash
# Install mesh tooling in Claude Code on the web sessions (fresh containers).
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}"
if ! ldconfig -p 2>/dev/null | grep -q libOpenGL.so.0; then
  (apt-get install -y -qq libopengl0 >/dev/null 2>&1 || \
   (apt-get update -qq >/dev/null 2>&1 && apt-get install -y -qq libopengl0 >/dev/null 2>&1)) || \
   echo "warning: could not install libopengl0 (pymeshlab checks will be skipped)"
fi
pip install -q -r requirements.txt 2>&1 | grep -v "Running pip as the 'root' user" || true
