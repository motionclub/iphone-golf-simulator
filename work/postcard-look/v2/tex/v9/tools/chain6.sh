#!/bin/bash
V=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/tex/v9
for spec in "g1|BASALT_P.net_trunk=0.10/0.22,BASALT_P.net_bulb=0.062" "g2|BASALT_P.net_trunk=0.10/0.22,BASALT_P.net_bulb=0.062,BASALT_P.vor_keep=0.65" "g3|BASALT_P.net_trunk=0.10/0.22,BASALT_P.net_bulb=0.062,BASALT_P.net_th=45/75"; do
  n="${spec%%|*}"; s="${spec#*|}"
  bash $V/tools/basalt_variant.sh $n "$s" 2>&1 | tail -4
done
echo chain6 done
