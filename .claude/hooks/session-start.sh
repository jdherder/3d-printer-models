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
# A download that gets cut off or corrupted through the network proxy fails
# pip's hash check ("THESE PACKAGES DO NOT MATCH THE HASHES"). Retry with a
# clean cache, then check the imports so a real failure is clear.
for attempt in 1 2 3; do
  if pip install -q --root-user-action=ignore --no-cache-dir -r requirements.txt; then
    break
  fi
  echo "pip install failed (attempt $attempt), retrying..."
  sleep $((attempt * 3))
done
python -c "import trimesh, numpy, scipy, shapely, mapbox_earcut, networkx, matplotlib, \
pymeshlab, manifold3d, build123d, skimage" 2>/dev/null \
  || echo "warning: some Python packages failed to install; run: pip install -r requirements.txt"
