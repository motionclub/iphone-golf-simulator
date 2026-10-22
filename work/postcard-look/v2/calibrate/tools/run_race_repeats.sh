#!/bin/bash
# the old waiting (GOLF_LOOK_PROBE_RACE=1) a few more times: does PROBE_SWAP_TOOK_EFFECT ever catch a stale HoleView?
R="$(cd "$(dirname "$0")/../../../../.." && pwd)"; cd "$R"
O=work/postcard-look/v2/calibrate/r2
for l in r2race2 r2race3 r2race4 r2race5; do GOLF_LOOK_PROBE_RACE=1 work/postcard-look/v2/calibrate/tools/run_probe.sh $l > "$O/final_probe_$l.out" 2>&1; done
echo done > "$O/race_repeats_done.flag"
