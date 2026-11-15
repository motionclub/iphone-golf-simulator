#!/bin/bash
# install_game_anim.sh: the wrist and elbow limits into the SHARED game project (Unity/). Backups first (keep.sh -> install_backup/), then
# the guarded rollback's manifest is brought up to date, so ROLLBACK.sh takes this out again without touching other chats' edits.
#   new  Unity/Assets/Scripts/Tennis/HeroArmLimits.cs (+ .meta from the project copy)
#   hook Unity/Assets/Scripts/Tennis/HeroPoseSafety.cs  (ArmLimits() at the end of Apply)
#   hook Unity/Assets/Editor/MatchHeroLockerExport.cs   (the menu export applies the same rule to every clip frame)
# Switch: ARM_LIMITS=0 (all of it off, game and export).
set -e
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$REPO/work/final-plan-1111; P=$W/install_patches
cd $REPO
T=Unity/Assets/Scripts/Tennis; E=Unity/Assets/Editor
$W/keep.sh $T/HeroArmLimits.cs $T/HeroPoseSafety.cs $E/MatchHeroLockerExport.cs
cp $W/anim/HeroArmLimits.cs.txt $T/HeroArmLimits.cs
[ -f $T/HeroArmLimits.cs.meta ] || cp $HOME/unity-clones/final-plan-dev/Unity/Assets/Scripts/Tennis/HeroArmLimits.cs.meta $T/HeroArmLimits.cs.meta
python3 $W/anim/patch_posesafety.py $T/HeroPoseSafety.cs
python3 $W/anim/patch_export.py $E/MatchHeroLockerExport.cs
for f in $T/HeroPoseSafety.cs $E/MatchHeroLockerExport.cs; do
  grep -vF "  $f" $P/MANIFEST.sha256 > $P/MANIFEST.tmp || true; mv $P/MANIFEST.tmp $P/MANIFEST.sha256
  echo "$(shasum -a 256 $f | cut -d' ' -f1)  $f" >> $P/MANIFEST.sha256
done
for f in $T/HeroArmLimits.cs $T/HeroPoseSafety.cs; do grep -qxF "$f" work/hero-sync/look_sources.txt || echo "$f" >> work/hero-sync/look_sources.txt; done
f=work/hero-sync/look_sources.txt; grep -vF "  $f" $P/MANIFEST.sha256 > $P/MANIFEST.tmp || true; mv $P/MANIFEST.tmp $P/MANIFEST.sha256; echo "$(shasum -a 256 $f | cut -d" " -f1)  $f" >> $P/MANIFEST.sha256
echo "INSTALLED $(date '+%Y-%m-%d %H:%M')"
