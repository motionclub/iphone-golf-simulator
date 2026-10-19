#!/bin/zsh
# Film one AutoPlay match in the chat-4 Unity clone. usage: run_film.sh <out-dir> <male|female> <seconds> [video 1|0]
set -e
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
CLONE=${TAI_CLONE:-/Users/adnanyonathan/tai-films/UnityClone}
mkdir -p $CLONE/Assets/Editor/TAI $CLONE/Assets/Scripts/TAI
cp $REPO/work/tennis-anim-integrity/unity/Editor/*.cs $CLONE/Assets/Editor/TAI/
cp $REPO/work/tennis-anim-integrity/unity/Runtime/*.cs $CLONE/Assets/Scripts/TAI/
OUT=$1; mkdir -p $OUT
GOLF_MUTE=1 TAI_OUT=$OUT TAI_SEX=$2 TAI_SECONDS=$3 TAI_VIDEO=${4:-1} TAI_FFMPEG=${TAI_FFMPEG:-/Users/adnanyonathan/tai-films/ffmpeg} \
  /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath $CLONE \
  -executeMethod GolfArcade.EditorTools.TennisAnimIntegrityFilm.Run -logFile $OUT/unity.log -screen-width 1280 -screen-height 720
