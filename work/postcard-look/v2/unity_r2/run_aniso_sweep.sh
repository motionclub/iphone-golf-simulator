#!/bin/bash
# aniso sweep: the nine proof shots under GOLF_LOOK_ANISO=4 / 8 / 16 (editor-only env override in GolfLook), Game view = PostcardLookStills
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; V=work/postcard-look/v2
for a in 4 8 16; do
  bash $R/$V/runtime/run_stills.sh r2_aniso$a $V/unity_r2/stills_a$a GOLF_STILLS_CFG=$R/$V/proof/stills_cfg_9.json GOLF_LOOK_ANISO=$a > $R/$V/unity_r2/sweep_a$a.out 2>&1
  cat $R/$V/unity_r2/sweep_a$a.out | tail -1
done
echo SWEEP_DONE
