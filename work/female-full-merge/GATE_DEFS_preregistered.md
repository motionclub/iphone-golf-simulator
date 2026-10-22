# Gate definitions - written BEFORE any seam number was computed (2026-10-02)

Scope: merge only. Nothing here may be tuned after seeing a result; if a definition turns out to be wrong it is changed in a
dated "AMENDMENT" block at the bottom with the reason, never silently.

## Provenance model used for the vmap / conflicts
* ArtDir `HeroBase_Female.blend` (200dc3b9, 22,444 verts) -> hands base (23,247 verts): ArtDir idx -> base idx through the limbs
  vertex map `work/female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz` (`base_to_final`, -1 = removed old SDF hand/foot verts).
  Base indices 0..22,418 keep the limbs order; 22,419..23,246 are the 828 appended hand verts.
* A FORM5 delta vertex is CLEAN if the base position == the delta `start_co` (bit exact float32), SUPERSEDED if the base position ==
  chat 7's torso position (`work/female-parallel-torso/export/torso_delta.npz` new_co), CONFLICT otherwise (anything else = a real
  overlap with arms/hands/limbs = STOP).

## Seam "step" (SEAMS gate) - two numbers per ring, both reported
1. POSITION_STEP: for every ring vertex, max |position in merged mesh - position the OTHER piece(s) expect for it| (pins stay pins => must be 0.000 mm).
2. DISPLACEMENT_STEP (FORM5's own SEAM_CLEAN convention): max over ring-crossing edges (r in ring, w not in ring) of
   | (P_w - P_r)_merged - (P_w - P_r)_before |, i.e. how much the merge deformed the edges that cross the ring; `before` = the hands base
   (or the ArtDir original where the base is chat-7-contaminated). For the head collar ring the head piece is a REPLACEMENT (no index
   counterpart), so there DISPLACEMENT_STEP := max distance from each head-piece vertex directly connected to the ring to the ORIGINAL
   ArtDir surface it replaced (closest point on the ArtDir head/neck triangles) - reported as COLLAR_OFFSET_MM.
NECK_STEP_MM := max(POSITION_STEP at neck rings, DISPLACEMENT_STEP of the FORM5 neck/shoulder ring, COLLAR_OFFSET_MM).
NECK_WELD FAILS if NECK_STEP_MM > 2.0 mm. Whatever the number is, it is recorded; nothing is moved to reduce it.
Rings: neck = FORM5 neck/shoulder border ring (72 verts, z ~1.35-1.37) + the collar ring (30 verts, z 1.3965-1.4053);
armpit = FORM5 arm-junction border (62 verts) vs the arms pins (107); wrist = 36 wrist-ring verts; leg-top = FORM5 floor ring (88 verts, z .62).

## Topology (TOPOLOGY gate)
Body_F boundary edges, non-manifold edges, hand-vs-body triangle intersections (BVH overlap, non-adjacent triangles) compared with the hands base.
Boundary edges that are IN THE SOURCE PIECES (F3's two 128-edge eye openings, covered by Face_F) are reported separately from edges the merge created.
The literal count is always printed; the verdict line says exactly which reading was applied.

## HEAD_ZONE_ONLY
Merged vertices/faces outside the old-head zone (base verts z > 1.40545) are the base's (after the torso delta). The only faces taken from F3 are its
head-zone faces (any vertex above its 30-vert collar ring). F3's lower body (12,421 verts, identical to ArtDir) is NOT copied; it is checked against the base.

## Never done here
No resculpt, no remesh, no densify, no neck slimming, no ArtDir write, no Unity, no clothes, no male.

## AMENDMENT 1 (2026-10-02, after the first seam run; no verdict depends on it)
* The ring sizes quoted above (72 neck / 62 armpit) were counted with a z threshold (z>1.3). The OPERATIONAL classes in `tools/verify_seams.py` are by adjacency to the arms zone:
  neck = FORM5 border vertices not adjacent to the arm zone with z>1.3 (45), armpit = border vertices adjacent to the arm zone (81), floor = |z-.62|<.01 (88), 8 further border vertices (z<=1.3, not adjacent to the arm zone).
  This classification reproduces FORM5's own SEAM_CLEAN numbers (0.57 / 9.42 / 1.35). `tools/verify_ring_classes.py` (data/ring_classes.json) shows the z-based classes give the SAME steps
  (neck 0.567, rest 9.415, floor 1.353; the 8 extra border vertices 0.933), so the choice cannot change the NECK_WELD verdict.
* "head-piece vertex directly connected to the collar ring" = graph distance 1 from the 30 collar vertices = 60 head vertices (row 1). COLLAR_OFFSET_MM = the largest closest-point distance of those 60 to the
  ORIGINAL ArtDir head+neck surface (10,417 triangles). Rows 2-6 and the front-contour slope change are reported as supporting evidence only.
