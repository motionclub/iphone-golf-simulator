#!/bin/bash
# Renders the character / cloth shader stills (and the rim on/off pairs) in a headless-graphics Unity batch run, then waits for it to exit.
#   work/character-shader/run_stills.sh [log-name]
cd "$(dirname "$0")/../.." || exit 1
ROOT=$PWD; LOG=${1:-still}
rm -f Unity/Temp/UnityLockfile
CSS_OUT=$ROOT/work/character-shader/proof /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath "$ROOT/Unity" \
  -executeMethod GolfArcade.EditorTools.CharacterShaderStill.Run -logFile "$ROOT/work/character-shader/logs/$LOG.log"
echo "unity exit $?"; grep -c "error CS" "$ROOT/work/character-shader/logs/$LOG.log"
