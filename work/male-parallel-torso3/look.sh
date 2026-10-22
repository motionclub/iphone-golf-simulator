#!/bin/bash
# usage: look.sh <tag> [views]  : renders data/V_<tag>.npy at plate framing + plate comparison + silhouette gate + profile deficits
set -e
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso3
export PYTHONPATH=$PWD/../male-micro1i/pylib
B=/Applications/Blender.app/Contents/MacOS/Blender
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
TAG=$1; VIEWS=${2:-front,back}
$B -b --factory-startup --python rt.py -- data/V_$TAG.npy r/$TAG $VIEWS 2>&1 | grep -E "Error|Traceback" || true
$B -b --factory-startup --python sil.py -- data/V_$TAG.npy r/sil_$TAG 0 2>&1 | grep -E "Error|Traceback" || true
$PY silgate.py r/sil_$TAG r/sil_$TAG.json
$PY cmp.py r/$TAG r/cmp_${TAG}_front.png front 2.6 >/dev/null
$PY cmp.py r/$TAG r/cmp_${TAG}_back.png back 2.6 >/dev/null
echo "look $TAG done"
$B -b --factory-startup --python rt.py -- data/V_$TAG.npy r/${TAG}c front,back clay 2>&1 | grep -E "Error|Traceback" || true
$PY relief.py r/rel_front_$TAG.png front basec ${TAG}c >/dev/null; $PY relief.py r/rel_back_$TAG.png back basec ${TAG}c >/dev/null
