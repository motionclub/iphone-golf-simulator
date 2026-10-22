#!/bin/zsh
# run.sh <label> <command...> : run a command and append its start / end time to work/emotes/logs/runs.log (the write-window ledger the verifier uses).
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
L=$R/work/emotes/logs/runs.log
label=$1; shift
s=$(date '+%Y-%m-%d %H:%M:%S')
"$@"
rc=$?
e=$(date '+%Y-%m-%d %H:%M:%S')
echo "$s | $e | rc=$rc | $label | $*" | cut -c1-300 >> $L
exit $rc
