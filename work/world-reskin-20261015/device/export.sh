#!/bin/zsh
set -eu
/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -quit -projectPath '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/world-reskin-20261015/device/root/Unity' -buildTarget iOS -job-worker-count 2 --burst-disable-compilation -executeMethod GolfArcade.EditorTools.BuildMenu.BuildIOS -logFile '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/world-reskin-20261015/device/unity-export.log'
