#!/bin/bash
# iter.sh DIR [extra build args]   build hole 10 into DIR (never the repo), then render the 3 phone shots + 4 aerials and a contact sheet
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
B=/Applications/Blender.app/Contents/MacOS/Blender
S=$R/work/postcard-look/v2/hole10
OUT=$1; shift
mkdir -p "$OUT"
$B -b --factory-startup --python $R/blender/scripts/hole10_build.py -- --out "$OUT" --no-render "$@" > "$OUT/build.log" 2>&1 || { echo BUILD FAILED; tail -20 "$OUT/build.log"; exit 1; }
grep -E "^GATE: .* FAIL|\[hole10_build\]" "$OUT/build.log" | cut -c1-600
J=${SHOTS:-$S/landmarks_with_aerial.json}
$B -b "$OUT/hole_10.blend" --python $S/tools/render_views.py -- --shots $J --out "$OUT/pv" --only tee,approach,lavarim,rimin > "$OUT/pv.log" 2>&1
$B -b "$OUT/hole_10.blend" --python $S/tools/render_views.py -- --shots $J --out "$OUT/pv" --only aerial,aerial2,aerial3,aerial4,aerial5 --res 1600x900 >> "$OUT/pv.log" 2>&1
python3 - "$OUT/pv" <<'PY'
import sys
from PIL import Image
d=sys.argv[1]
names=["hole10_tee","hole10_approach","hole10_lavarim","hole10_rimin"]
ims=[Image.open(f"{d}/{n}.png").convert("RGB").resize((450,800)) for n in names]
s=Image.new("RGB",(1800,800),(20,20,20))
for k,i in enumerate(ims): s.paste(i,(k*450,0))
s.save(f"{d}/sheet_phone.png")
a=[Image.open(f"{d}/hole10_aerial{n}.png").convert("RGB").resize((800,450)) for n in ("","2","3","4","5","")]
t=Image.new("RGB",(1610,1370),(20,20,20))
for k,i in enumerate(a): t.paste(i,((k%2)*810,(k//2)*460))
t.save(f"{d}/sheet_aerials.png")
PY
echo done $OUT
