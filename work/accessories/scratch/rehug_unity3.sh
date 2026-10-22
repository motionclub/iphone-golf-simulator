#!/bin/zsh
# 10-18 round 2: re-sync the clone (male prefab patch: garments draw), re-run the cap clip check + rest/posed proofs with the re-hugged caps
set -e
A=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/accessories; R=${A:h:h}
CL=$HOME/cap-rehug-UnityClone; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
export GOLF_MUTE=1
for d in Assets Packages ProjectSettings; do rsync -a --exclude 'Resources/Accessories/' $R/Unity/$d/ $CL/$d/; done
rm -f $CL/Assets/Tests/EditMode/HeroClearanceTests.cs $CL/Assets/Tests/EditMode/HeroClearanceTests.cs.meta   # did not compile in a clone on 10-18 (clone only)
ACC_CLIP_OUT=$A/clipcheck/rehug_male_1018_garments ACC_CLIP_HEROES=MatchHero_Male,GolfKitHero_Male ACC_CLIP_BAG=0 \
  $U -batchmode -nographics -quit -projectPath $CL -executeMethod GolfArcade.EditorTools.AccessoriesClipCheck.RunBatch -logFile $A/logs/unity_clip_1018.log
echo clip-ok
ACC_PROOF_OUT=$A/proof/rehug_male_1018/rest ACC_PROOF_HEROES=MatchHero_Male,GolfKitHero_Male \
ACC_PROOF_SHOTS="head_front:head:0,head_q34:head:45,head_side:head:90,head_back:head:180,head_q315:head:315,head_left:head:270" \
  $U -batchmode -quit -projectPath $CL -executeMethod GolfArcade.EditorTools.AccessoriesProof.RunBatch -logFile $A/logs/unity_proof_1018.log
for P in Putt@0.3 FistPump@0.4 Emote_Spike@3.1 Emote_Thrust@1.0; do
ACC_PROOF_OUT=$A/proof/rehug_male_1018/poses/${P/@/_} ACC_PROOF_HEROES=GolfKitHero_Male ACC_PROOF_POSE=$P \
ACC_PROOF_SHOTS="head_back:head:180,head_side:head:90,head_left:head:270,bust_q:bust:150" \
  $U -batchmode -quit -projectPath $CL -executeMethod GolfArcade.EditorTools.AccessoriesProof.RunBatch -logFile $A/logs/unity_proof_pose_1018.log
done
echo all-ok
