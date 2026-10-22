#!/bin/bash
V=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/tex/v9
bash $V/tools/variant.sh ctrl 'BAND_P.sheen_l=0.10,BAND_P.sheen_d=0.10,BAND_P.sheen_mott=0,BAND_P.sheen_streak=0'
bash $V/tools/variant.sh A ''
bash $V/tools/variant.sh B 'BAND_P.sheen_l=0.22,BAND_P.sheen_d=0.04'
bash $V/tools/variant.sh C 'BAND_P.lean_deg=0,BAND_P.lean_streak_deg=0'
echo chain1 done
