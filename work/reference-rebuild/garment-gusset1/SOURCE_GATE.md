# Underarm gusset — integration-ready source candidate

GATE: source topology and new-interior-hole audit PASS. Whole-motion visual approval remains provisional pending actual Unity full/LOD shader review. No Assets edits were made by this task.

## Final measured result

| Detail | Source → resulting vertices | Source → resulting triangles | Audit views | New interior-hole views | Forehand1 target pixels | Regional visible Body total |
|---|---:|---:|---:|---:|---:|---:|
| Full | 13,932 → 18,401 | 19,408 → 27,470 | 330 | 0 | 411 → 1 | 30,864 → 7,159 |
| LOD | 11,533 → 15,989 | 15,914 → 23,946 | 330 | 0 | 411 → 1 | 30,587 → 7,183 |

Both output meshes have zero welded open edges and zero welded nonmanifold edges. All existing vertices and their skin weights stay unchanged at rest; added points interpolate the original source face attributes and weights. Physical UV aliases have identical weights (maximum weight difference 0). The small Body proxy reconstructs exact posed points to within 0.00032 mm in the independent bone-local contract check.

Forehand1 has zero new skin and zero new background pixels in both views at both detail levels; only one original target pixel remains in the front source raster. The raised-arm EmoteSpike1, Serve4, and CelebratePoint1 samples have no new interior holes in either view. All 33 clips × five samples × two views were checked per detail, with corrected front-face winding and original Body mask2.

Regional skin counts also include legitimate cuff/edge skin visible in front of distant garment surfaces, so the remaining totals are not a count of surviving tears. They still require actual visual adjudication. Largest newly exposed skin changes are 43 full / 33 LOD pixels in EmoteScuba2 rear; this clip is included in the targeted capture config. Max new background is 555 full / 558 LOD pixels, mainly exterior contour changes, not interior holes.

## Concrete implementation

- `HeroGarmentGusset.cs`: self-installing opt-in helper, independent per-renderer mesh, exact source basis/topology/bone validation, separate full and LOD contracts, final-pose application after original sleeve anchor weights.
- `UnderarmGusset_Female_Full.json` and `lod/UnderarmGusset_Female_LOD.json`: full serialized subdivision, anatomical weights, pinned/free vertices, alias groups, contact triangles, and exact 104-vertex / 135-triangle skinned Body proxy.
- `INTEGRATION.md`: exact single-line hook, solver contract, runtime limitations, and native-parity requirements.
- `capture-targeted.json`: full/LOD actual capture of the target, raised arms, formerly flagged one-pixel cases, and EmoteScuba.
- `capture-motion-after-targeted.json`: dense all-clip follow-up after the targeted visual gate.
- Detail folders each contain source audit, topology report, and exact Forehand1/EmoteSpike1 posed oracles.

The C# compiles cleanly against the installed project version Unity 6000.3.24f1 CoreModule and JSONSerializeModule assemblies. Runtime execution, GPU normals/shading, dense motion between the five canonical samples, and performance have not yet been certified. Physical-phone checks remain deferred as directed.

## Provenance and reproduction

Canonical source: `proof/reference-rebuild/character-motion-matrices17/poses/female_intro.json`; canonical motion matrices are the 165 female files beside it. LOD source: `proof/reference-rebuild/underarm-fit2-lod/poses/female_intro.json`, 11,533 Top vertices. Existing original ten SleeveFit anchors are transferred to LOD with the same aligned nearest-source rule; maximum bind-space transfer distance 8.89 mm.

The source author corrected physical UV-copy edge synchronization before final export; earlier dense and unsynchronized results are superseded. No broad retopology, nearest-Body weight transfer, new Body mask, camera-specific displacement, or per-frame full Body baking is used. The local solver is pose-driven and stateless.

```sh
python3 work/reference-rebuild/garment-gusset1/author_patch.py
python3 work/reference-rebuild/garment-gusset1/check_patch_contact.py --all
python3 work/reference-rebuild/garment-gusset1/export_contract.py
GUSSET_LOD=1 python3 work/reference-rebuild/garment-gusset1/author_patch.py
GUSSET_LOD=1 python3 work/reference-rebuild/garment-gusset1/check_patch_contact.py --all
GUSSET_LOD=1 python3 work/reference-rebuild/garment-gusset1/export_contract.py
```

## Final file hashes

- `HeroGarmentGusset.cs`: `b9d3096def5cf8dbdd2a4c72ef907f50c94cab641c00a08020c9da88fa0952e8`
- `UnderarmGusset_Female_Full.json`: `755a116fa63aed465ae56ac43f10545c1652e8ed4f8530fec04a44ab16698b87`
- `lod/UnderarmGusset_Female_LOD.json`: `ffb3c0f2d858ec115ef1a1d824c53cf14b6b9b485b2e5651b65c572f3d94b607`
