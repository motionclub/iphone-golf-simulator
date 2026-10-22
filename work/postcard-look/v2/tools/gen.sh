#!/bin/bash
# usage: gen.sh <outdir> <only-list or ""> [extra generator args]   (Blender python, numpy)
R="$(cd "$(dirname "$0")/../../../.." && pwd)"
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
OUT="$1"; ONLY="$2"; shift 2
if [ -n "$ONLY" ]; then "$PY" "$R/blender/scripts/golf_look_textures.py" --out "$OUT" --only "$ONLY" "$@"; else "$PY" "$R/blender/scripts/golf_look_textures.py" --out "$OUT" "$@"; fi
