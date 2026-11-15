#!/bin/bash
# hubbay_rerun.sh: after the golf2 runs, the one PlayMode test that passed before Phase 1 and failed after, twice on the changed copy and once on the baseline.
cd "$(dirname "$0")"
while pgrep -f "golf2_both.sh" > /dev/null; do sleep 20; done
for i in 1 2; do CLONE=final-plan-dev ./utest.sh hubbay-new$i PlayMode "HubBayTests.StandingUpMidLoadLeavesNothingLoaded" > logs/hubbay-new$i.out 2>&1; done
./utest.sh hubbay-base1 PlayMode "HubBayTests.StandingUpMidLoadLeavesNothingLoaded" > logs/hubbay-base1.out 2>&1
echo "HUBBAY DONE"; tail -4 logs/hubbay-new1.out logs/hubbay-new2.out logs/hubbay-base1.out | cut -c1-300
