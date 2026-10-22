#!/bin/bash
# fresh snapshot of the repo at HEAD -> Unity iOS export -> xcodegen -> Release build (no install; install.sh does that)
set -e
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
W="$R/work/phone-build-1013"
rm -rf "$W/root" "$W/DerivedData"
mkdir -p "$W/root"
cd "$R"
cp -c -R Unity "$W/root/Unity"
rm -rf "$W/root/Unity/Builds" "$W/root/Unity/Temp" "$W/root/Unity/Logs" "$W/root/Unity/work"
cp -c -R GolfArcade GolfArcadeTests GolfArcadeUITests project.yml project-unity.yml "$W/root/"
echo "snapshot done $(date)"
bash "$W/export.sh" > "$W/export-run.log" 2>&1
tail -2 "$W/export-run.log"
grep -q "^Succeeded" "$W/export-run.log" || { echo "EXPORT FAILED"; exit 1; }
bash "$W/xcode.sh" > "$W/xcode-run.log" 2>&1
cat "$W/xcode-run.log"
echo "ALL DONE $(date)"
