#!/bin/bash
V=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/tex/v9
B="BASALT_P.net_trunk=0.10/0.22,BASALT_P.net_bulb=0.062,BASALT_P.net_th=45/75"
for spec in "h1|$B,BASALT_P.vor_n=15,BASALT_P.vor_w=0.026" "h2|$B,BASALT_P.vor_n=14,BASALT_P.vor_keep=0.62"; do
  n="${spec%%|*}"; s="${spec#*|}"
  bash $V/tools/basalt_variant.sh $n "$s" 2>&1 | tail -4
  grep "glow texels" $V/bv_$n/gen.log | head -1 | sed 's/.*glow texels/glow texels/' | cut -c1-50
done
echo chain7 done
