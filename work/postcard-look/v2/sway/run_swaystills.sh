#!/bin/bash
# usage: run_swaystills.sh <label> <cfg.json> [extra env assignments...]
# The Game-view frame pairs of the plant sway: PostcardLookStills with a FIXED wind and a FROZEN clock (GOLF_STILLS_SWAY=mph,deg,seconds) and GOLF_STILLS_SWAY_PAIR=<dt>.
# Output (never ArtDir): v2/sway/stills_<label>/<shot>.png, <shot>__sway_t1.png, <shot>__sway_diff.png, stills_stats.json (a "sway" block per shot).
# defaults: 12 mph toward 45 degrees, clock 5.0 s, pair 1.2 s.  Override with GOLF_STILLS_SWAY=... / GOLF_STILLS_SWAY_PAIR=... in the extra env.
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; L="$1"; CFG="$2"; shift; shift
O=work/postcard-look/v2/sway/stills_$L
mkdir -p "$R/$O"
SW="${GOLF_STILLS_SWAY:-12,45,5.0}"; PR="${GOLF_STILLS_SWAY_PAIR:-1.2}"
"$R/work/postcard-look/v2/runtime/run_stills.sh" "sway_$L" "$O" GOLF_STILLS_CFG="$CFG" GOLF_STILLS_SWAY="$SW" GOLF_STILLS_SWAY_PAIR="$PR" "$@"
