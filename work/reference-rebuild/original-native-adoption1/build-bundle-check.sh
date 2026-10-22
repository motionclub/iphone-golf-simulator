#!/bin/zsh
# After root installs reviewed assets/resources/test patches; build only, no launch.
set -euo pipefail
TASK_DIR=work/reference-rebuild/original-native-adoption1
xcodebuild -project GolfArcade.xcodeproj -scheme GolfArcade -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath "$TASK_DIR/DerivedData" CODE_SIGNING_ALLOWED=NO build-for-testing > "$TASK_DIR/native-build.log" 2>&1
python3 "$TASK_DIR/audit-package.py" --bundle "$TASK_DIR/DerivedData/Build/Products/Debug-iphonesimulator/GolfArcade.app" --output "$TASK_DIR/built-bundle-audit.json"
# GolfArcadeUnity's resource phase is separately audited by audit-package.py.
# Its full link/build requires root's current Unity iOS export and is root-owned.
