#!/bin/bash
# sync.sh: copy the shared project's scripts, tests and editor code into the plan's project copy (source of truth = the repo's Unity/).
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
C=$HOME/unity-clones/${CLONE:-final-plan}/Unity
for d in Assets/Scripts Assets/Tests Assets/Editor; do rsync -a --itemize-changes "$REPO/Unity/$d/" "$C/$d/" | grep -v '^\.' ; done
exit 0
