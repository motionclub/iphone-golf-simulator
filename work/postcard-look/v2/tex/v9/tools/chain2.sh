#!/bin/bash
V=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/tex/v9
bash $V/tools/sync_to_clone.sh $V/var_id
rm -rf $V/stills_id; bash $V/tools/run_clone_stills.sh id $V/stills_id $V/cfg_grass.json
bash $V/tools/variant.sh D 'BAND_P.sheen_l=0.20,BAND_P.sheen_d=0.04,BAND_P.sheen_streak=0.03'
echo chain2 done
