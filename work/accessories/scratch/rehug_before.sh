#!/bin/zsh
# cap re-hug (male, 10-17): dump the current male body (new head) and photograph the caps BEFORE the re-hug, in ~/cap-rehug-UnityClone
set -e
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
export ACC_CLONE=$HOME/cap-rehug-UnityClone GOLF_MUTE=1
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
for d in Assets Packages ProjectSettings; do rsync -a --exclude 'Resources/Accessories/' $R/Unity/$d/ $ACC_CLONE/$d/; done
mkdir -p $R/work/accessories/dump_1017
CV2_OUT=$R/work/accessories/dump_1017 CV2_HEROES=MatchHero_Male CV2_FPS=1 VISUAL_GARMENT_COVERAGE=0 \
  $U -batchmode -nographics -quit -projectPath $ACC_CLONE -executeMethod GolfArcade.EditorTools.ClothingV2Dump.Run -logFile $R/work/accessories/logs/unity_dump_1017.log
grep "\[CV2\]" $R/work/accessories/logs/unity_dump_1017.log | tail -3
ACC_PROOF_SHOTS="head_front:head:0,head_q34:head:45,head_side:head:90,head_back:head:180,head_q315:head:315,head_left:head:270" \
  $R/work/accessories/unity_iter.sh proof $R/work/accessories/proof/rehug_male_1017/before MatchHero_Male,GolfKitHero_Male
