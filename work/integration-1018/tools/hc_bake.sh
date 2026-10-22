#!/bin/zsh
# Hand clearance on the COMBINED clone (chat 12): re-bake the tennis tracks (chat 4's strokes changed), then the gate sweep on all four
# contexts with the installed tracks. Same settings as work/hand-clearance/tools/full_bake.sh; outputs in ~/integration-work/hc, not chat 3's.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
W=$HOME/integration-work/hc; mkdir -p $W/sweep $W/logs
export CLONE=$HOME/integration-work/Unity1
cd $R
for ctx in ${=BAKE_CONTEXTS:-tennis_male tennis_female}; do
  rm -rf $W/sweep/fbake_$ctx
  UNITY_WHAT="chat 12: clearance re-bake $ctx (combined clone)" UNITY_MINUTES=30 SWEEP_TRACKS=bake SWEEP_TRACKS_FRESH=1 SWEEP_TRACK_HZ=30 SWEEP_ROUNDS=2 SWEEP_BAKE_DIAG=0 \
    SWEEP_BEFORE=0 SWEEP_RENDER=0 SWEEP_FREE=1 SWEEP_OUT=$W/sweep/fbake_$ctx SWEEP_CONTEXTS=$ctx SWEEP_HZ=60 \
    work/hand-clearance/tools/unity.sh $W/logs/fbake_$ctx.log -executeMethod GolfArcade.EditorTools.AnimationSafetyAudit.Sweep
  echo "fbake $ctx $(tail -1 $W/logs/fbake_$ctx.log) $(date +%H:%M)" >> $W/logs/progress
done
for ctx in ${=SWEEP_CONTEXTS_ALL:-tennis_male tennis_female golf_male golf_female}; do
  rm -rf $W/sweep/fuse_$ctx
  UNITY_WHAT="chat 12: clearance gate sweep $ctx (combined clone)" UNITY_MINUTES=20 SWEEP_TRACKS=use SWEEP_BEFORE=1 SWEEP_RENDER=1 SWEEP_WORST=6 SWEEP_FREE=1 \
    SWEEP_OUT=$W/sweep/fuse_$ctx SWEEP_CONTEXTS=$ctx SWEEP_HZ=60 work/hand-clearance/tools/unity.sh $W/logs/fuse_$ctx.log -executeMethod GolfArcade.EditorTools.AnimationSafetyAudit.Sweep
  echo "fuse $ctx $(tail -1 $W/logs/fuse_$ctx.log) $(date +%H:%M)" >> $W/logs/progress
done
echo "ALL DONE $(date +%H:%M)" >> $W/logs/progress
