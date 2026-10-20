"""write export/README_MERGE.md and copy merge script (called by finalize)"""
import sys, hashlib, shutil, os
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form4/tools')
from torso4 import WD
sha=lambda p: hashlib.sha256(open(p,'rb').read()).hexdigest()
ROOT=WD.parent.parent
blend=WD/'export/HeroBase_Female_torso_form4_candidate.blend'; delta=WD/'export/torso_form4_delta.npz'
art=ROOT/'ArtDir/hero/base_lock/blender/HeroBase_Female.blend'
txt=f"""# Merging the female torso FORM4 zone (bust primary + glute hold)

Delta is relative to the ORIGINAL start `HeroBase_Female.blend` SHA `200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd` (22,444 verts).
It **supersedes** FORM3's `torso_form3_delta.npz`, FORM2's `torso_form2_delta.npz` and chat 7's `torso_delta.npz` - apply exactly ONE of them (never stack).

`torso_form4_delta.npz` (SHA `{sha(delta)[:16]}...`): `moved_idx`, `start_co` (original float32), `new_co`, `zone_mask` (chat 7's 3,320-vertex torso mask), `vertex_count`.
The 238 zone border vertices (neck / arm junction / leg tops) are NOT in the delta: they stay bit-identical to the original, which the arms/legs/neck seams rely on.

Staged candidate: `HeroBase_Female_torso_form4_candidate.blend` SHA `{sha(blend)[:16]}...` (= ArtDir blend + this delta, vertex arrays bit-identical - verified).
ArtDir `HeroBase_Female.blend` is still `{sha(art)[:16]}...` : NOTHING was installed. Install only after Adnan's eye PASS.

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
# same vertex order as ArtDir (22,444): tested on a copy of the ArtDir blend -> 3,082 applied, 0 conflicts, vertex arrays bit-identical to the staged candidate (audit/merge_verify.json)
$B -b <target.blend> --python export/merge_torso_delta.py -- export/torso_form4_delta.npz <out>.blend
# limbs-chat vertex order (22,419):
$B -b <limbs-order.blend> --python export/merge_torso_delta.py -- export/torso_form4_delta.npz <out>.blend \\
   --vmap work/female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz
# a target that already carries chat 7's / FORM2's / FORM3's torso (e.g. the arms candidate) needs --force (its torso verts are not at the original positions)
```
* Each delta vertex must still be at its original position in the target (float32 exact); otherwise the vertex is reported and skipped (`--force` overwrites).
* Never run "clear custom split normals" on `Body_F`; positions only, the authored normal codes follow the geometry.
* Install rule: only one chat writes ArtDir at a time. After installing re-run the other chats' outside-zone audits and `tools/make_final4.py`-style audit; re-check the armpit seam against the arms candidate (`proof/10_armpit_seam_check_merged.png` shows it on `export/PREVIEW_form4_torso_plus_limbs_plus_arms_UNOFFICIAL.blend`, UNOFFICIAL preview: the arms chat faired its armpit against chat 7's torso, so the first interior ring differs).
* Rebuild from scratch: `bash finalize4.sh data/P_final4.json data/P_glute4.json` (chest params + pelvis/glute params; blend, delta, audits, gates, proofs, preview, results).
* Also exported: `form4_params.json` (+`_full`), `form4_params_glute.json` (+`_full`), `form4_wall_corrections.npy` (rows: chest dF,dB, glute dF,dB).
"""
open(WD/'export/README_MERGE.md','w').write(txt); print('README_MERGE written')
