#!/bin/zsh
# male-garments: lobby parity WITHOUT touching the shared lobby assets. Exports from ~/male-garments-UnityClone into lobby/export, overlays a
# private copy of GolfArcade/Unity/CharacterAssets (lobby/assets), regenerates the .ktx of my garment maps, renders game vs lobby, sheets.
# The install into the real CharacterAssets is left to the integration chat (patches/LOBBY_INSTALL.md).
set -e; setopt null_glob
ME=${0:A:h:h}; REPO=${ME:h:h}; L=$ME/lobby; CL=$HOME/male-garments-UnityClone
HV=$REPO/work/delegation-2026-10-17/heavy.sh; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
export GOLF_MUTE=1
mkdir -p $L/logs; rm -rf $L/export $L/golden; mkdir -p $L/export $L/golden
for job in Run RunDistance RunGolf; do
  MH_LOCKER_FACE_PARITY=0 MH_LOCKER_OUT=$L/export MH_LOCKER_GOLDEN=$L/golden MH_LOCKER_REPORT=$L/logs/$job-report.txt \
    $HV unity $U -batchmode -nographics -quit -projectPath $CL -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.$job -logFile $L/logs/$job.log \
    || { echo "export $job FAILED"; grep -m5 -E "error CS|Exception" $L/logs/$job.log; exit 1; }
done
rm -rf $L/assets; cp -cR $REPO/GolfArcade/Unity/CharacterAssets $L/assets
changed=(); for f in $L/export/*.*; do n=${f:t}; cmp -s $f $L/assets/$n || { cp $f $L/assets/$n; changed+=$n; }; done
print -l $changed > $L/changed_export.txt; echo "export: ${#changed} changed files vs the repo's CharacterAssets"
conv=/Applications/Xcode.app/Contents/Developer/usr/bin/TextureConverter; : > $L/changed_ktx.txt
for p in $CL/Assets/Resources/{Tennis,Golf}/KitsV2/**/KitV2_*.png; do
  name=${p:t:r}; out=$L/assets/MatchHero_$name.ktx; fmt=ASTC8x8; [[ $name == *Atlas* ]] && fmt=ASTC4x4
  [[ -f $out && $out -nt $p && $REPO/GolfArcade/Unity/CharacterAssets/MatchHero_$name.ktx -nt $p ]] && continue
  $conv --compression_format=$fmt --compression_quality=Highest --alpha_mode=Preserve --channel_weighting=Linear --gamma_in=1 --gamma_out=1 --flip_y --wrap_mode=Clamp --file_format=KTX --output=$out $p > /dev/null
  cmp -s $out $REPO/GolfArcade/Unity/CharacterAssets/MatchHero_$name.ktx || echo MatchHero_$name.ktx >> $L/changed_ktx.txt
done
echo "ktx changed: $(wc -l < $L/changed_ktx.txt)"
rm -rf $L/unity $L/lobby; mkdir -p $L/unity/tennis $L/unity/golf $L/lobby/tennis $L/lobby/golf
for sport in tennis golf; do
  LP_OUT=$L/unity/$sport LP_GOLF=$([[ $sport == golf ]] && echo 1 || echo 0) \
    $HV unity $U -batchmode -quit -projectPath $CL -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.CaptureLobbyParity -logFile $L/logs/capture-$sport.log \
    || { echo "capture $sport FAILED"; exit 1; }
done
S=$REPO/work/hero-sync
swiftc -swift-version 6 -O -parse-as-library $S/lobby_render.swift $REPO/GolfArcade/Unity/MatchHeroData.swift $REPO/GolfArcade/Unity/MatchHeroSurfaces.swift \
  $REPO/GolfArcade/Unity/MatchHeroMotion.swift -framework SceneKit -framework AppKit -framework Metal -o $L/lobby_render
LP_ASSETS=$L/assets LP_DISTANCE=1 $L/lobby_render $L/lobby/tennis 2>&1 | grep -v "^$" | grep -iv warning || true
LP_ASSETS=$L/assets LP_GOLF=1 $L/lobby_render $L/lobby/golf default 2>&1 | grep -v "^$" | grep -iv warning || true
python3 $S/compare.py $L $L/sheets
echo "lobby parity sheets: $L/sheets"
