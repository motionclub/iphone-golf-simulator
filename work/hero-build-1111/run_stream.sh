#!/bin/bash
# run_stream.sh <clone> <jobs file>: runs each capture job in turn through heavy.sh (one Unity at a time per clone).
# Job line:  name|timeout_s|ENV=.. ENV=..|unity args      ({OUT} = this job's output folder, {P} = the clone)
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
A=$REPO/work/hero-build-1111
P=$1; JOBS=$2
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
while IFS='|' read -r name to envs args; do
  [[ -z "$name" || "$name" == \#* ]] && continue
  OUT=$A/shots/$name; mkdir -p "$OUT"
  envs=${envs//\{OUT\}/$OUT}; args=${args//\{OUT\}/$OUT}; args=${args//\{P\}/$P}
  echo "$(date +%H:%M:%S) START $name" >> $A/logs/progress.log
  rm -f "$P/Temp/UnityLockfile"
  ( env GOLF_MUTE=1 $envs $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath "$P" $args -logFile $A/logs/$name.log ) &
  pid=$!; t=0
  while kill -0 $pid 2>/dev/null; do sleep 5; t=$((t+5)); if [ $t -ge $to ]; then echo "$(date +%H:%M:%S) TIMEOUT $name" >> $A/logs/progress.log; pkill -f "projectPath $P" ; sleep 3; pkill -9 -f "projectPath $P"; break; fi; done
  wait $pid 2>/dev/null; rc=$?
  echo "$(date +%H:%M:%S) END $name rc=$rc files=$(find "$OUT" -type f | wc -l | tr -d ' ') (${t}s)" >> $A/logs/progress.log
done < "$JOBS"
echo "$(date +%H:%M:%S) STREAM DONE $JOBS" >> $A/logs/progress.log
