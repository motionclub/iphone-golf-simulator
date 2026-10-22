#!/bin/bash
# usage: variant.sh <name> '<--set list or empty>' [cfg]   : generate Fairway/Green into v9/var_<name>/, sync into the clone, render stills into v9/stills_<name>/ (clone, through heavy.sh)
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; V=$R/work/postcard-look/v2/tex/v9
N="$1"; SET="$2"; CFG="${3:-$V/cfg_grass.json}"
mkdir -p "$V/var_$N"
if [ -n "$SET" ]; then bash "$R/work/postcard-look/v2/tools/gen.sh" "$V/var_$N" Fairway,Green --set "$SET" > "$V/var_$N/gen.log" 2>&1; else bash "$R/work/postcard-look/v2/tools/gen.sh" "$V/var_$N" Fairway,Green > "$V/var_$N/gen.log" 2>&1; fi
bash "$V/tools/sync_to_clone.sh" "$V/var_$N"
rm -rf "$V/stills_$N"
bash "$V/tools/run_clone_stills.sh" "$N" "$V/stills_$N" "$CFG"
