#!/bin/zsh
# build prefabs -> tests -> after-fingerprint -> locker assets, one Unity batch after the other (each behind heavy.sh)
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/hero-dressed
cd $W
./scripts/unity_stage.sh build MatchHeroBuild.Run
./scripts/unity_stage.sh tests MatchHeroKitTests.Run
MH_FP_OUT=$W/baseline/prefab_after.json ./scripts/unity_stage.sh fp_after MatchHeroKitBaseline.Run
./scripts/unity_stage.sh locker MatchHeroLockerExport.Run
echo "unity chain done"
