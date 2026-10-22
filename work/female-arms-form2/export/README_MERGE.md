# Merging the female ARMS zone

`arms_delta.npz` holds the 1,592 moved vertices (start position, new position) in two index orders.

```bash
# limbs-chat / torso+limbs vertex order (22,419 verts)
blender -b <target>.blend --python merge_arms_delta.py -- arms_delta.npz <out>.blend --order limbs
# ArtDir / torso-candidate vertex order (22,444 verts)
blender -b <target>.blend --python merge_arms_delta.py -- arms_delta.npz <out>.blend --order base
```
Each moved vertex must still be at its start position (bit-exact) in the target; conflicts are reported and skipped (`--force` to overwrite). Positions only. Arm zone is disjoint from the torso zone (chat 7), the head (z>=1.37 / neck) and the limbs zone (wrist rings and below), so order does not matter. Never clear custom split normals on Body_F.
