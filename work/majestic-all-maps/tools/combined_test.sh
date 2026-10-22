#!/bin/bash
# combined_test.sh : maps (chat 10) + weather (chat W) together in ~/majestic-all-maps-UnityClone. Copies chat W's dormant
# files + harness into the clone, applies its shared patch, then (1) chat W's harness on W09 (ashfall, h22) and X16 (h16,
# rain -> ash) with the maps layer on, (2) the maps ref views of 22 and 16 in clear weather. Muted, through heavy.sh.
set -eu
D=$(cd "$(dirname "$0")/.." && pwd); ROOT=$(cd "$D/../.." && pwd); C=$HOME/majestic-all-maps-UnityClone
cd "$D"
cp "$ROOT"/Unity/Assets/Scripts/Majestic/MajesticWeather*.cs "$C/Assets/Scripts/Majestic/"
cp "$ROOT"/Unity/Assets/Resources/Majestic/MajesticWeather* "$C/Assets/Resources/Majestic/" 2>/dev/null || true
rm -f "$C"/Assets/Resources/Majestic/*.meta.meta
cp "$ROOT/work/majestic-weather/unity/Assets/Editor/MajesticWeatherShots.cs" "$C/Assets/Editor/"
python3 -I "$ROOT/work/majestic-weather/tools/patch_shared.py" apply "$C"
python3 -I "$ROOT/work/majestic-weather/tools/patch_shared.py" check "$C" && echo "weather shared patch: applied"
MAM_WITH_LAYER=1 MW_JOBS=refs,read MW_SLOTS=W09,X16 MW_OUT=$D/g3/combined_weather tools/run_editor.sh MajesticWeatherShots g3/combined_weather
MAM_WITH_LAYER=1 MAM_VIEWS=ref MAM_HOLES=22,16 tools/run_editor.sh MajesticHoleViews g3/combined_clear
