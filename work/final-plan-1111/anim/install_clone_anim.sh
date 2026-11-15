#!/bin/bash
# install_clone_anim.sh [clone]: the arm limits in a PROJECT COPY only (never the shared Unity/): syncs the copy from the shared
# project, adds HeroArmLimits.cs and the probe, and hooks the limits onto the end of HeroPoseSafety.Apply.
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$REPO/work/final-plan-1111
C=$HOME/unity-clones/${1:-final-plan-dev}/Unity
CLONE=${1:-final-plan-dev} $W/sync.sh
for d in Assets/Resources/HeroStudio; do rsync -a "$REPO/Unity/$d/" "$C/$d/"; done
cp $W/anim/HeroArmLimits.cs.txt $C/Assets/Scripts/Tennis/HeroArmLimits.cs
cp $W/anim/ZArmProbe.cs.txt $C/Assets/Scripts/Tennis/ZArmProbe.cs
python3 $W/anim/patch_posesafety.py "$C/Assets/Scripts/Tennis/HeroPoseSafety.cs"
python3 $W/anim/patch_export.py "$C/Assets/Editor/MatchHeroLockerExport.cs"
