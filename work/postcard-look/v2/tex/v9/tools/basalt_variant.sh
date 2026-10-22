#!/bin/bash
# usage: basalt_variant.sh <name> '<--set list or empty>' : generate Basalt into v9/bv_<name>/, sync C/N/E into the clone, render the 3 hole 10 stills into v9/stills_<name>/, run the BASALT_JOINTS measurement
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; V=$R/work/postcard-look/v2/tex/v9
SC=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/b67a5225-b7e5-4252-b92f-b4ee9f4f2d01/scratchpad
N="$1"; SET="$2"; mkdir -p "$V/bv_$N"
if [ -n "$SET" ]; then bash "$R/work/postcard-look/v2/tools/gen.sh" "$V/bv_$N" Basalt --set "$SET" > "$V/bv_$N/gen.log" 2>&1; else bash "$R/work/postcard-look/v2/tools/gen.sh" "$V/bv_$N" Basalt > "$V/bv_$N/gen.log" 2>&1; fi
for f in Basalt_C Basalt_N Basalt_E; do cp "$V/bv_$N/$f.png" "$SC/UnityClone/Assets/Resources/Course/Look/$f.png"; done
rm -rf "$V/stills_$N"
bash "$V/tools/run_clone_stills.sh" "$N" "$V/stills_$N" "$V/cfg_h10.json"
python3 "$V/tools/basalt_gv.py" "$V/stills_$N" | tee "$V/bv_$N/gv.txt"
