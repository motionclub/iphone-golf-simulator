#!/bin/bash
# Re-creates the evidence in v2/gates/runs: the verify on the repo files, on the baseline, on the lib smoke builds (as of 2026-10-04 10:44 and
# the 2026-10-03 pre-repair ones), against a Look snapshot (fixtures/look_at_run) and the old failing Look (fixtures/old_look); then the self-test.
# usage: work/postcard-look/v2/gates/tools/run_evidence.sh [--selftest]      (selftest = ~20 min, both stages, all holes)
R="$(cd "$(dirname "$0")/../../../../.." && pwd)"; cd "$R"
B=/Applications/Blender.app/Contents/MacOS/Blender; V=blender/scripts/postcard_look_verify.py; G=work/postcard-look/v2/gates
export PYTHONDONTWRITEBYTECODE=1
for h in 8 9 10; do t=$(printf "%02d" $h)
  $B -b --factory-startup --python $V -- $h --look-dir $G/fixtures/look_at_run --json $G/runs/repo_files_$t.json > $G/runs/repo_files_$t.log 2>&1
  $B -b --factory-startup --python $V -- $h --blend work/postcard-look/baseline/blender/hole_$t.blend --fbx work/postcard-look/baseline/fbx/hole_$t.fbx --look-dir $G/fixtures/look_at_run --json $G/runs/baseline_$t.json > $G/runs/baseline_$t.log 2>&1
  $B -b --factory-startup --python $V -- $h --blend $G/fixtures/lib_smoke_now/hole_$t.blend --fbx $G/fixtures/lib_smoke_now/hole_$t.fbx --look-dir $G/fixtures/look_at_run --json $G/runs/libsmoke_now_$t.json > $G/runs/libsmoke_now_$t.log 2>&1
  $B -b --factory-startup --python $V -- $h --blend $G/fixtures/lib_smoke_old/hole_$t.blend --fbx $G/fixtures/lib_smoke_old/hole_$t.fbx --look-dir $G/fixtures/old_look --json $G/runs/libsmoke_old_$t.json > $G/runs/libsmoke_old_$t.log 2>&1
  # the lib smoke holes against the LIVE Look folder of the repo (the tex agent keeps writing it: the numbers move)
  $B -b --factory-startup --python $V -- $h --blend $G/fixtures/lib_smoke_now/hole_$t.blend --fbx $G/fixtures/lib_smoke_now/hole_$t.fbx --look-dir Unity/Assets/Resources/Course/Look --json $G/runs/livelook_$t.json > $G/runs/livelook_$t.log 2>&1
done
# the REAL props library (rocks / stretch gates on a props-only FBX; plants fail there because the test FBX has no terrain)
$B -b --factory-startup --python $G/tools/run_gate.py -- 8 work/postcard-look/v2/review_V/props_test_08.fbx g_rock_verts,g_rock_variety,g_rock_stretch,g_props_off_play > $G/runs/props_lib_08.log 2>&1
$B -b --factory-startup --python $G/tools/run_gate.py -- 10 work/postcard-look/v2/props/scratch/props_test_10.fbx g_rock_verts,g_rock_variety,g_rock_stretch,g_props_off_play > $G/runs/props_lib_10.log 2>&1
for g in "repo_files_*" "baseline_*" "libsmoke_old_*" "libsmoke_now_*" "livelook_*"; do echo "######## $g"; python3 $G/tools/summarize_runs.py "$g.json"; done
if [ "$1" = "--selftest" ]; then
  $B -b --factory-startup --python $V -- all --selftest --selftest-fbx --selftest-dir $G/st > $G/runs/selftest_all_fbx.log 2>&1
  grep -E "^SELFTEST_GATE|^SELFTEST: [0-9]+ lines|^RESULT" $G/runs/selftest_all_fbx.log
  python3 $G/tools/summarize_mut.py $G/runs/selftest_all_fbx.log --json $G/runs/selftest_summary.json
fi
work/postcard-look/guards.sh
