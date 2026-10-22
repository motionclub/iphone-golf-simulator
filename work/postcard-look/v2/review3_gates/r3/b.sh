B=/Applications/Blender.app/Contents/MacOS/Blender; G=work/postcard-look/v2/review3_gates; O=work/postcard-look/v2/review3_gates/r3
$B -b --factory-startup --python $G/ground_cmp.py > $O/ground_cmp.out 2>&1 &
$B -b --factory-startup --python $G/markers_cmp.py > $O/markers.out 2>&1 &
$B -b --factory-startup --python $G/fbx_ground.py > $O/fbx_ground.out 2>&1 &
wait
for m in blend fbx; do for n in 08 09 10; do $B -b --factory-startup --python $G/props_check.py -- $m $n > $O/props_${m}_$n.out 2>&1 & done; done; wait
for m in fbx blend; do $B -b --factory-startup --python $G/path_check.py -- $m > $O/path_$m.out 2>&1 & done; wait
