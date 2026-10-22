#!/bin/bash
# waits until the main project compiles (another chat's Multiplayer work in progress may break it), then runs the final chain.
R="$(cd "$(dirname "$0")/../../../../.." && pwd)"; cd "$R"
O=work/postcard-look/v2/calibrate/r2
rm -f "$O/final3_done.flag"
n=0
while true; do
  n=$((n+1))
  work/postcard-look/v2/calibrate/tools/run_probe.sh r2try > "$O/final3_try.out" 2>&1
  e=$(grep -c "error CS" work/postcard-look/v2/calibrate/logs/probe_r2try.log)
  echo "try $n $(date): $e error CS" >> "$O/final3_tries.log"
  [ "$e" = "0" ] && break
  [ $n -ge 60 ] && { echo "gave up after $n tries" >> "$O/final3_tries.log"; echo "gave up" > "$O/final3_done.flag"; exit 1; }
  sleep 45
done
work/postcard-look/v2/calibrate/tools/run_r2_final.sh
