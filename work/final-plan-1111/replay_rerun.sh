#!/bin/bash
# replay_rerun.sh: after the still-air film, bring the changed copy up to date and run ReplayTests on it (its pin-approach set-up was tied to the old run-out).
cd "$(dirname "$0")"
while pgrep -f "film_calm.sh|hubbay_rerun.sh" > /dev/null; do sleep 20; done
CLONE=final-plan-dev ./sync.sh > logs/replay-sync.out 2>&1
CLONE=final-plan-dev ./utest.sh replay-new PlayMode "ReplayTests" > logs/replay-new.out 2>&1
echo "REPLAY DONE"; cut -c1-400 logs/replay-new.out
