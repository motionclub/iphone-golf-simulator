#!/bin/zsh
# Run only after root's three serialized exports. Coordinates actual Metal GPU use.
set -euo pipefail
TASK_DIR=work/reference-rebuild/original-native-adoption1
python3 "$TASK_DIR/package-resources.py"
python3 "$TASK_DIR/audit-package.py"
xcrun swiftc -module-cache-path "$TASK_DIR/module-cache" -O GolfArcade/Unity/MatchHeroData.swift GolfArcade/Unity/MatchHeroSurfaces.swift GolfArcade/Unity/MatchHeroMotion.swift "$TASK_DIR/NativeParity.swift" -o "$TASK_DIR/native-adoption-parity"
PROOF_START=$(date '+%Y-%m-%d %H:%M:%S')
PROOF_CODE=0
NATIVE_PROOF_QUICK=1 "$TASK_DIR/native-adoption-parity" "$TASK_DIR/export" "$TASK_DIR/golden" "$TASK_DIR/actual" > "$TASK_DIR/native-runtime.log" 2>&1 || PROOF_CODE=$?
/usr/bin/log show --start "$PROOF_START" --style compact --predicate 'process == "native-adoption-parity" AND subsystem == "com.apple.scenekit"' > "$TASK_DIR/native-metal.log" 2>&1
cat "$TASK_DIR/native-runtime.log"
if rg -q 'failed compiling shader|FATAL ERROR' "$TASK_DIR/native-metal.log"; then
  echo 'FAIL: SceneKit Metal compiler failure; inspect native-metal.log'
  exit 1
fi
exit "$PROOF_CODE"
