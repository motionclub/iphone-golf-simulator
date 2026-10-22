# DRESS_MATCH_HEROES - the match heroes wear the tennis kit

Job (2026-10-03): the two match heroes (HERO_MAINSTAY: `Body_M` / `Body_F` + painted face + classic racket on their own 53-bone skeleton) were bare mannequins. They now wear the White kit of
`work/tennis-shoes-fit/export/StandardKit_{Male,Female}.blend` (polo, shorts / skort + liner, two socks, two shoes), **skinned to their own skeleton** so it moves with all 16 clips, in the
Unity match / rivals / locker view and in the SwiftUI menu mirror, recolourable per role from the launch message. Bald stays. Rules, definitions, results:

| file | what |
|---|---|
| `GATE_DEFS_preregistered.md` | the 9 gates, written before the kit was measured on the skeleton; addenda A1-A9 are dated corrections made before the numbers they affect were used |
| `GATE_RESULTS.md`, `checks.json` | measured numbers per gate and the verdict |
| `NOTE_DRESS_MATCH_HEROES.md` | short note: what is installed where, rebuild, pitfalls, what is open |
| `run_all.sh` | one script that rebuilds and re-proves everything |
| `scripts/` | Blender (`build_dressed.py`, `measure_follow.py`, `check_skin.py`, ...), Unity stage wrappers, Swift stage wrapper, proofs |
| `export/` | `HeroBase_{Male,Female}_Dressed.blend` (the match-anim blend untouched + 6 skinned kit pieces), `{Male,Female}_Kit.fbx` (the Unity input) |
| `data/`, `logs/` | measurements (json), per-stage logs, `logs/tuning_log.md` = every weight configuration that was evaluated |
| `proof/` | Blender sheets, before / after, worst poses, `proof/unity/` (play mode), `proof/swift/` (the real SwiftUI view) |
| `baseline/` | hashes of the 32 clip FBXs and of every file edited, prefab fingerprints before / after, `orig/` copies of the edited files |

## How the kit is attached (decision D3, justification)

A NEW kit FBX per hero (`Male_Kit.fbx`, `Female_Kit.fbx`), exported from the match-anim blend with `Rig_<Hero>` (identical bones, hierarchy and rest pose; checked: 53 bones, head / tail error 0.0 mm against
the clip FBX) and the six kit meshes with an Armature modifier. `MatchHeroKit.Attach` (Unity editor) creates one `SkinnedMeshRenderer` per kit piece on the prefab and re-binds `bones[]` BY NAME to the
prefab's own bone transforms (the bindposes inside the kit mesh are the ones of that identical rest pose, so no re-computation is needed). Why this and not the alternatives:

* **Kit inside the 32 clip FBXs** would change every clip file (hash guard in `MatchHeroBuild`, the clip table, the 16 x 2 copies in Unity) and bake the kit into every clip import. Rejected: the brief forbids touching them.
* **Kit as rigid children of bones** (the `Chest_Top` / `Foot_L_Shoe` sockets the kit already has) fails for the polo, shorts and skort (they must deform with the torso, arms and thighs).
* **Humanoid retargeting / a second Animator** adds a second skeleton to keep in step; the match clips were deliberately imported Generic because Humanoid drifted.
* **Re-binding by name** costs nothing at run time (the kit renderers read the SAME bone transforms the body does, bound once at build), needs no new animation, and every clip, the driver, the replay and the locker export work unchanged.
  The import settings (`MatchHeroKitPostprocessor`) copy the body's: scale 1, no weld, custom skin weights <= 4 bones, normals imported; Generic rig (with *None* the importer drops the skin: found on the first build).

## Skinning (decision D2)

Weights are transferred by name from the hero's own body at the bind pose (nearest body face, barycentric interpolation = Blender Data Transfer "Nearest Face Interpolated"), with these evaluated refinements
(`logs/tuning_log.md` has the numbers of every one): a bone whitelist per piece (the polo may use trunk / shoulder / arm / thigh bones, the shorts hips / thighs / shins, a sock or shoe one side's shin / foot / toes),
nearest lookups restricted to the body surface those bones own (the skirt used to look up the hanging hand), per-side lookups in the leg region, cloth smoothing, an envelope (inverse-distance to the hips / thigh bones) for the female
skirt where it is far from the body, and for the shoes a Foot / Toes split read off the body's own weight profile along the foot axis. Then at most 4 influences, weights normalised. The kit geometry (positions, topology, custom
normals) is bit-identical to the staged kit (`check_skin.py`); only the seven role material slots and the vertex groups were added.

## Colour roles (the contract with the menu owner)

Materials, by exact name, on the kit renderers: `Kit_Shirt`, `Kit_ShirtTrim`, `Kit_Shorts`, `Kit_ShortsBand`, `Kit_Shoe`, `Kit_Sole`, `Kit_Sock`. Unity: `MatchHeroLook.SetKit(shirtHex, shortsHex, shoesHex)` (hex without `#`,
null / empty = authored White kit) or `SetKit(Color, Color, Color)` (alpha 0 = none); the Swift mirror recolours from `Player.outfitHex("shirt" / "shorts" / "accent")` with the same maths
(`MatchHero.kitTint`, `kitDerive`, `kitColour(role:player:)`). Maths (D6): `out = max(0.93 * pick, floor)` per channel (floor = the authored Black kit's albedo 0.035 / 0.035 / 0.040, so a near-black pick still shows folds);
the trim / band is the pick darkened 35 % when its luminance is >= 0.5, else lightened 35 % toward white, then tinted the same way. The waistband is black in the authored White kit and stays so until a shorts pick is made.
`Kit_Sole` and `Kit_Sock` are never touched.

## Where it is installed

Unity: `Assets/Characters/MatchHeroKit/{Male,Female}_Kit.fbx` (new), `Assets/Characters/MatchHeroes/Materials/Kit/*.mat` (7 new), `Resources/Tennis/Customization/PlayerMale|PlayerFemale.prefab` (+6 `Kit_*` renderers each),
`MatchHeroLook` (kit API), `HeroKit.Apply` (one line: `SetKit(s.Shirt, s.Shorts, s.Shoes)`), `MatchHeroBuild`, `MatchHeroLockerExport`, new editor files `MatchHeroKit.cs`, `MatchHeroKitTests.cs`, `MatchHeroKitProof.cs`,
`MatchHeroKitBaseline.cs`, `MatchHeroKitProbe.cs`. Swift: `GolfArcade/Unity/CharacterModelPreview.swift` (inside `enum MatchHero` only), `GolfArcade/Unity/CharacterAssets/MatchHero_*` (regenerated),
`GolfArcadeTests/DressedHeroSnapshotTests.swift` (new), `GolfArcadeTests/MatchHeroLockerTests.swift` (the part list now includes the kit).
