# DRESS_MATCH_HEROES - note (2026-10-03)

Installed: kit FBX `Assets/Characters/MatchHeroKit/{Male,Female}_Kit.fbx` (same armature as the clip FBXs), 7 role materials `Assets/Characters/MatchHeroes/Materials/Kit/`, 6 `Kit_*` SkinnedMeshRenderers on `PlayerMale/PlayerFemale.prefab`
bound by name to the prefab's own bones, `MatchHeroLook.SetKit(shirtHex, shortsHex, shoesHex)` (+ Color overload), one line in `HeroKit.Apply`, kit parts in the locker export (`MatchHero_*.json/.lzfse` regenerated, 51.5 MB vs ~22 MB),
Swift `MatchHero.kitTint / kitDerive / kitColour(role:player:)` inside `enum MatchHero` of CharacterModelPreview.swift. Roles: Kit_Shirt, Kit_ShirtTrim, Kit_Shorts, Kit_ShortsBand, Kit_Shoe, Kit_Sole, Kit_Sock.
Rebuild: `./run_all.sh` (Blender stage ~2 min, Unity chain, xcodegen + xcodebuild test/build, play-mode proof, `scripts/final_report.py` -> checks.json).
Pitfalls found: importer Animation Type None drops the skin (use Generic); the saved prefab hierarchy is in the pose of frame 0 of the clip FBX, not the bind pose (compare against mesh.vertices, not BakeMesh); the clips key the armature node
`Rig_<Hero>` itself, so the prefab cannot carry a ground lift; nearest-face weight transfer must only see the body surface the piece's bones own (the skirt looked up the hanging hand); heavy.sh locks are per scratchpad; an xcodebuild test can hang at teardown.
Open: (1) shoe soles are 30.8 mm (M) / 25.5 mm (F) below the court (ReadyIdle) - fix needs one line in HeroTennisDriver.PostProcess (`transform.localPosition = lungeOffset + up * soleLift`), not touched by order;
(2) skin-poke / float and sole-track numbers above the pre-registered thresholds (see checks.json, logs/tuning_log.md): male polo armpit, female polo sleeve slit (open kit seams; DR_WELD_EPS knob prepared, evaluated, not adopted), toe-box roof of the shoes in Serve / Overhead;
(3) `xcodebuild build` of the plain scheme was not run as a separate step (the 15 touched tests built and passed); (4) Play-mode rally/campaign proof frames exist in proof/unity but were not reviewed frame by frame.
