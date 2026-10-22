#!/bin/bash
# runv.sh spec.json label  -> prints shares, writes overlay sheet /private/tmp/claude-501/ov_<label>.png
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
T=$R/work/postcard-look/v2/hole10/repair_r1
STAGE=${3:-$R/work/postcard-look/v2/hole10/stage/hole_10.blend}
PV=${4:-$R/work/postcard-look/v2/hole10/previews}
python3 $T/mk_cards.py $1 /private/tmp/claude-501/cards_$2.json >/dev/null
/Applications/Blender.app/Contents/MacOS/Blender -b $STAGE --python $T/smoke_probe.py -- --cards /private/tmp/claude-501/cards_$2.json --out /private/tmp/claude-501/sp_$2 2>&1 | grep -E "SMOKE|Error|Traceback"
cd $T
python3 overlay.py $PV/hole10_tee.png /private/tmp/claude-501/sp_$2/smoke_hole10_1_tee.ppm /private/tmp/claude-501/o1_$2.png
python3 overlay.py $PV/hole10_approach.png /private/tmp/claude-501/sp_$2/smoke_hole10_2_approach.ppm /private/tmp/claude-501/o2_$2.png
python3 overlay.py $PV/hole10_lavarim.png /private/tmp/claude-501/sp_$2/smoke_hole10_3_lavarim.ppm /private/tmp/claude-501/o3_$2.png
python3 - <<PY
from PIL import Image
ims=[Image.open('/private/tmp/claude-501/o%d_$2.png'%i).resize((450,800)) for i in (1,2,3)]
s=Image.new('RGB',(1350,800)); [s.paste(im,(450*i,0)) for i,im in enumerate(ims)]; s.save('/private/tmp/claude-501/ov_$2.png')
PY
