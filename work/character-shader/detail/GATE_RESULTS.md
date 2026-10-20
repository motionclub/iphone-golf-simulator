# GATE HERO_DETAIL

- PASS  [match male] TennisCloth samples a weave normal + base (seam) map on every kit piece  (10 kit materials)
- PASS  [match male] thread break multiplied into the colour (thread>0) on every kit cloth
- PASS  [match male] shirt trim is dark (#09090A) and not the shirt white, smoothness ~0.25  (trim #09090A sm 0.250 | shirt #EDEDED | band #09090A)
- PASS  [match male] sole is darker and rougher than the upper  (sole #A8A6A1 sm 0.040 | upper #EDEDED sm 0.120)
- PASS  [match male] cloth smoothness <= 0.14 (dark trim excepted)  (max 0.12)
- PASS  [match male] skin smoothness ~0.2  (0.200)
- PASS  [match male] skin normal on and weak (0 < bump <= 0.25), wrap + subsurface unchanged  (bump 0.18 wrap 0.55 sss (0.18,0.06,0.03))
- PASS  [match male] eyes stay smoother than skin (~0.85), no weave / bump  (5 eye materials)
- PASS  [match male] brow / lid / lip / nostril / seam decals on TennisCharacter (no URP Lit), no weave, no bump  (8 decal materials)
- PASS  [match male] grip on TennisCloth, dark, rougher than the shirt  (grip sm 0.050 base #1C1C1F | shirt sm 0.100)
- PASS  [match male] strings on TennisCharacter, a touch smoother than the grip, no weave  (strings sm 0.150)
- PASS  [match male] nothing on either hero is still URP Lit  (0 Lit materials)
- PASS  [locker male] TennisCloth samples a weave normal + base (seam) map on every kit piece  (10 kit materials)
- PASS  [locker male] thread break multiplied into the colour (thread>0) on every kit cloth
- PASS  [locker male] shirt trim is dark (#09090A) and not the shirt white, smoothness ~0.25  (trim #09090A sm 0.250 | shirt #EDEDED | band #09090A)
- PASS  [locker male] sole is darker and rougher than the upper  (sole #A8A6A1 sm 0.040 | upper #EDEDED sm 0.120)
- PASS  [locker male] cloth smoothness <= 0.14 (dark trim excepted)  (max 0.12)
- PASS  [locker male] skin smoothness ~0.2  (0.200)
- PASS  [locker male] skin normal on and weak (0 < bump <= 0.25), wrap + subsurface unchanged  (bump 0.18 wrap 0.55 sss (0.18,0.06,0.03))
- PASS  [locker male] eyes stay smoother than skin (~0.85), no weave / bump  (5 eye materials)
- PASS  [locker male] brow / lid / lip / nostril / seam decals on TennisCharacter (no URP Lit), no weave, no bump  (8 decal materials)
- PASS  [locker male] grip on TennisCloth, dark, rougher than the shirt  (grip sm 0.050 base #1C1C1F | shirt sm 0.100)
- PASS  [locker male] strings on TennisCharacter, a touch smoother than the grip, no weave  (strings sm 0.150)
- PASS  [locker male] nothing on either hero is still URP Lit  (0 Lit materials)
- PASS  [locker female] TennisCloth samples a weave normal + base (seam) map on every kit piece  (10 kit materials)
- PASS  [locker female] thread break multiplied into the colour (thread>0) on every kit cloth
- PASS  [locker female] shirt trim is dark (#09090A) and not the shirt white, smoothness ~0.25  (trim #09090A sm 0.250 | shirt #EDEDED | band #09090A)
- PASS  [locker female] sole is darker and rougher than the upper  (sole #A8A6A1 sm 0.040 | upper #EDEDED sm 0.120)
- PASS  [locker female] cloth smoothness <= 0.14 (dark trim excepted)  (max 0.12)
- PASS  [locker female] skin smoothness ~0.2  (0.200)
- PASS  [locker female] skin normal on and weak (0 < bump <= 0.25), wrap + subsurface unchanged  (bump 0.18 wrap 0.55 sss (0.18,0.06,0.03))
- PASS  [locker female] eyes stay smoother than skin (~0.85), no weave / bump  (6 eye materials)
- PASS  [locker female] brow / lid / lip / nostril / seam decals on TennisCharacter (no URP Lit), no weave, no bump  (8 decal materials)
- PASS  [locker female] grip on TennisCloth, dark, rougher than the shirt  (grip sm 0.050 base #1C1C1F | shirt sm 0.100)
- PASS  [locker female] strings on TennisCharacter, a touch smoother than the grip, no weave  (strings sm 0.150)
- PASS  [locker female] nothing on either hero is still URP Lit  (0 Lit materials)
- PASS  TennisCloth: no bloom / toon ramp / outline in the shader
- PASS  TennisCharacter: no bloom / toon ramp / outline in the shader
- PASS  TennisCloth: the small hard Blinn dot is gone (exponent <= 30, peak <= 0.35*smoothness, sheen term present)
- PASS  TennisCloth: sheen is gated by the light (ndl) and shadow (atten) -> dead in shadow
- PASS  TennisCloth: samples the weave map and multiplies a thread break into the colour
- PASS  TennisURP.asset (post stack, bloom, light layers) + Serve / Walk / Run FBXs byte-identical to before  (0 changed of 11)
- PASS  all 16 clip FBXs x 2 heroes (+ .meta) under Characters/MatchHeroes byte-identical  (0 changed of 80 files)
- PASS  course files (Resources/Course, Scripts/Course): this pass writes none of them (23 files written by the pass, 0 in the course tree)  (also changed under the course tree during the run, by the parallel golf session: Unity/Assets/Scripts/Course/GolfLook.cs)

**GATE: HERO_DETAIL PASS** (44/44 lines)

## Evidence
- Before / after, same cameras, same frame set: `work/character-shader/proof/detail/SHEET_*.png` (single frames in `before/` and `after/`, in-game audit of every material in `after/report.txt`).
- Locker close-ups: male torso, female skort, shoe (both), face (both). Match: `SHEET_match_behind_game_camera.png` (the game camera behind the baseline) and `SHEET_match_behind_close.png`.
- Gate is rerunnable: `work/character-shader/detail/run_detail.sh after` then `python3 work/character-shader/detail/run_gates.py`. `MatchHeroKitTests` (changed: trim / sole authored colours) PASS for both heroes.

## Measured, with the caveats
- Skin highlight (interior skin patch, luminance, before -> after): forehead max 0.909 -> 0.844, p99 0.897 -> 0.835 (lower and broader: smoothness .35 -> .2 = exponent 39.6 -> 25.2, peak .21 -> .12). Cheek 0.641 -> 0.640. Two arm patches differ by +0.007 (p99, male forearm) and +0.013 (max, female upper arm): the weak normal adds diffuse variation and the pose differs by a few frames run to run; that is inside the run-to-run noise noted in the earlier pass, but it is not zero, so it is disclosed rather than called a clean win.
- White cloth average luminance on the close-ups: male torso 0.686 -> 0.685, skort 0.759 -> 0.766, shoe 0.630 -> 0.640 (the thread / seam multipliers are re-centred on 1, so the white stays white); local contrast on the cloth rises (that is the weave and the seams). No rim blow-out seen in the rim on/off pairs (`*_norim.png`), so the rim strength on cloth stays 0.2 and the Hero rim light was not retuned.

## What was NOT done / limits
- Swift SceneKit locker mirror (`CharacterModelPreview.swift`) still draws the old flat look; this pass is the Unity materials only.
- Not built for a device. Both shaders compile on Metal in the editor (no shader errors in the logs); ASTC overrides are set for iOS (4x4 weave / skin normal, 6x6 seam maps) but not measured on hardware.
- Weave grain follows the kit unwrap (the shirt's islands are turned ~45 deg, so its weave runs diagonally; trousers, socks, shoes are axis aligned). `_WeaveAngle` exists for a fix and is left 0.
- A shirt colour picked in the locker still derives its trim with the existing `KitDerive` rule (35 % darker / lighter than the pick); only the default White kit has the black #09090A piping. A pick of pure white gives grey piping, as before the pass.
- The seam / collar / hem maps are baked from the current kit meshes (`bake_kit.py`, `make_textures.py`). If the kit meshes change, rerun both and `HeroDetailSetup`.
