#!/bin/bash
# iter.sh DIR : build into DIR (scratch, never the repo) and render the tee + pad views (Blender previews, NOT Game view)
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
B=/Applications/Blender.app/Contents/MacOS/Blender
S=$R/work/postcard-look/v2/hole10
OUT=$1; shift; mkdir -p "$OUT"
$B -b --factory-startup --python $R/blender/scripts/hole10_build.py -- --out "$OUT" --no-render "$@" > "$OUT/build.log" 2>&1 || { echo BUILD FAILED; tail -20 "$OUT/build.log"; exit 1; }
grep -E "^GATE: (H_TEE_RIM)|\[hole10_build\] (rim|done)" "$OUT/build.log" | cut -c1-500
$B -b "$OUT/hole_10.blend" --python $S/tools/render_views.py -- --shots $S/repair_r3/shots_pad.json --out "$OUT/pv" --only hole10_tee,uv_pad,uv_pad_side,uv_pad_front --res 900x1600 --prefix "" > "$OUT/pv.log" 2>&1
python3 - "$OUT/pv" <<'PY'
import sys
from PIL import Image
d=sys.argv[1]
im=Image.open(f"{d}/hole10_tee.png").convert("RGB")
im.crop((0,540,900,680)).resize((1800,280),Image.LANCZOS).save(f"{d}/crop_tee_rim.png")
a=[Image.open(f"{d}/{n}.png").convert("RGB").resize((450,800)) for n in ("hole10_tee","uv_pad","uv_pad_side","uv_pad_front")]
s=Image.new("RGB",(1800,800))
for k,i in enumerate(a): s.paste(i,(k*450,0))
s.save(f"{d}/sheet_pad_views.png")
PY
echo done $OUT
