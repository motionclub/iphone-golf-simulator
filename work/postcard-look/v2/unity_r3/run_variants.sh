#!/bin/bash
# usage: run_variants.sh <label> <outdir (under work/postcard-look/v2/unity_r3)> <cfg> "<variants spec>"
R="$(cd "$(dirname "$0")/../../../.." && pwd)"
bash "$R/work/postcard-look/v2/runtime/run_stills.sh" "$1" "work/postcard-look/v2/unity_r3/$2" GOLF_STILLS_CFG="$R/work/postcard-look/v2/unity_r3/$3" "GOLF_STILLS_VARIANTS=$4"
