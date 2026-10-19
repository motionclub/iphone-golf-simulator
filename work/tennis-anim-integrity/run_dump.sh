#!/bin/zsh
# Sample every tennis clip of both heroes in the chat-4 clone. usage: run_dump.sh <out-dir>
set -e
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
CLONE=${TAI_CLONE:-/Users/adnanyonathan/tai-films/UnityClone}
mkdir -p $CLONE/Assets/Editor/TAI; cp $REPO/work/tennis-anim-integrity/unity/Editor*/*.cs $CLONE/Assets/Editor/TAI/
mkdir -p $1
GOLF_MUTE=1 TAI_DUMP_OUT=$1 /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath $CLONE \
  -executeMethod GolfArcade.EditorTools.TennisAnimClipDump.Run -logFile $1/unity.log
