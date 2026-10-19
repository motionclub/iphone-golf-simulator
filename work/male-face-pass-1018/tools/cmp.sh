#!/bin/zsh
# tools/cmp.sh <tag> : REF17 / BEFORE (audit) / <tag> for front, 3/4, lips -> proof/cmp_<tag>_{a,b}.jpg
cd ${0:A:h}/..
S=../../ArtDir/style/alive/male-reference-pack-2026-10-17/sheets/17-face-detail-neutral.png; B=../male-audit-1018/unity_out/now/male_views; N=unity_out/$1/male_views
python3 tools/row.py proof/cmp_$1_a.jpg 640 "REF17 front=$S@190,140,510,560" "BEFORE=$B/front.png@200,80,880,980" "NOW $1=$N/front.png@200,80,880,980" "REF17 3/4=$S@820,140,1180,560" "BEFORE=$B/tq45.png@200,80,880,980" "NOW $1=$N/tq45.png@200,80,880,980"
python3 tools/row.py proof/cmp_$1_b.jpg 560 "REF17 lips=$S@710,720,1340,1200" "BEFORE=$B/front_lower.png" "NOW $1=$N/front_lower.png" "REF17 profile=$S@1450,140,1880,560" "BEFORE=$B/right90.png@170,60,910,1020" "NOW $1=$N/right90.png@170,60,910,1020"
