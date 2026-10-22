#!/bin/bash
# polite_queue.sh <ClassName> <out_dir> : keeps a run_editor.sh job queued, but steps aside whenever another chat's Unity job
# is waiting in heavy.sh at the same time (coordinator, 10-17: character work first), and re-queues once that job has run.
set -u
H=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/delegation-2026-10-17/heavy.sh
D=$(cd "$(dirname "$0")/.." && pwd)
mine() { pgrep -f "heavy.sh unity .*majestic-all-maps-UnityClone" | head -1; }
running() { pgrep -f "projectPath $HOME/majestic-all-maps-UnityClone" | grep -v "$(mine)" >/dev/null && $H status | grep -q "unity-1 .*majestic-all-maps-UnityClone"; }
others_waiting() { $H status | grep "^waiting: unity" | grep -v majestic-all-maps-UnityClone | grep -q .; }
others_any() { $H status | grep -E "^unity-1|^waiting: unity" | grep -v majestic-all-maps-UnityClone | grep -q .; }
start() { (cd "$D" && MAM_CAMS=${MAM_CAMS:-} nohup tools/run_editor.sh "$1" "$2" >> "$D/polite_$1.out" 2>&1 &); sleep 10; }
[ -z "$(mine)" ] && ! running && start "$1" "$2"
while :; do
  if $H status | grep -q "unity-1 .*majestic-all-maps-UnityClone"; then echo "$(date +%H:%M) running"; wait; while pgrep -f "projectPath $HOME/majestic-all-maps-UnityClone" >/dev/null; do sleep 30; done; echo "$(date +%H:%M) finished"; exit 0; fi
  if others_waiting && [ -n "$(mine)" ]; then
    echo "$(date +%H:%M) another Unity job is waiting: stepping aside"; pkill -f "tools/run_editor.sh $1"; kill "$(mine)" 2>/dev/null; sleep 5
    while others_any; do sleep 30; done
    echo "$(date +%H:%M) re-queueing"; start "$1" "$2"
  fi
  if [ -z "$(mine)" ] && ! running && ! others_waiting; then echo "$(date +%H:%M) not queued: starting"; start "$1" "$2"; fi
  sleep 20
done
