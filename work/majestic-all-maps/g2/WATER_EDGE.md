# Water / lava edge in frame — what blocks it (r26 reads, 10-18)

Structural item `water_edge`: 30/80 views show the sea or lava edge the reference shows. The coast itself is now dressed in every sea hole (shore kit + foam + shallows); in the failing views it is simply not in frame. Causes:

| view | target shows | blocker | fix that stays in the look layer? |
|---|---|---|---|
| h07 tee, h07 approach | sea + cliffs + lighthouse headland on the right | course pines along the right rough (authored placements) | no: needs thinning authored trees (decision) |
| h07 offR | cliff drop, sea, sailboats | the coast lies ~40 yd further right, outside the camera's view | no: camera framing (harness / game camera) |
| h07 greenBack | sea on the left behind the tee bluff | terrain rise behind the tee | no |
| h09 mid | lagoon on the left | terrain + rough rise hides the lagoon | no |
| h12 offL / offR | turquoise channel / open sea | the tee-cliff blossom grove and cliff lip | no |
| h15 tee, approach, offL | sea round the island green | a wall of authored pines across the view + floating label | no: needs thinning authored trees (decision) |
| h08 greenBack | sea stacks with foam at the base | green edge drops below the camera's horizon | no |
| Wild Isles (most) | cove / lake glimpses | forest walls (13/14), snowbanks (17); several targets show water the course doesn't have in that direction | partly a target/course mismatch |
| Magma 10/16 | dark sea right | basalt columns and lava field fill the right | no |

**Trees are visual only** (HoleView adds colliders to ground meshes only; GolfCoastalInstances draws trees as instances with no physics), so thinning a few pines off the corridor would not change play. They are still authored course layout, and hiding them needs a patch to the shared GolfCoastalInstances. That makes it a decision for Adnan, not a look-layer change.

Candidate if approved: on h07 (right rough) and h15 (tee to island line), hide the course pines that stand more than (FairwayWidth / 2 + 20) yd off the corridor AND inside the tee camera's view cone toward the coast; ~6–12 trees per hole.
