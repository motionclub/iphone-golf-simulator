#!/bin/zsh
# ROOT ONLY. Desktop Metal snapshots; never runs Unity or a physical device.
set -euo pipefail
FACE_TASK=work/reference-rebuild/face-material30
NATIVE_DATA="${1:?Pass the accepted geometry native task directory containing export and golden}"
xcrun swiftc -module-cache-path work/reference-rebuild/original-native-adoption1/module-cache -O GolfArcade/Unity/MatchHeroData.swift GolfArcade/Unity/MatchHeroSurfaces.swift GolfArcade/Unity/MatchHeroMotion.swift "$FACE_TASK/NativeParity.swift" -o "$FACE_TASK/native-face-proof" > "$FACE_TASK/swift-build.log" 2>&1
for variant in control satin; do
  flag=0
  [[ "$variant" == satin ]] && flag=1
  PROOF_START=$(date '+%Y-%m-%d %H:%M:%S')
  VISUAL_CHARACTER_SKIN_POLISH="$flag" NATIVE_PROOF_SKIN_MALE=EA8D71 NATIVE_PROOF_SKIN_FEMALE=FBAE8F NATIVE_PROOF_LOBBY_LIGHT=1 NATIVE_PROOF_PRIMARY_ONLY=1 NATIVE_PROOF_MATERIAL_ONLY=1 NATIVE_PROOF_QUICK=1 "$FACE_TASK/native-face-proof" "$NATIVE_DATA/export" "$NATIVE_DATA/golden" "$FACE_TASK/native-$variant" > "$FACE_TASK/native-$variant-runtime.log" 2>&1
  /usr/bin/log show --start "$PROOF_START" --style compact --predicate 'process == "native-face-proof" AND subsystem == "com.apple.scenekit"' > "$FACE_TASK/native-$variant-metal.log" 2>&1
  if rg -q 'failed compiling shader|FATAL ERROR' "$FACE_TASK/native-$variant-metal.log"; then
    print 'FAIL: SceneKit Metal pipeline'; exit 1
  fi
done
