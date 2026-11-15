#!/bin/bash
# Puts the game scripts back to how they were before the 2026-11-11 hero build + presence install.
# The eight modified files are restored from install_backup; the three new files are moved out of the project (not deleted).
set -u
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator || exit 1
W=work/hero-build-1111
MOD=(Assets/Scripts/Tennis/HeroShoeShape.cs Assets/Scripts/Tennis/MatchHeroLook.cs Assets/Scripts/Tennis/HeroTennisDriver.cs Assets/Scripts/Tennis/HeroLightingProfile.cs Assets/Scripts/Tennis/HeroGarmentLOD.cs Assets/Scripts/Tennis/TennisGame.cs Assets/Scripts/Tennis/TennisGame.Versus.cs Assets/Scripts/Hub/Menu/MenuBackdrop.cs)
NEW=(Assets/Scripts/Tennis/HeroBuild.cs Assets/Scripts/Tennis/HeroForearmTwist.cs Assets/Scripts/Hub/Menu/MenuHeroGaze.cs)
for f in "${MOD[@]}"; do cp -p "$W/install_backup/$f" "Unity/$f"; done
mkdir -p "$W/install_backup/moved_out"
for f in "${NEW[@]}"; do
  [ -e "Unity/$f" ] && mv "Unity/$f" "$W/install_backup/moved_out/"
  [ -e "Unity/$f.meta" ] && mv "Unity/$f.meta" "$W/install_backup/moved_out/"
done
echo "rolled back: ${#MOD[@]} files restored, ${#NEW[@]} new files moved to $W/install_backup/moved_out"
