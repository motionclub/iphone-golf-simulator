#!/bin/bash
# usage: go.sh <model.py> <params.json|-> <tag> [cmp tags...]  : build -> render set -> silhouette gate -> comparison sheets (start | tag)
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin
export PYTHONPATH=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
M=$1; P=$2; T=$3; shift 3
$PY $M $P $T 2>&1 | grep -v -E "Warning|nanmean"
./render_set.sh $T >/dev/null
./sil_np.sh $T
./cmp_all.sh "$@" $T >/dev/null
echo "GO_DONE $T"
