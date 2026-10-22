#!/bin/bash
# Calibration round 2 (after review K): the FINAL runs on the main project, one after another (each acquires heavy.sh's lock itself).
#   r2i r2j : GolfLookProbe on the ground library's smoke FBXs (hole 8 must be textured every time: PROBE_SWAP_TOOK_EFFECT), active asset
#   r2tennis: the same under TennisURP (GOLF_LOOK_PROBE_PIPELINE=tennis, in memory)
#   r2raceF : the pre-review waiting (GOLF_LOOK_PROBE_RACE=1);  r2staleF: the baseline model injected (GOLF_LOOK_PROBE_SELFTEST=stale): the swap gate must FAIL
#   GolfLookSmoke, PostcardImportCheck, PostcardLookStills on the test board.
# usage: run_r2_final.sh   -> v2/calibrate/r2/final3_*.out, final3_done.flag
R="$(cd "$(dirname "$0")/../../../../.." && pwd)"; cd "$R"
O=work/postcard-look/v2/calibrate/r2; mkdir -p "$O"
T=work/postcard-look/v2/calibrate/tools/run_probe.sh
for l in r2i r2j; do $T $l > "$O/final3_probe_$l.out" 2>&1; done
GOLF_LOOK_PROBE_PIPELINE=tennis $T r2tennis > "$O/final3_probe_r2tennis.out" 2>&1
GOLF_LOOK_PROBE_RACE=1 $T r2raceF > "$O/final3_probe_r2raceF.out" 2>&1
GOLF_LOOK_PROBE_SELFTEST=stale $T r2staleF > "$O/final3_probe_r2staleF.out" 2>&1
work/postcard-look/v2/runtime/run_smoke.sh r2final3 > "$O/final3_smoke.out" 2>&1
work/postcard-look/v2/runtime/run_importcheck.sh r2final3 > "$O/final3_importcheck.out" 2>&1
work/postcard-look/v2/runtime/run_stills.sh r2final3 work/postcard-look/v2/calibrate/stills_board_r2c GOLF_STILLS_BOARD=1 > "$O/final3_stills.out" 2>&1
echo "all done $(date)" > "$O/final3_done.flag"
