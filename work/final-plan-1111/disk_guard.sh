#!/bin/bash
# disk_guard.sh: while chain.sh runs, stop it (and its Unity) if the disk falls under 5 GB free: swap grows onto the same disk.
cd "$(dirname "$0")"
while pgrep -f "chain.sh" > /dev/null; do
  free=$(df -g "$HOME" | tail -1 | awk '{print $4}')
  if [ "${free:-99}" -lt 5 ]; then
    echo "$(date +%H:%M:%S) disk ${free} GB free: stopping the chain" >> logs/disk_guard.log
    pkill -f "chain.sh"; pkill -f "playmode_chunks.sh"; pkill -f "utest.sh"
    for p in $(pgrep -f "Unity -projectPath $HOME/unity-clones/final-plan"); do kill $p; done
    echo "DISK GUARD STOPPED THE CHAIN at ${free} GB free"; exit 1
  fi
  sleep 60
done
echo "disk guard: chain finished, disk $(df -g "$HOME" | tail -1 | awk '{print $4}') GB free"
