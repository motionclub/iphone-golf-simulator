#!/bin/bash
# after_chunks.sh: once both PlayMode batch runs are done and the machine is quiet: frame times per scene on the Mac editor
# (FrameRate60bTests.RuntimeHoldsSixty) for the baseline copy and the changed one, then the intro-rule tests on the changed code.
cd "$(dirname "$0")"
while pgrep -f "playmode_chunks.sh pm-" > /dev/null; do sleep 30; done
mkdir -p phase0/frames-base phase0/frames-new
FR60B_DIR=$PWD/phase0/frames-base ./utest.sh frames-base PlayMode "FrameRate60bTests.RuntimeHoldsSixty" > logs/frames-base.out 2>&1
CLONE=final-plan-dev ./sync.sh > logs/after-sync.out 2>&1
CLONE=final-plan-dev FR60B_DIR=$PWD/phase0/frames-new ./utest.sh frames-new PlayMode "FrameRate60bTests.RuntimeHoldsSixty" > logs/frames-new.out 2>&1
CLONE=final-plan-dev ./utest.sh intro-rules PlayMode "IntroRulesPlayTests" > logs/intro-rules.out 2>&1
echo "AFTER DONE"; tail -3 logs/frames-base.out logs/frames-new.out; cat logs/intro-rules.out
