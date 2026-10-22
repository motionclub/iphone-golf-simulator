#!/bin/bash
# Samples memory every 30 s into memlog.csv so we can see how much leeway the machine has.
cd "$(dirname "$0")"
[ -f memlog.csv ] || echo "time,free_pct,swap_used_mb,unity,blender" > memlog.csv
while :; do
  f=$(memory_pressure | awk -F': ' '/free percentage/{gsub("%","",$2);print $2+0}')
  sw=$(sysctl -n vm.swapusage | awk '{gsub("M","",$6);print $6}')
  u=$(ps -axo comm | grep -cE "MacOS/Unity$"); b=$(ps -axo comm | grep -cE "MacOS/Blender$")
  echo "$(date +%H:%M:%S),$f,$sw,$u,$b" >> memlog.csv
  sleep 30
done
