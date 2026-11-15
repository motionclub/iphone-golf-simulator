#!/bin/bash
# Undo the 11-14 polo underarm install (UA_F): restore his polo mesh, prefab, correctives and offsets as they were before.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; B=$R/work/polo-tear-1113/rollback_F
cp -p $B/Kit_Top.asset $R/Unity/Assets/Characters/KitsV2/MatchHero_Male/Kit_Top.asset
cp -p $B/PlayerMale.prefab $R/Unity/Assets/Resources/Tennis/Customization/PlayerMale.prefab
cp -p $B/KitV2_Tennis_Male_Top_correctives.json $B/KitV2_Tennis_Male_offsets.json $R/Unity/Assets/Resources/Tennis/KitsV2/Male/
echo restored
