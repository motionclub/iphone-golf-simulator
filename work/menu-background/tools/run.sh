#!/bin/zsh
# Menu background proof: syncs this worktree's Unity/ into the APFS clone, copies the capture test in, runs
# MenuBackgroundCapture.Capture windowed (batchmode never renders), muted, through the machine's heavy-job gate.
#   work/menu-background/tools/run.sh <out dir> [extra env, e.g. MB_SEQ=low MB_FRAMES=120]
#   MB_TEST=GolfArcade.Tests.MenuFrameTime.Profile work/menu-background/tools/run.sh <out dir>   (the SMOOTH gate)
set -e
TOOLS="$(cd "$(dirname "$0")" && pwd)"
# MB_REPO: measure another checkout (e.g. an origin/main worktree for the BEFORE numbers) with this harness
REPO="${MB_REPO:-$(cd "$TOOLS/../../.." && pwd)}"
CLONE="${MB_CLONE:-$HOME/unity-clones/menu-background}"
OUT="$1"; shift || true
UNITY=/Applications/Unity/Hub/Editor/$(sed -n 's/^m_EditorVersion: //p' "$REPO/Unity/ProjectSettings/ProjectVersion.txt")/Unity.app/Contents/MacOS/Unity
for d in Assets Packages ProjectSettings; do rsync -a --delete --exclude 'Tests/PlayMode/MenuBackgroundCapture.cs*' --exclude 'Tests/PlayMode/MenuFrameTime.cs*' "$REPO/Unity/$d/" "$CLONE/$d/"; done
cp "$TOOLS/MenuBackgroundCapture.cs" "$TOOLS/MenuFrameTime.cs" "$CLONE/Assets/Tests/PlayMode/"
mkdir -p "$OUT"
HEAVY="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/delegation-2026-10-17/heavy.sh"
env GOLF_MUTE=1 MB_OUT="$OUT" "$@" "$HEAVY" unity "$UNITY" -projectPath "$CLONE" -runTests -testPlatform PlayMode \
  -testFilter "${MB_TEST:-GolfArcade.Tests.MenuBackgroundCapture.Capture}" -testResults "$OUT/results.xml" -logFile "$OUT/unity.log" || true
grep -o 'result="[A-Za-z]*"' "$OUT/results.xml" | head -3 || echo "no results (see $OUT/unity.log)"
