#!/bin/zsh
# cap re-hug (male, 10-17) in ~/cap-rehug-UnityClone: clip check with the OLD caps, install the re-hugged caps, clip check again, after proof
set -e
A=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/accessories
export ACC_CLONE=$HOME/cap-rehug-UnityClone GOLF_MUTE=1 ACC_CLIP_HEROES=MatchHero_Male,GolfKitHero_Male ACC_CLIP_BAG=0
ACC_CLIP_OUT=$A/clipcheck/rehug_male_1017_before $A/unity_iter.sh run GolfArcade.EditorTools.AccessoriesClipCheck.RunBatch
cp $A/logs/unity_run.log $A/logs/unity_clip_before_1017.log
$A/unity_iter.sh install
ACC_CLIP_OUT=$A/clipcheck/rehug_male_1017_after $A/unity_iter.sh run GolfArcade.EditorTools.AccessoriesClipCheck.RunBatch
ACC_PROOF_SHOTS="head_front:head:0,head_q34:head:45,head_side:head:90,head_back:head:180,head_q315:head:315,head_left:head:270" \
  $A/unity_iter.sh proof $A/proof/rehug_male_1017/after MatchHero_Male,GolfKitHero_Male
echo all-ok
