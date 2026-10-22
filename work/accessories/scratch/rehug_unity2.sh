#!/bin/zsh
# after proof + region probe in ~/cap-rehug-UnityClone (no re-sync: another chat's HeroClearanceTests.cs does not compile; removed in the clone only)
set -e
A=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/accessories
CL=$HOME/cap-rehug-UnityClone; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
export GOLF_MUTE=1
ACC_PROOF_OUT=$A/proof/rehug_male_1017/after ACC_PROOF_HEROES=MatchHero_Male,GolfKitHero_Male \
ACC_PROOF_SHOTS="head_front:head:0,head_q34:head:45,head_side:head:90,head_back:head:180,head_q315:head:315,head_left:head:270" \
  $U -batchmode -quit -projectPath $CL -executeMethod GolfArcade.EditorTools.AccessoriesProof.RunBatch -logFile $A/logs/unity_proof_after_1017.log
echo proof-ok
CAPPROBE_OUT=$A/clipcheck/rehug_male_1017_after CAPPROBE_FILTER='Emote|Intro|Celebrate|MatchWin|HitPerfect|MissWhiff|Run|Idle|Drive|HalfSwing|IronSwing' \
  $U -batchmode -nographics -quit -projectPath $CL -executeMethod GolfArcade.EditorTools.CapRegionProbe.RunBatch -logFile $A/logs/unity_probe_after_1017.log
echo probe-ok
for P in Putt@0.3 FistPump@0.4 Emote_Spike@3.1 Emote_Thrust@1.0; do
ACC_PROOF_OUT=$A/proof/rehug_male_1017/after_poses/${P/@/_} ACC_PROOF_HEROES=GolfKitHero_Male ACC_PROOF_POSE=$P \
ACC_PROOF_SHOTS="head_back:head:180,head_side:head:90,head_left:head:270,bust_q:bust:150" \
  $U -batchmode -quit -projectPath $CL -executeMethod GolfArcade.EditorTools.AccessoriesProof.RunBatch -logFile $A/logs/unity_proof_pose_1017.log
done
echo poses-ok
