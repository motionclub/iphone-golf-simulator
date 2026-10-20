#!/bin/bash
# merged-preview proofs 08 / 09.  Run from the work folder after run_all.sh
B=/Applications/Blender.app/Contents/MacOS/Blender; HERE="$(pwd)"; MC="$HERE/tools/soft_plate_matcap.png"
A=../female-arms-form2/export/HeroBase_Female_arms_candidate.blend; M=export/PREVIEW_form2_torso_plus_limbs_plus_arms_UNOFFICIAL.blend
for t in A M; do if [ "$t" = "A" ]; then F=$A; else F=$M; fi
 $B -b $F --python tools/render_views.py -- proof/scratch/mrg_$t 1.10 0.95 $MC front,q3F,side,q3B,back 560x760 >/dev/null 2>&1
 $B -b $F --python tools/render_views.py -- proof/scratch/mrgpit_$t 1.20 0.26 $MC front,y25,y-25 520x520 0.13 >/dev/null 2>&1
 $B -b $F --python tools/render_views.py -- proof/scratch/mrgpitS_$t 1.20 0.26 check_reflection_vertical.exr front,y25,y-25 520x520 0.13 >/dev/null 2>&1
 $B -b $F --python tools/render_views.py -- proof/scratch/mrgpitL_$t 1.20 0.26 check_reflection_vertical.exr front,y25,y-25 520x520 -0.13 >/dev/null 2>&1
done
python3 - <<'PY'
from PIL import Image, ImageDraw, ImageFont
W='proof/scratch/'; F=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',20)
def lab(im,t):
    d=ImageDraw.Draw(im); w=d.textlength(t,font=F); d.rectangle([4,4,w+14,30],fill=(0,0,0)); d.text((8,6),t,font=F,fill=(255,255,255)); return im
S=Image.new('RGB',(560*5,760*2))
for r,(t,l) in enumerate((('A','ARMS CANDIDATE (chat-7 torso + limbs + arms)'),('M','MERGED: form2 torso + limbs + arms'))):
    for c,v in enumerate(('front','q3F','side','q3B','back')):
        im=Image.open(W+f'mrg_{t}_{v}.png').convert('RGB'); lab(im,l if c==0 else v); S.paste(im,(c*560,r*760))
S.resize((2240,1216),Image.LANCZOS).save('proof/08_merged_preview_torso_limbs_arms_UNOFFICIAL.png')
S=Image.new('RGB',(520*6,520*4))
for r,(t,l) in enumerate((('A','arms cand.'),('M','merged'))):
    for c,v in enumerate(('front','y25','y-25')):
        S.paste(lab(Image.open(W+f'mrgpit_{t}_{v}.png').convert('RGB'),f'{l} R-armpit {v}'),(c*520,r*1040))
        S.paste(lab(Image.open(W+f'mrgpitS_{t}_{v}.png').convert('RGB'),f'{l} R-armpit stripes {v}'),(c*520,r*1040+520))
        S.paste(lab(Image.open(W+f'mrgpitL_{t}_{v}.png').convert('RGB'),f'{l} L-armpit stripes {v}'),(1560+c*520,r*1040+520))
S.resize((1800,1200),Image.LANCZOS).save('proof/09_armpit_seam_check_merged_vs_arms_candidate.png'); print('merged proofs written')
PY
