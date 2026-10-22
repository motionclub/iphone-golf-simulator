#!/bin/zsh
# ROOT ONLY after complete reviewed assets/fixtures are installed. Build only.
set -euo pipefail
TASK_DIR=work/reference-rebuild/original-native-adoption29
xcodebuild -project GolfArcade.xcodeproj -scheme GolfArcade -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath work/reference-rebuild/original-native-adoption1/DerivedData CODE_SIGNING_ALLOWED=NO build-for-testing > "$TASK_DIR/native-build.log" 2>&1
python3 "$TASK_DIR/audit-package.py" --bundle work/reference-rebuild/original-native-adoption1/DerivedData/Build/Products/Debug-iphonesimulator/GolfArcade.app --output "$TASK_DIR/built-bundle-audit.json"
# No simulator/phone launch, no XCTest execution or complete test claim here.
