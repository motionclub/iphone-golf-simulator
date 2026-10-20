#!/bin/bash
# usage: kitview.sh <gender> <names,comma> <preset> [colorways=white,black] [bodyfile]  -> tmp/sheet_<gender>_<names>_<preset>.png
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb
G=$1; N=$2; P=$3; CW=${4:-white,black}; BF=$5
for cw in ${CW//,/ }; do
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python scripts/view_garment.py -- $G $N $cw $P tmp/v_${G}_${N//,/+}_${cw}_${P} $BF 2>&1 | grep -E "Error|Traceback|File \"" 
done
python3 - "$G" "$N" "$P" "$CW" <<'PY'
import sys
from PIL import Image
G,N,P,CW=sys.argv[1:5]
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/tmp/'
rows=[]
for cw in CW.split(','):
    base=f'{W}v_{G}_{N.replace(",","+")}_{cw}_{P}'
    import glob
    fs=sorted(glob.glob(base+'_*.png'), key=lambda f: ['front','q3','side','back','q3b'].index(f.split('_')[-1][:-4]) if f.split('_')[-1][:-4] in ['front','q3','side','back','q3b'] else 9)
    rows.append([Image.open(f) for f in fs])
w=max(sum(i.width for i in r) for r in rows); h=sum(r[0].height for r in rows)
sheet=Image.new('RGB',(w,h)); y=0
for r in rows:
    x=0
    for i in r: sheet.paste(i,(x,y)); x+=i.width
    y+=r[0].height
out=f'{W}sheet_{G}_{N.replace(",","+")}_{P}.png'; sheet.save(out); print(out, sheet.size)
PY
