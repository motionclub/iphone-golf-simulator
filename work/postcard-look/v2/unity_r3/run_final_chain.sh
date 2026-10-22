#!/bin/bash
# the round-3 verification chain (each step through heavy.sh): smoke suite, golfer probes, 9 stills, masks. usage: run_final_chain.sh <tag>
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; T="$1"; U3=work/postcard-look/v2/unity_r3; cd "$R"
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
bash work/postcard-look/v2/runtime/run_smoke.sh "r3$T" > $U3/chain_smoke_$T.out 2>&1
bash $U3/run_probe_r3.sh "$T" > $U3/chain_probe_$T.out 2>&1
mkdir -p $U3/stills9_$T $U3/proofcopy_$T/masks/9
bash work/postcard-look/v2/runtime/run_stills.sh "r3$T" $U3/stills9_$T GOLF_STILLS_CFG=$R/work/postcard-look/v2/proof/stills_cfg_9.json > $U3/chain_stills_$T.out 2>&1
GOLF_PROOF_CFG=$R/work/postcard-look/v2/proof/stills_cfg_9.json GOLF_PROOF_OUT=$R/$U3/proofcopy_$T/masks/9 work/postcard-look/heavy.sh "R3-masks-$T" "$U" -batchmode -projectPath "$R/Unity" -executeMethod GolfArcade.EditorTools.PostcardProofMasks.Run -logFile "$R/$U3/chain_masks_$T.unity.log" > $U3/chain_masks_$T.out 2>&1
echo done > $U3/chain_$T.done
