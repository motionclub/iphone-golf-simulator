#!/bin/bash
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; V=$R/work/postcard-look/v2/tex/v9; cd $R
bash work/postcard-look/v2/runtime/run_smoke.sh t9s3 > $V/real_smoke.out 2>&1
bash work/postcard-look/v2/runtime/run_importcheck.sh t9i1 > $V/real_importcheck.out 2>&1
rm -rf $V/stills_real9
bash work/postcard-look/v2/runtime/run_stills.sh t9r work/postcard-look/v2/tex/v9/stills_real9 GOLF_STILLS_CFG=$V/cfg_9.json > $V/real_stills.out 2>&1
rm -rf $V/stills_real_grass
bash work/postcard-look/v2/runtime/run_stills.sh t9g work/postcard-look/v2/tex/v9/stills_real_grass GOLF_STILLS_CFG=$V/cfg_grass.json > $V/real_stills_grass.out 2>&1
env GOLF_GRASS_CHECK_REPORT=$V/grasscheck_real2.txt work/postcard-look/heavy.sh "T9-real-grasscheck2" /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath $R/Unity -executeMethod GolfArcade.EditorTools.GolfLookGrassCheck.Run -logFile $V/logs/real_grasscheck2.log
echo chain_real done > $V/chain_real.done
