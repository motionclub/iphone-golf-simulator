#!/bin/zsh
# SMOOTH gate, no editor: builds a macOS standalone player of a checkout (this worktree, or MB_REPO for the BEFORE numbers)
# in its own APFS clone, with MenuProfileBoot (boots the menu with the phone's start message, walks it uncapped, logs frame
# timings) and runs it once at 1920x1080 windowed, muted.
#   work/menu-background/tools/player/run_player.sh <out dir>
set -e
P="$(cd "$(dirname "$0")" && pwd)"
REPO="${MB_REPO:-$(cd "$P/../../../.." && pwd)}"
CLONE="${MB_PLAYER_CLONE:-$HOME/unity-clones/menu-player}"
OUT="$1"; mkdir -p "$OUT"
UNITY=/Applications/Unity/Hub/Editor/$(sed -n 's/^m_EditorVersion: //p' "$REPO/Unity/ProjectSettings/ProjectVersion.txt")/Unity.app/Contents/MacOS/Unity
HEAVY="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/delegation-2026-10-17/heavy.sh"
[ -d "$CLONE" ] || cp -c -R "$HOME/unity-clones/menu-background" "$CLONE"
for d in Assets Packages ProjectSettings; do rsync -a --delete --exclude 'MenuProfile' --exclude 'MenuProfile.meta' --exclude 'Tests/PlayMode/MenuBackgroundCapture.cs*' --exclude 'Tests/PlayMode/MenuFrameTime.cs*' "$REPO/Unity/$d/" "$CLONE/$d/"; done
mkdir -p "$CLONE/Assets/MenuProfile/Editor"
cp "$P/MenuProfileBoot.cs" "$CLONE/Assets/MenuProfile/"; cp "$P/MenuProfileBuild.cs" "$CLONE/Assets/MenuProfile/Editor/"
APP="$CLONE/Builds/MenuProfile.app"
"$HEAVY" unity "$UNITY" -batchmode -quit -buildTarget OSXUniversal -projectPath "$CLONE" -executeMethod MenuProfileBuild.Build -menuBuildOut "$APP" -logFile "$OUT/build.log" || true
grep -m1 "MenuProfileBuild:" "$OUT/build.log" || { echo "build failed (see $OUT/build.log)"; exit 1; }
BIN=$(ls "$APP/Contents/MacOS/" | head -1)
"$HEAVY" status > "$OUT/machine_load.txt" 2>&1 || true
GOLF_MUTE=1 "$APP/Contents/MacOS/$BIN" -menuprofile "$OUT" -screen-width 1920 -screen-height 1080 -screen-fullscreen 0 -logFile "$OUT/player.log" || true
cat "$OUT/player_frametime.txt"
