#!/bin/bash
# wait for the Unity export, then Xcode build, then install on the phone
cd "$(dirname "$0")"
until grep -q "Unity exit" export.out 2>/dev/null; do sleep 15; done
cat export.out
grep -q "Unity exit: 0" export.out || { echo "CHAIN: Unity export failed"; exit 1; }
./xcode.sh | tee xcode.out
grep -q "xcodebuild exit: 0" xcode.out || { echo "CHAIN: Xcode build failed"; exit 1; }
./install.sh
