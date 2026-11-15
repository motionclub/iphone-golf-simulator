#!/bin/bash
# after_chain.sh: once chain.sh is done: the one baseline PlayMode batch the memory brake stopped at 16:55 (golf2), on the baseline copy.
cd "$(dirname "$0")"
while pgrep -f "chain.sh" > /dev/null; do sleep 30; done
bash playmode_chunks.sh pm-base2 golf2
echo "AFTER CHAIN DONE"; cat logs/pm-base2-summary.txt | cut -c1-300
