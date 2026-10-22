# Coastal botanical pilot gate

GATE: Original procedural pilot1 appearance FAIL. The real showcase055 exposed large angular broadleaf triangles rather than needles. Full source foliage cost was 8,067,692 near / 2,084,870 far triangles. Closed topology did not certify appearance. That source is superseded.

GATE: Artist-derived source adaptation CANDIDATE. The installed kit now uses the native CC0 Poly Haven Fir Sapling Medium, Fir Tree01, Shrub02 and Fern02 geometry and maps. Verified source files/MD5 and credits are documented in ArtDir/golf/vendor. Artist needle UV coverage and shape are retained; corner-domain realized UV fields are converted into actual UV layers. Variant C has selected rotated native boughs to fill large canopy gaps. B/C dominate planted placement.

GATE: Near tree source budget PASS — A19,016 / B11,886 / C15,488 / D10,395 triangles, each below20k. Distant trees are four directional source bakes (eight triangles), with complete crown padding and no far shadow casting. Shrub clumps/fern use native textured stems and fronds. These source counts are not actual rendered frame cost or phone FPS.

GATE: Source visual proof CANDIDATE. Actual CPU near, far and understory proofs are in artist3/artist-final-{near,far,understory}.png. Needle scale is visible in artist-fir-branch-close.png. The selected evergreen forms remain naturally open; the reference's overall composition/material/lighting fidelity requires actual game review.

GATE: Original physics/source contract STATIC PRESERVED. The runtime uses exact already-extracted Tree/Bush pivots. Source MeshFilters/colliders/obstacles/Ground remain; only original TREES/SHRUBS/FLOWERS renderers are hidden. No botanical colliders are introduced. Actual regression remains root-owned.

GATE: URP runtime material/cost/art PENDING. New isolated GolfCoastalFoliage shader samples actual diffuse/normal maps and alpha clips forward, shadow, depth and depth-normal passes. The bounded olive tint, directional light and root SSAO must be judged in real game captures. Physical phone checks remain deferred by user instruction.

Canonical source: ArtDir/golf/source/CoastalBotany.blend. Canonical reproducible pipeline: ArtDir/golf/tools/rebuild-coastal-botany.py. Installed file hashes: ArtDir/golf/coastal-botany-manifest.json. No shared BotanicalKit or other venue changes.

## Actual pilot2 and next color candidate

GATE: Artist needle geometry/UV/material binding PASS in actual `proof/reference-rebuild/coastal-pilot2/hole12_showcase_055.png`: narrow textured compound needles and curved boughs replace the giant triangular leaves. Actual log confirms one original FLOWERS renderer hidden. Compile/shader gate passed in root's run. This does not certify full reference fidelity.

GATE: Reference color/shading FAIL in pilot2 — distant crowns remain too black/brown and shaded foliage lacks the reference's lively warm-green separation. Source sum is now 1,858,934 near / 338,774 far triangles (41 exact tree pivots,301 understory placements,42 crest pockets). The actual fixture audit measured3,188,149 triangles/465draws; source sums and actual submitted counts are different evidence.

Color candidate installed: native leaf brightness2.0/shrubs1.7, warm-green tint1.02/1.48/.75, bounded sky fill.14, shaded-needle transmission.28, broad sun backscatter/rim. Distant bakes have separate6× linear exposure compensation: their native median green was.019 linear vs needle texture.080, explaining the dark distant crowns. Texture contrast, alpha coverage, bark, plant geometry and original physics remain.

GATE: Actual color candidate3 FAIL against reference: real reference_camera2 and showcase055 show fluorescent lime foliage after exposure/tint lift. Needle detail and coverage remain coherent.

Color4 installed bounded correction: native leaf brightness1.7/shrubs1.55, tint1.10/1.20/.83, distant exposure4.6. Transmission/fill, geometry, textures and shadows remain as candidate3. Actual Color4 matching views reviewed at proof/reference-rebuild/coastal-colour4/hole12_{gameplay,reference_camera_2,showcase_055}.png. Bounded colour balance PASS: fluorescent lime removed, warm olive/deeper evergreen and small needle variation remain visible; no apparent clipped highlights. Overall reference fidelity remains PARTIAL: crowns are naturally more open/smaller in frame and crest is sparse versus target. No full course completion or physical phone performance claim.
