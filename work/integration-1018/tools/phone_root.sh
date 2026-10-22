#!/bin/zsh
# Chat 12: make the phone-build snapshot root from the repo AFTER the real install (the coordinator's work/phone-build-20261018 recipe):
#   phone_root.sh <new empty dir>     e.g. work/phone-build-final/root   (refuses an existing dir; nothing is deleted)
# APFS clones of Unity, the app, tests, the Control Center extension and both project specs, plus the blender/ link
# that GolferModelImporter needs (../../blender/tennis-clips.json) so the standard tennis rig keeps its clips. Then: export.sh / xcode.sh with
# APP_BUNDLE_ID=com.aloniewski.GolfArcade (project.yml's APP_BUNDLE_ID drives the app AND the .controls extension id).
set -e
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; D=${1:?new root dir}
[ -e "$D" ] && { echo "$D exists: pick a new folder"; exit 1; }
mkdir -p "$D"
cp -c -R $R/Unity "$D/Unity"   # APFS clone (11 GB Library in seconds); the export rewrites Builds/iOS
for x in GolfArcade GolfArcadeTests GolfArcadeUITests MotionClubControls; do cp -c -R $R/$x "$D/$x"; done
cp $R/project.yml $R/project-unity.yml "$D/"
ln -s $R/blender "$D/blender"
c=$(grep -c "name: " "$D/Unity/Assets/Resources/StandardCharacters/standard_male_tennis.fbx.meta"); echo "standard tennis meta clip names: $c (must be > 50)"
echo "root ready: $D"
