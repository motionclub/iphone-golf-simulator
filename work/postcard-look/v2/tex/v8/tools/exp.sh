#!/bin/bash
# exp.sh <name> '<json LAVA_P/LAVA_ENC overrides>' [lava8 args] : runs lava8 + plateau into v8/<name>, log v8/<name>.log
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; V=$R/work/postcard-look/v2/tex/v8; PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
N="$1"; J="$2"; shift 2; mkdir -p $V/$N
cd $R
{ $PY $V/tools/lava8.py $V/$N --set "$J" "$@" 2>&1 | grep -E "STATS|REGIONAL|GATE: LAVA|LUT" | cut -c1-420; $PY $V/tools/plateau.py $V/$N 2>&1 | tail -1; echo DONE; } > $V/$N.log 2>&1
