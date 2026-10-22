#!/bin/bash
# Unity import check of the kit FBXs in a SCRATCH project outside the repo (never touches the game project).
# usage: scripts/unity_check.sh <scratch_project_dir>
#   scratch project = any empty Unity 6000.3 project with Assets/Kit/ and Assets/Editor/KitImportCheck.cs (copy of scripts/KitImportCheck.cs.txt)
# result: proof/unity_import_report.json  (STDKIT_WORN_UNITY_IMPORT PASS|FAIL)
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-worn
P=${1:?scratch project dir}
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
mkdir -p "$P/Assets/Kit" "$P/Assets/Editor"
rm -f "$P"/Assets/Kit/*.fbx "$P"/Assets/Kit/*.fbx.meta
cp "$W"/export/StdKit_*.fbx "$P/Assets/Kit/"
cp "$W/scripts/KitImportCheck.cs.txt" "$P/Assets/Editor/KitImportCheck.cs"
python3 "$P/make_expected.py" "$P/expected_bounds.json"
rm -f "$P/unity_import_report.json"
"$UNITY" -batchmode -nographics -projectPath "$P" -executeMethod KitImportCheck.Run -logFile "$P/unity.log" > "$P/unity_stdout.txt" 2>&1 || true
grep -E "STDKIT_WORN_UNITY_IMPORT" "$P/unity.log" | tail -1
cp "$P/unity_import_report.json" "$W/proof/unity_import_report.json"
