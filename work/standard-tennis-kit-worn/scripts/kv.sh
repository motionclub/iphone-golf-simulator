#!/bin/bash
# usage: kv.sh <gender> <parts,comma> <preset> [colorways=white,black] [nobody]  -> tmp/sheet_<gender>_<parts>_<preset>.png
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-worn
G=$1; N=$2; P=$3; CW=${4:-white,black}; NB=$5
for cw in ${CW//,/ }; do
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python $W/scripts/view_kit.py -- $G $N $cw $W/tmp/v_${G}_${N//,/+}_${cw}_${P} $P $NB 2>&1 | grep -E "Error|Traceback|File \"" 
done
python3 - "$G" "$N" "$P" "$CW" "$W" <<'PY'
import sys, glob
from PIL import Image
G,N,P,CW,W=sys.argv[1:6]
order=['front','q3','side','back','under']
rows=[]
for cw in CW.split(','):
    base=f'{W}/tmp/v_{G}_{N.replace(",","+")}_{cw}_{P}'
    fs=sorted(glob.glob(base+'_*.png'), key=lambda f: order.index(f.split('_')[-1][:-4]) if f.split('_')[-1][:-4] in order else 9)
    rows.append([Image.open(f).convert('RGB') for f in fs])
w=max(sum(i.width for i in r) for r in rows); h=sum(r[0].height for r in rows)
sheet=Image.new('RGB',(w,h)); y=0
for r in rows:
    x=0
    for i in r: sheet.paste(i,(x,y)); x+=i.width
    y+=r[0].height
out=f'{W}/tmp/sheet_{G}_{N.replace(",","+")}_{P}.png'; sheet.save(out); print(out, sheet.size)
PY
