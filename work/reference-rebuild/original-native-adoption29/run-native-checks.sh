#!/bin/zsh
# ROOT ONLY: serial native GPU interval after export profiles are complete.
set -euo pipefail
TASK_DIR=work/reference-rebuild/original-native-adoption29
MANIFEST_ARGS=()
PROOF_TENNIS_ONLY=0
if [[ "${1:-}" == "--tennis-only" ]]; then
  PROOF_TENNIS_ONLY=1
  for name in MatchHero_Male MatchHero_Female MatchHero_Male_Distance MatchHero_Female_Distance; do
    MANIFEST_ARGS+=(--manifest "$name")
  done
fi
python3 "$TASK_DIR/audit-registration.py"
python3 "$TASK_DIR/package-resources.py" "${MANIFEST_ARGS[@]}"
python3 "$TASK_DIR/audit-package.py" "${MANIFEST_ARGS[@]}"
# Reuse the existing compiler cache instead of duplicating a large archive.
xcrun swiftc -module-cache-path work/reference-rebuild/original-native-adoption1/module-cache -O GolfArcade/Unity/MatchHeroData.swift GolfArcade/Unity/MatchHeroSurfaces.swift GolfArcade/Unity/MatchHeroMotion.swift "$TASK_DIR/NativeParity.swift" -o "$TASK_DIR/native-adoption-parity"
PROOF_START=$(date '+%Y-%m-%d %H:%M:%S')
PROOF_CODE=0
VISUAL_CHARACTER_STAGE_LIGHT=0 NATIVE_PROOF_QUICK=1 NATIVE_PROOF_TENNIS_ONLY="$PROOF_TENNIS_ONLY" "$TASK_DIR/native-adoption-parity" "$TASK_DIR/export" "$TASK_DIR/golden" "$TASK_DIR/actual" > "$TASK_DIR/native-runtime.log" 2>&1 || PROOF_CODE=$?
/usr/bin/log show --start "$PROOF_START" --style compact --predicate 'process == "native-adoption-parity" AND subsystem == "com.apple.scenekit"' > "$TASK_DIR/native-metal.log" 2>&1
if rg -q 'failed compiling shader|FATAL ERROR' "$TASK_DIR/native-metal.log"; then
  print 'FAIL: SceneKit Metal pipeline; inspect native-metal.log'
  exit 1
fi
exit "$PROOF_CODE"
