# TENNIS_SHOES_FIT - gate definitions (written BEFORE the final measurement run)

Bodies (measured, never edited): male `work/male-pelvis-form3/export/merged_fd04bc28.blend` SHA d6c4dcfb..., female `work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend` SHA a1d73a33...
Start kit: `StandardKit_Male.blend` ad07a7b9..., `StandardKit_Female.blend` f19a9c03... (copies in `start/`, outputs in `export/`).
All numbers are measured on the ASSEMBLED output blends (objects as stored, world transforms applied), in body space (metres, Z up, toes toward -Y).
Colourways: the geometry is shared by White and Black, but every test reads both colourways' objects.

| gate | definition (PASS needs all lines) |
|---|---|
| FOOT_INSIDE | per hero, per foot: body vertices of that leg with z < the LOWEST point of the shoe collar rim ("below the collar"): (a) generalised winding number of the shoe mesh at the vertex < 0.5 (not inside shoe material); (b) 16-azimuth x 5-elevation enclosure rays (straight down, -60, -35, -15, 0 deg) ALL hit the shoe (exact Moller-Trumbore re-check of every BVH miss) = enclosed; count of vertices failing (a) or (b) must be 0. (c) minimum distance foot skin -> shoe surface >= 3.0 mm ("inner wall about 3 mm off the skin"). (d) triangle-level BVH overlap foot vs shoe = 0 pairs. Same (a)(b)(d) for the sock vertices below the collar. |
| TOE_COVERED | along the foot's own axis (PCA of the footprint, toe-out measured per foot): inner wall of the upper reaches past the longest toe tip by >= 5 mm and the outside of the toe box by >= 10 mm; AND camera-ray test: no foot-skin sample (z < sock top) is reachable from any camera ray within +-60 deg of the foot axis (front half-space, elevations -10..45 deg). |
| HEEL_COVERED | same along the foot axis behind the heel point (inner >= 5 mm, outer >= 10 mm) and camera-ray test from behind. |
| NO_SKIN_GAP | every skin triangle-centroid of both legs with z < (sock top - 4 mm) is hidden from 24 azimuths x 5 elevations (-10, 0, 10, 25, 45 deg) by shoe or sock (1 mm beam, exact ray-triangle) = 0 exposed samples; AND the sock continues above the collar rim by >= 20 mm at every azimuth of the rim and passes down through the collar into the shoe (sock vertices both above and below every rim sample) -> reported as sock-to-collar overlap (min over the rim). |
| SOLE_GROUNDED | lowest z of the left sole (tag sole) = lowest z of the right sole within 0.1 mm; lowest z of the whole shoe (tread) equal within 0.1 mm; every sole vertex z >= that plane - 0.1 mm. |
| MIRROR | reflect the right shoe across x = 0: symmetric Hausdorff distance to the left shoe <= 0.01 mm; both shoes closed with positive signed volume (outward windings); left is NOT a translated copy of the right (Hausdorff(right + best translation, left) > 1 mm). Same length / same sole height reported. |
| OTHER_PIECES_UNCHANGED | per colourway and hero: SHA-256 of the polo mesh and of the bottom mesh (vertex float32 bytes, polygon vertex indices, material indices, UV, loop normals, face attributes) is identical in start and output blend; polo/bottom objects keep names, parents, transforms. |
| BODY_UNCHANGED | SHA-256 of both body blends identical before and after the job; the FitRef copy in each output blend is vertex-identical to the source body mesh. |
| ON_THESE_FEET | build and checks verify the two body SHAs above; positive control: the START kit measured the same way on these bodies (female must FAIL FOOT_INSIDE, proving the test sees the old fit); nothing in the pipeline reads 200dc3b9 / the arms candidate. |
| NO_ARMS_CAND | no object, mesh, material or collection whose name contains ArmsCand in either output blend. |
| SOCKETS | Kit_Shoe_L/Kit_Sock_L parent = Foot_L_Shoe_<colour>, Kit_Shoe_R/Kit_Sock_R parent = Foot_R_Shoe_<colour> (socket_name Foot_L_Shoe / Foot_R_Shoe); sockets have an identity world transform; the meshes have an identity world transform; no armature / foot bone is moved (none exists). |

Sock note: the whole sock mesh is rebuilt (the start female sock stood up to 63 mm off the new legs and the male sock is rebuilt bit-identically); the cuff is part of it.

---
## Disclosed refinement (added AFTER the first measurement run; the text above is unchanged)
First run, female: NO_SKIN_GAP found 244 exposed skin samples of 220,762 ray tests. All 244 lie 6.0-17.8 mm BELOW THE TOP EDGE OF THE SOCK (z 0.2689-0.2807), seen from above (25 and 45 deg elevation) through the
open end of the sock tube down the 3-4 mm gap between leg and cuff (ray traced: it never meets the sock, it runs inside the gap). That is the open end of a sock, not a bare band at the shoe.
The zone is therefore narrowed from `z < sock top - 4 mm` to `z < sock top - 30 mm` (everything from the sole to below the 26 mm cuff band, which contains the whole ankle / collar / shoe region).
The cuff band itself is reported separately as informational (`skin_visibility_cuff_band`): skin seen only through the open top edge, never next to the shoe.
