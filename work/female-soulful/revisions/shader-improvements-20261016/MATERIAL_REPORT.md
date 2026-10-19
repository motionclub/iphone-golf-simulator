# Female shader candidate — 2026-10-16

GATE: Native Swift compile PASS.
GATE: Native material shader execution PASS — eight actual SceneKit PNGs in `proof/combined-fixes/native-material-diagnostic/`; inspected clean tennis/golf textiles, cap, eyes and skin. Historical geometry and temporary explicit material metadata; see PROVENANCE.json. These are not final garment parity or gameplay captures.
GATE: Final Unity/native geometry parity FAIL — new garment export and matched final renders remain with the main task.
GATE: Reference appearance NOT ACCEPTED — original face and chosen complexion remain; broad satin/material separation improved, but generated reference has different geometry, pigment and light. User appearance judgment remains necessary.

Source changes (this specialist only):
- Clone `Assets/Resources/Tennis/Shaders/HeroLighting.hlsl`, `HeroFaceSkin.shader`, `TennisCharacter.shader`, `TennisCloth.shader`; identical candidate mirrors under `work/female-soulful/unity/`.
- `GolfArcade/Unity/MatchHeroSurfaces.swift`. MatchHeroData.swift unchanged: optional femaleSurface already carries the required marker.
- Before backups and this report in `revisions/shader-improvements-20261016/`. No installation into production Unity, staging or commits by this specialist.

The female skin uses a broader controlled dielectric satin lobe, less camera fill and ambient, tighter diffuse wrap and no overall fixed tan grade. Registered pigment, lips, identity, face geometry and selected complexion remain. The existing eyes retain geometry, gaze, original albedo/catchlights; a female-only material marker selects the controlled corneal response. Female cloth uses rough diffuse plus soft grazing fibre response, derivative-filtered neutral cluster detail, and lighter cavity darkening. Existing fabric versions and IDs stay intact. Rubber uses existing sole edge data and receives no textile sheen. Golf cap marker 2 uses its existing trim mask to keep the white patch quiet while retaining construction seams.

The first full material candidate was rejected for overly coarse/mottled cloth. The refined candidate reduces noise to 3.5%, tightens it, filters it out at phone distance, reduces atlas slopes/thread contrast, and suppresses patch noise. Parent owns FemaleGarmentFinish parameters and Editor refresh/capture; shader clone/work mirrors are synchronized.

Male preservation was checked by static before-diff: original shared character shading functions and cloth Shade/Fabric/SoftShoulder remain intact; new branches require female markers (defaults 0), skinFinish>1.5 or the female material setup. The only shared numerical safety correction clamps Blink to nonnegative before fractional pow, matching its valid 0–1 range, and initializes an out parameter. No body/head/hair/rig/map/camera/light assets were edited.

Native harness build:
```
xcrun swiftc -swift-version 6 -O -parse-as-library -module-cache-path work/reference-rebuild/original-native-adoption1/module-cache /private/tmp/female-material-lobby-render.swift GolfArcade/Unity/MatchHeroData.swift GolfArcade/Unity/MatchHeroSurfaces.swift GolfArcade/Unity/MatchHeroMotion.swift -framework SceneKit -framework AppKit -framework Metal -o /private/tmp/female-material-lobby-render
```
Rendering requires Metal access outside the shell sandbox. Native declaration and cap mask transfer failures were discovered with actual renders, fixed, and all eight final images overwritten with clean results. Logs are retained. Final native behavior needs freshly exported runtime metadata and current garment geometry before claiming parity. Phone performance remains deferred.
