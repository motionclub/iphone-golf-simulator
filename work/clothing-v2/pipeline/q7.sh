#!/bin/zsh
# chat 5 queue 7: the timed NEW_GARMENT_30MIN test after q6 (one heavy job at a time): a 3/4-sleeve polo for the male tennis hero, design data only
cd ${0:A:h}
while pgrep -f "zsh ./q6.sh" >/dev/null; do sleep 30; done
T0=$(date +%s); echo "START $(date +%H:%M:%S)" > logs/new_ls.time
./garment_new MatchHero_Male polo2 tennis_male Kit_Top '{"sleeve":{"t":[0.05,0.20,0.30],"r":[0.086,0.072,0.060]}}' run=new_ls > logs/new_ls.log 2>&1
echo "END $(date +%H:%M:%S) exit $? wall $(( $(date +%s) - T0 )) s" >> logs/new_ls.time
