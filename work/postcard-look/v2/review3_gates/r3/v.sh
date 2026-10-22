#!/bin/bash
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; cd $R
S=work/postcard-look/v2/review3_gates/r3
while read a b; do cmp ArtDir/screenshots/golf_postcards/look/$a.png work/postcard-look/v2/proof/gate_stills/$b.png && echo same $a; done <<L
hole08_1_tee hole08_tee
hole08_2_approach hole08_approach
hole08_3_arch hole08_arch
hole09_1_tee hole09_tee
hole09_2_approach hole09_approach
hole09_3_ruin hole09_ruin
hole10_1_tee hole10_tee
hole10_2_approach hole10_approach
hole10_3_lavarim hole10_lavarim
L
B=/Applications/Blender.app/Contents/MacOS/Blender
for h in 8 9 10; do $B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- $h --stills-dir $R/work/postcard-look/v2/proof/gate_stills --require-stills > $S/verify_hole$h.log 2>&1 & done; wait
for h in 8 9 10; do echo == $h; grep -c PASS $S/verify_hole$h.log; grep -E "FAIL|RESULT" $S/verify_hole$h.log | head; done
