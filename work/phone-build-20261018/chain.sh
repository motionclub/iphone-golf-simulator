#!/bin/bash
cd "$(dirname "$0")"
./export.sh > export.out 2>&1; echo "export exit $?"
n=$(grep -c "name: " root/Unity/Assets/Resources/StandardCharacters/standard_male_tennis.fbx.meta); echo "tennis clip names after export: $n"
grep -q "Build succeeded\|Succeeded\|result: Succeeded" root/Unity/Library/BuildResults/ios.txt 2>/dev/null && echo "unity build result: $(head -3 root/Unity/Library/BuildResults/ios.txt)" || { echo "unity build result missing/failed:"; cat root/Unity/Library/BuildResults/ios.txt 2>/dev/null; tail -20 unity-export.log; exit 1; }
./xcode.sh; grep -q "BUILD SUCCEEDED" xcode-build.log || { echo "xcode failed:"; grep -E "error:" xcode-build.log | head -15; exit 1; }
./install.sh
