"""Print a quick printability report for any mesh file.

    python tools/inspect_mesh.py projects/gate-footing/output/gate-footing-clean.stl
"""

import json
import sys

import trimesh

from meshkit import report

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python tools/inspect_mesh.py <mesh> [<mesh> ...]")
    for path in sys.argv[1:]:
        mesh = trimesh.load(path, force="mesh")
        print(path)
        print(json.dumps(report(mesh), indent=2))
