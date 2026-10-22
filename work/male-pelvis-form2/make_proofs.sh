#!/bin/bash
# usage: make_proofs.sh <TAG>   regenerates every proof image for the candidate TAG (positions in data/V_<TAG>.npy) into proof/
set -u
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2
unset PYTHONPATH
T=$1
PYL=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib
BP=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
B=/Applications/Blender.app/Contents/MacOS/Blender
L3="PLATE (ref),chat-9 (9bfd788a),FORM2"
# 4x silhouettes for contour plots
for X in start $T; do SRC=data/V_$X.npy; [ $X = start ] && SRC=baseline/HeroBase_Male_Silhouette.blend; PYTHONPATH=$PYL $B -b --factory-startup --python rig.py -- $SRC r/${X}_sil4 "left@4,right@4,back@4,front@4" sil 2>&1 | grep -E "Error|Traceback"; done
sed -i '' "s#'FINAL[0-9]*'#'$T'#g; s#FINAL[0-9]*_sil4#${T}_sil4#g" profile_plot.py
python3 profile_plot.py proof/P6_profile_side_contour_z074_104.png 0.74 1.04 0.03 0.13 | tail -1
python3 profile_plot.py proof/P6b_profile_side_contour_underbutt.png 0.70 0.90 0.03 0.13 | tail -1
# judge sheets (plate | chat-9 | FORM2)
python3 judge.py render $T >/dev/null 2>&1; python3 judge.py render start >/dev/null 2>&1
LABELS="$L3" VIEWS=back,q_bl,q_br,left,right ZOOM=3 python3 judge.py sheet proof/P1_pelvis_BA_back_3q_side.png pelvis $T | tail -1
LABELS="$L3" VIEWS=front,q_fl,q_fr ZOOM=3 python3 judge.py sheet proof/P2_pelvis_BA_front_groin.png pelvis $T | tail -1
LABELS="$L3" VIEWS=q_bl,q_br,back ZOOM=2 python3 judge.py sheet proof/P13_fullbody_3q_back.png full $T | tail -1
# registered close-ups
python3 crop_cmp.py render $T manneq; python3 crop_cmp.py render start manneq
LABELS="PLATE,chat-9 (9bfd788a),FORM2" python3 crop_cmp.py sheet proof/P3_back_closeup_plain.png back 0.68 1.06 0.20 start $T
LABELS="PLATE,chat-9 (9bfd788a),FORM2" python3 crop_cmp.py sheet proof/P3b_back_closeup_enhanced.png back 0.68 1.06 0.20 start $T --enh
python3 quick.py render $T start >/dev/null
for pair in "P4_3q_closeups_plain:bl,br:" "P4b_3q_closeups_enhanced:bl,br:--enh" "P5_highkey_relit_back_3q:backH,blH:--enh" "P7_side_closeup:left,right:" "P8_front_groin_closeups_plain:front,fl,fr:" "P8b_front_groin_closeups_enhanced:front,fl,fr:--enh"; do
  IFS=: read name views flag <<< "$pair"; LABELS="PLATE,chat-9 (9bfd788a),FORM2" python3 quick.py sheet proof/$name.png $views start $T $flag | tail -1
done
# silhouette overlays, sections
PANELS=q_bl,q_br python3 overlay.py render $T >/dev/null; PANELS=q_bl,q_br python3 overlay.py render start >/dev/null
python3 overlay.py sheet proof/P9_3q_silhouette_overlay_chat9_red_FORM2_green.png q_bl,q_br start $T | tail -1
BOX="-0.07,0.07,0.72,0.82" SC=7000 PYTHONPATH=$PYL $BP gapplot.py proof/P10_gap_sections_rear_chat9_blue_FORM2_green.png start,$T -0.10,-0.04,0.0,0.03,0.055,0.065 | tail -1
BOX="-0.10,0.10,0.72,0.86" SC=5500 PYTHONPATH=$PYL $BP gapplot.py proof/P10b_gap_sections_front_chat9_blue_FORM2_green.png start,$T -0.17,-0.15,-0.13,-0.10 | tail -1
XR=0.10 YLO=0.04 YHI=0.115 SC=9000 PYTHONPATH=$PYL $BP corplot.py proof/P11_coronal_rear_profiles_FORM2.png $T 0.78,0.80,0.82,0.84,0.86,0.88,0.90 | tail -1
XR=0.10 YLO=0.04 YHI=0.115 SC=9000 PYTHONPATH=$PYL $BP corplot.py proof/P11b_coronal_rear_profiles_chat9.png start 0.78,0.80,0.82,0.84,0.86,0.88,0.90 | tail -1
BOX="-0.12,0.12,0.70,0.96" SC=4500 PYTHONPATH=$PYL $BP rearplot.py proof/P14_sagittal_rear_profiles_vs_plate_FORM2.png 0.70 1.00 0.00 0.13 $T start | tail -1
# skin look
for X in start $T; do SRC=data/V_$X.npy; [ $X = start ] && SRC=baseline/HeroBase_Male_Silhouette.blend; PYTHONPATH=$PYL $B -b --factory-startup --python rig.py -- $SRC r/skf_$X "yaw180_0.5_0.9_0_700_600_0,yaw150_0.5_0.9_0_700_600_0,yaw210_0.5_0.9_0_700_600_0,yaw90_0.5_0.9_0_700_600_0,yaw0_0.5_0.85_0_700_600_0" skin 0.886,0.627,0.431 2>&1 | grep -E "Error|Traceback"; done
python3 - <<PYEOF
from PIL import Image, ImageDraw, ImageFont
names=['yaw180_0.5_0.9_0_700_600_0','yaw150_0.5_0.9_0_700_600_0','yaw210_0.5_0.9_0_700_600_0','yaw90_0.5_0.9_0_700_600_0','yaw0_0.5_0.85_0_700_600_0']
F=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',20)
S=Image.new('RGB',(700*5,630*2),(16,16,16)); d=ImageDraw.Draw(S)
for r,(t,lab) in enumerate((('start','chat-9 (9bfd788a)'),('$T','FORM2'))):
    for c,n in enumerate(names):
        S.paste(Image.open(f'r/skf_{t}/{n}.png').convert('RGB'),(c*700,r*630+30)); d.text((c*700+6,r*630+4),lab+'  '+['back','3q back L','3q back R','side','front'][c]+' (skin look)',fill=(255,200,80),font=F)
S=S.resize((S.width*2//3,S.height*2//3)); S.save('proof/P12_skin_look_chat9_vs_FORM2.png'); print(S.size)
PYEOF
rm -f proof/P12_skin_look_start_vs_FORM2.png proof/P10_gap_sections_rear_start_blue_FORM2_green.png proof/P10b_gap_sections_front_start_blue_FORM2_green.png
echo PROOFS_DONE
