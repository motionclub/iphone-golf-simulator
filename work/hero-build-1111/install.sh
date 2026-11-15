#!/bin/bash
# Installs the verified hero build + presence changes from the clone into Unity/ (no commit). Refuses if a target changed since the clone was made.
set -u
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator || exit 1
C=$HOME/unity-clones/hero-build; W=work/hero-build-1111
MOD=(Assets/Scripts/Tennis/HeroShoeShape.cs Assets/Scripts/Tennis/MatchHeroLook.cs Assets/Scripts/Tennis/HeroTennisDriver.cs Assets/Scripts/Tennis/HeroLightingProfile.cs Assets/Scripts/Tennis/HeroGarmentLOD.cs Assets/Scripts/Tennis/TennisGame.cs Assets/Scripts/Tennis/TennisGame.Versus.cs Assets/Scripts/Hub/Menu/MenuBackdrop.cs)
NEW=(Assets/Scripts/Tennis/HeroBuild.cs Assets/Scripts/Tennis/HeroForearmTwist.cs Assets/Scripts/Hub/Menu/MenuHeroGaze.cs)
CT=$(stat -f %B "$C"); echo "clone created $(date -r "$CT" +%H:%M:%S)"; bad=0
for f in "${MOD[@]}"; do m=$(stat -f %m "Unity/$f"); if [ "$m" -gt "$CT" ]; then echo "CHANGED SINCE CLONE: $f"; bad=1; fi; done
for f in "${NEW[@]}"; do [ -e "Unity/$f" ] && { echo "ALREADY EXISTS: $f"; bad=1; }; [ -f "$C/$f.meta" ] || { echo "no meta in clone: $f"; bad=1; }; done
[ $bad = 0 ] || { echo "not installed"; exit 1; }
for f in "${MOD[@]}"; do mkdir -p "$W/install_backup/$(dirname "$f")"; cp -p "Unity/$f" "$W/install_backup/$f"; done
: > "$W/tools/installed_changes.patch"
for f in "${MOD[@]}"; do diff -u "Unity/$f" "$C/$f" | sed "s#^--- Unity/#--- a/#; s#^+++ $C/#+++ b/#" >> "$W/tools/installed_changes.patch"; done
for f in "${MOD[@]}"; do cp "$C/$f" "Unity/$f"; done
for f in "${NEW[@]}"; do cp "$C/$f" "Unity/$f"; cp "$C/$f.meta" "Unity/$f.meta"; cp "$C/$f" "$W/tools/$(basename "$f")"; done
echo "installed ${#MOD[@]} modified + ${#NEW[@]} new files"; wc -l "$W/tools/installed_changes.patch"
