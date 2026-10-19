#!/bin/zsh
# FINAL bake-first sequence: re-bake every clip x hero x kit, then the gate sweeps with the installed tracks, then films / bake check / tests
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
W=$HOME/hand-clearance-work
cd $R
for ctx in tennis_male tennis_female golf_male golf_female; do
  rm -rf $W/sweep/fbake_$ctx
  UNITY_WHAT="bake-first FINAL bake: $ctx" UNITY_MINUTES=30 SWEEP_TRACKS=bake SWEEP_TRACKS_FRESH=1 SWEEP_TRACK_HZ=30 SWEEP_ROUNDS=2 SWEEP_BAKE_DIAG=0 \
    SWEEP_BEFORE=0 SWEEP_RENDER=0 SWEEP_FREE=1 SWEEP_OUT=$W/sweep/fbake_$ctx SWEEP_CONTEXTS=$ctx SWEEP_HZ=60 \
    work/hand-clearance/tools/unity.sh $W/logs/fbake_$ctx.log -executeMethod GolfArcade.EditorTools.AnimationSafetyAudit.Sweep
  echo "fbake $ctx $(tail -1 $W/logs/fbake_$ctx.log) $(date +%H:%M)" >> $W/logs/final.progress
done
for ctx in tennis_male tennis_female golf_male golf_female; do
  rm -rf $W/sweep/fuse_$ctx
  UNITY_WHAT="bake-first FINAL gate sweep: $ctx" UNITY_MINUTES=20 SWEEP_TRACKS=use SWEEP_BEFORE=1 SWEEP_RENDER=1 SWEEP_WORST=6 SWEEP_FREE=1 \
    SWEEP_OUT=$W/sweep/fuse_$ctx SWEEP_CONTEXTS=$ctx SWEEP_HZ=60 work/hand-clearance/tools/unity.sh $W/logs/fuse_$ctx.log -executeMethod GolfArcade.EditorTools.AnimationSafetyAudit.Sweep
  echo "fuse $ctx $(tail -1 $W/logs/fuse_$ctx.log) $(date +%H:%M)" >> $W/logs/final.progress
done
# then: films + lobby bake check + EditMode tests (see README "Run")
echo "ALL DONE $(date +%H:%M)" >> $W/logs/final.progress
