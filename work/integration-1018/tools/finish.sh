#!/bin/zsh
# Chat 12 (max speed): when BOTH clearance halves are done -> tennis tracks into Unity3 (final combined state) -> IN PARALLEL:
#   (a) iOS export from a fresh APFS snapshot ~/integration-work/phone/root/Unity (+ app, tests, controls, specs, blender link) -> xcode build
#   (b) final EditMode on Unity3        (c) install_real.py into Unity/ (3-way, one rollback)
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; I=$R/work/integration-1018; W=$HOME/integration-work; C=$W/Unity3
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$R/work/delegation-2026-10-17/heavy.sh
P=$I/logs/finish.progress; mark() { echo "$(date +%H:%M) $*" >> $P; }
until grep -q done $I/logs/side_lane2.progress 2>/dev/null && grep -q done $I/logs/tennis_bake.progress 2>/dev/null; do sleep 20; done
mark "both bake halves done: $(grep bake $I/logs/side_lane2.progress | tail -1) | $(grep bake $I/logs/tennis_bake.progress | tail -1)"
for x in Male Female; do cp $W/Unity4/Assets/Resources/HeroClearance/Tracks_${x}_Tennis.bytes $C/Assets/Resources/HeroClearance/; done
mark "tennis tracks copied into Unity3"
# (a) export root
PR=$W/phone/root; mkdir -p $PR
cp -c -R $C $PR/Unity
for x in GolfArcade GolfArcadeTests GolfArcadeUITests MotionClubControls; do cp -c -R $R/$x $PR/$x; done
cp $R/project.yml $R/project-unity.yml $PR/; ln -s $R/blender $PR/blender
mark "phone root ready ($PR); standard tennis clips: $(grep -c 'name: ' $PR/Unity/Assets/Resources/StandardCharacters/standard_male_tennis.fbx.meta)"
( GOLF_MUTE=1 $H unity $U -batchmode -quit -projectPath $PR/Unity -buildTarget iOS -job-worker-count 1 --burst-disable-compilation -executeMethod GolfArcade.EditorTools.BuildMenu.BuildIOS -logFile $W/phone/unity-export.log
  mark "iOS export rc=$? $(cat $PR/Unity/Library/BuildResults/ios.txt 2>/dev/null | head -1)"
  cd $PR && xcodegen generate --spec project-unity.yml > $W/phone/xcodegen.log 2>&1 && \
  xcodebuild -project GolfArcadeUnity.xcodeproj -scheme GolfArcade -configuration Release -sdk iphoneos -destination generic/platform=iOS -derivedDataPath $W/phone/DerivedData \
    DEVELOPMENT_TEAM=9VP5B3Q5VQ CODE_SIGN_STYLE=Automatic APP_BUNDLE_ID=com.aloniewski.GolfArcade -allowProvisioningUpdates build > $W/phone/xcode-build.log 2>&1
  mark "xcodebuild rc=$? app=$(ls -d $W/phone/DerivedData/Build/Products/Release-iphoneos/GolfArcade.app 2>/dev/null)" ) &
EXP=$!
# (b) final EditMode on Unity3
( $I/tools/tests.sh comb_edit_final $C EditMode; mark "final EditMode $(head -1 $I/tests/comb_edit_final/summary.txt)" ) &
EDT=$!
# (c) the real install (3-way, one rollback)
python3 -I $I/tools/install_real.py plan > $I/logs/install_plan.txt 2>&1; mark "install plan: $(grep -c '^add\|^replace\|^remove' $I/logs/install_plan.txt) files, $(grep -c CONFLICT $I/logs/install_plan.txt) conflicts"
python3 -I $I/tools/install_real.py install > $I/logs/install_real.txt 2>&1; mark "install: $(tail -1 $I/logs/install_real.txt)"
wait $EDT; wait $EXP
mark done
