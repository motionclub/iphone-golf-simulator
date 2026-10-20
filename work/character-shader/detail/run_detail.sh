#!/bin/bash
# HERO_DETAIL stills in a headless-graphics Unity batch run.   work/character-shader/detail/run_detail.sh before|after [log-name]
cd "$(dirname "$0")/../../.." || exit 1
ROOT=$PWD; SET=${1:-after}; LOG=${2:-$SET}
rm -f Unity/Temp/UnityLockfile
HDS_OUT=$ROOT/work/character-shader/proof/detail/$SET /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath "$ROOT/Unity" \
  -executeMethod GolfArcade.EditorTools.HeroDetailStill.Run -logFile "$ROOT/work/character-shader/detail/logs/$LOG.log"
echo "unity exit $?"; grep -c "error CS" "$ROOT/work/character-shader/detail/logs/$LOG.log"
