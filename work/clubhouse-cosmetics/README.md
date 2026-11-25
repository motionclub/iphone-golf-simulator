# Clubhouse cosmetics — 2026-11-24

14 free locker choices: Icebreaker hockey stick, Home Run bat, Pop Hound balloon dog and Sugar Rush candy club; Orbit, Watermelon, Race Day and Sunset balls; Coastal Club, Arcade Nights and Citrus Rally outfit colour skins; Mint Condition, Neon League and Caramel Club accessory finishes. The outfit skins use existing garments; the accessory finishes use existing fitted caps, gloves and carry bags. Skin tone, face, hair, body, skeleton, animation sources, cameras and maps are preserved.

## Current authority

The user rejected the first plain designs and requested bold, over-the-top Fortnite-style gear, then required the existing golf animations and the same size. `concept-bold.png` is an **AI concept**, not game proof. Only `proof/` contains actual renderer captures.

Every club skin has Driver, Iron, Wedge and Putter variants, for both heroes. Each retains the original grip mesh and retains the corresponding original club's overall length and fits within its width/depth envelope, before and after the existing lie correction. Decorative heads are scaled uniformly to retain their proportions. No club-root scaling or animation retiming is used. Contact/arc queries bake the original club reference; novelty geometry is visual only. The new meshes have no colliders. The dimensions are relative to the original grip, not a new pivot.

## Equip

Locker → Golf → Club / Ball / Extras. Outfit palettes are under Skin, with existing Customize colour controls still available. Selecting an outfit palette deliberately sets shirt, lower garment and shoe colours; equipping equipment leaves those colours and identity alone. Picks use existing optional `Player.loadout` storage and stable IDs, with unknown IDs falling back to the existing defaults. Native launch explicitly transmits the three cosmetic fields that Unity reads. Multiplayer uses optional flat fields and retains the older three-slot gear dictionary for compatibility.

`party.hockey`, `party.slugger`, `party.balloon`, `party.candy`; `ball.orbit`, `ball.melon`, `ball.checker`, `ball.sunset`; `skin.coastal`, `skin.arcade`, `skin.citrus`; `extra.mint`, `extra.neon`, `extra.caramel`.

## Sources and rebuild

Powered by Poly Haven. The four scanned surfaces are [Fabric Pattern 07](https://polyhaven.com/a/fabric_pattern_07), [Brown Leather](https://polyhaven.com/a/brown_leather), [Metal Plate](https://polyhaven.com/a/metal_plate), and [Fine Grained Wood](https://polyhaven.com/a/fine_grained_wood), under [CC0](https://polyhaven.com/license). `sources/manifest.json` records download URLs, original SHA-256 hashes and derivations. Runtime assets are bundled offline; there is no game-time API request. The new club geometry and ball graphics are original procedural work.

Run from the repository root:

1. `python3 work/clubhouse-cosmetics/fetch_sources.py` — fetch the recorded 1k scans and derive 512px neutral detail maps.
2. Blender 5.2, `-b --factory-startup --python-exit-code 1 --python work/clubhouse-cosmetics/build_equipment.py` — generate four variants per style, native geometry, exact-rig FBXs, source blends, material definitions and size contracts.
3. `python3 work/clubhouse-cosmetics/compact_native.py`; `python3 work/clubhouse-cosmetics/build_balls.py`; `python3 work/clubhouse-cosmetics/validate_assets.py`.
4. Optional: Blender with `compact_sources.py` creates small standalone editable blend files from the generated club objects.
5. `python3 work/clubhouse-cosmetics/register_resources.py` registers new native resources in both existing Xcode projects.
6. Import into an isolated APFS Unity clone. Run `GolfArcade.EditorTools.PartyCosmeticsProof.Run` with `PARTY_PROOF_OUT` set to this folder's `proof` path; run EditMode `GolfArcade.Tests.PartyCosmeticsTests`.
7. `python3 work/clubhouse-cosmetics/make_sheet.py` assembles actual Unity render sheets. Native `LockerTests.testPartyShelfRendersBundledMeshesAndPatterns` records the real shelf thumbnails.

Do not rerun historical migration patch helpers. No commits were made. Existing unrelated working-tree changes are not part of this pack.

## Costs and limits

Per visible club: 3,220 / 3,400 / 13,832 / 9,376 triangles for Icebreaker / Home Run / Pop Hound / Sugar Rush. Geometry is shared through imported assets; material instances are cached by finish. Colour maps are 512px with mipmaps and iPhone ASTC 6×6, without crunch compression. These are asset budgets, not measured device FPS results. Physical-device performance and subjective user acceptance remain unmeasured.

See `GATE_RESULTS.md` for tested versus untested status. The app's Unity player export must be rebuilt to install the C# and shader changes on a physical iPhone; this work does not claim a device installation.
