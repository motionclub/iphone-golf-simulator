#!/bin/bash
# final Game-view stills of this repair round: default code (no GOLF_LOOK_ANISO), TennisURP (active) then HeroBaseStudioURP in memory
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; V=work/postcard-look/v2
bash $R/$V/runtime/run_stills.sh r2_final $V/unity_r2/stills_final GOLF_STILLS_CFG=$R/$V/proof/stills_cfg_9.json > $R/$V/unity_r2/final_stills.out 2>&1; tail -1 $R/$V/unity_r2/final_stills.out
bash $R/$V/runtime/run_stills.sh r2_final_studio $V/unity_r2/stills_final_studio GOLF_STILLS_CFG=$R/$V/proof/stills_cfg_9.json GOLF_STILLS_PIPELINE=HeroBaseStudioURP > $R/$V/unity_r2/final_stills_studio.out 2>&1; tail -1 $R/$V/unity_r2/final_stills_studio.out
echo FINAL_STILLS_DONE
