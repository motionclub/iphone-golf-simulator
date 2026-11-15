#!/bin/bash
# golf2_both.sh: the golf2 PlayMode batch (8 classes) on the changed copy, then on the baseline copy, one Unity at a time.
cd "$(dirname "$0")"
CLONE=final-plan-dev bash playmode_chunks.sh pm-new2 golf2
bash playmode_chunks.sh pm-base2 golf2
echo "GOLF2 DONE"; cat logs/pm-new2-summary.txt logs/pm-base2-summary.txt | cut -c1-400
