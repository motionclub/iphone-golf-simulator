#!/bin/zsh
set -e
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup export/HeroBase_Male_MatchAnims.blend --python scripts/bake_loco.py -- male Serve=serve_r4 > r4/bake_male.log 2>&1
$B -b --factory-startup export/HeroBase_Male_MatchAnims.blend --python scripts/export_fbx_r4.py -- male Serve > r4/export_male.log 2>&1
cp r4/fbx/Male_Serve.fbx UnityClone/Assets/Characters/MatchHeroes/Male/Male_Serve.fbx
cp r3/final_candidate/fbx/Male_Serve.fbx.meta UnityClone/Assets/Characters/MatchHeroes/Male/Male_Serve.fbx.meta
cp r3/final_candidate/fbx/Female_Serve.fbx UnityClone/Assets/Characters/MatchHeroes/Female/Female_Serve.fbx
cp r3/final_candidate/fbx/Female_Serve.fbx.meta UnityClone/Assets/Characters/MatchHeroes/Female/Female_Serve.fbx.meta
SJ_OUT=$PWD/r4/trial1/male SJ_FEMALE=0 SJ_CAPTURE=1 SJ_KEY_ONLY=1 SJ_ENTRY_DELAY=0 SJ_TAIL=30 /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath $PWD/UnityClone -executeMethod GolfArcade.EditorTools.ServeJumpProof.Run -logFile $PWD/r4/trial1_male.log
