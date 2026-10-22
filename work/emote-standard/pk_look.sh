#!/bin/zsh
# pk_look.sh <male|female> : rebuild + side-view sheet in /tmp/pk_prev/side_sheet.jpg + diagnostics
cd "$(dirname $0)/scripts"
T=$1; HB=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/delegation-2026-10-17/heavy.sh
../run_pickup.sh $T | python3 -c "
import sys,json
for l in sys.stdin:
    if l.startswith('INFO {'):
        d=json.loads(l[5:]);print({k:round(v,3) for k,v in d.items() if k.startswith('z_36') or k.startswith('z_30') or 'hand_36' in k})
    else: print(l.strip())"
BL=../blend/$([ $T = male ] && echo Male || echo Female)_Std.blend
rm -rf /tmp/pk_prev; $HB blender /Applications/Blender.app/Contents/MacOS/Blender -b $BL --python render_preview.py -- $T Emote_PickUp_Free /tmp/pk_prev 6 2>&1 | tail -1
python3 - <<'P'
from PIL import Image
fr=[12,24,30,36,48,54,60,66]
ims=[Image.open(f'/tmp/pk_prev/side_{f:03d}.png').convert('RGB') for f in fr]
w,h=ims[0].size;cw=int(w*0.62);x0=int(w*0.19)
S=Image.new('RGB',(cw*4,h*2),(30,30,30))
for i,im in enumerate(ims): S.paste(im.crop((x0,0,x0+cw,h)),((i%4)*cw,(i//4)*h))
S.save('/tmp/pk_prev/side_sheet.jpg',quality=85)
P
