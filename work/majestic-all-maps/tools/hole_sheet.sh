#!/bin/bash
# hole_sheet.sh <views_dir> <NN> <out.jpg> : every captured view of a hole on one sheet
D=$1; N=$2; args=()
for v in tee flyOpen flyH1 flyH2 flyH3 mid approach offL offR puttFront puttLeft puttRight greenBack reverseMid pan0 pan90 pan180 pan270 crane map driveGood_0 driveGood_1 driveGood_2 driveGood_rest driveBad_0 driveBad_1 driveBad_2 driveBad_rest; do
  [ -f "$D/h${N}_$v.jpg" ] && args+=("h$N $v=$D/h${N}_$v.jpg")
done
python3 "$(dirname "$0")/sheet.py" "$3" 6 480 "${args[@]}"
