#!/bin/bash
# usage: cmpall.sh <tag> [--enh]  -> renders the candidate in all comparison setups and writes tmp/cmp_<tag>_*.png (plate | start | tag)
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2
T=$1
python3 crop_cmp.py render $T manneq
python3 panel_cmp.py render $T manneq
LABELS="PLATE,START,$T" python3 crop_cmp.py sheet tmp/cmp_${T}_back.png back 0.68 1.06 0.20 start $T
LABELS="PLATE,START,$T" python3 crop_cmp.py sheet tmp/cmp_${T}_back_enh.png back 0.68 1.06 0.20 start $T --enh
LABELS="PLATE,START,$T" python3 panel_cmp.py sheet tmp/cmp_${T}_q.png q_bl,q_br start $T
LABELS="PLATE,START,$T" python3 panel_cmp.py sheet tmp/cmp_${T}_q_enh.png q_bl,q_br start $T --enh
LABELS="PLATE,START,$T" python3 panel_cmp.py sheet tmp/cmp_${T}_side.png left,right start $T
LABELS="PLATE,START,$T" python3 panel_cmp.py sheet tmp/cmp_${T}_front.png q_fl,q_fr,front start $T
LABELS="PLATE,START,$T" python3 panel_cmp.py sheet tmp/cmp_${T}_front_enh.png q_fl,q_fr,front start $T --enh
