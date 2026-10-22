#!/bin/bash
# v7 Game-view re-measure (own copy: stills into v7/stills9, extras into v7/proofcopy/extra, masks into v7/proofcopy/masks; NEVER ArtDir/screenshots/golf_postcards/look/).
# usage: run_v7_proof.sh <tag>      (Unity only through heavy.sh)
R="$(cd "$(dirname "$0")/../../../../../.." && pwd)"; cd "$R" || exit 2
TAG="${1:-v7}"; V=work/postcard-look/v2; T=$V/tex/v7; P=$V/proof
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
mkdir -p $T/stills9 $T/proofcopy/extra $T/proofcopy/masks/9 $T/proofcopy/masks/extra $T/logs
echo "[$(date +%H:%M:%S)] stills 9"; bash $V/runtime/run_stills.sh s9_$TAG $T/stills9 GOLF_STILLS_CFG=$R/$P/stills_cfg_9.json > $T/logs/stills_9_$TAG.log 2>&1; tail -1 $T/logs/stills_9_$TAG.log
echo "[$(date +%H:%M:%S)] stills extra"; bash $V/runtime/run_stills.sh sx_$TAG $T/proofcopy/extra GOLF_STILLS_CFG=$R/$P/stills_cfg_extra.json > $T/logs/stills_x_$TAG.log 2>&1; tail -1 $T/logs/stills_x_$TAG.log
for k in 9 extra; do
  echo "[$(date +%H:%M:%S)] masks $k"
  GOLF_PROOF_CFG=$R/$P/stills_cfg_$k.json GOLF_PROOF_OUT=$R/$T/proofcopy/masks/$k work/postcard-look/heavy.sh "T-masks-$k-$TAG" "$U" -batchmode -projectPath "$R/Unity" -executeMethod GolfArcade.EditorTools.PostcardProofMasks.Run -logFile "$R/$T/logs/masks_${k}_$TAG.unity.log" > $T/logs/masks_${k}_$TAG.log 2>&1
  echo "masks $k exit $?; compile errors: $(grep -c 'error CS' $T/logs/masks_${k}_$TAG.unity.log)"
done
echo "[$(date +%H:%M:%S)] measure"; python3 $T/tools/measure_v7.py > $T/logs/measure_$TAG.log 2>&1; tail -3 $T/logs/measure_$TAG.log
echo "[$(date +%H:%M:%S)] done"
