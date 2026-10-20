# Character + cloth shader pass (2026-10-03)
- Heroes' body, eyes (Sclera/Iris/IrisIn/Pupil/Limbal/Catch) and racket frame -> `GolfArcade/TennisCharacter`; kit (7 roles) -> new `GolfArcade/TennisCloth`. Done at runtime in `MatchHeroLook.OwnMaterials` (prefab assets stay URP Lit, MatchHeroKitTests unaffected). Roster tints still go to `_BaseColor`.
- One warm rim light `HeroRimLight` ("Hero rim", 1.8 vs sun 2.3, yaw 38 / elev 18 off the camera axis, follows Camera.main), created in `TennisLook.LightScene`.
- It sits on rendering layer 1 "Hero rim": needed `TennisURP.asset m_SupportsLightLayers: 1`, a layer defined in `ProjectSettings/TagManager.asset`, the mask set via `GetUniversalAdditionalLightData().renderingLayers` (Light.renderingLayerMask alone is ignored), hero renderers on layers 0+1, and `_LIGHT_LAYERS` tests in both shaders.
- Court check (same frame, rim on vs off): ~110-145 of ~480k court pixels differ, all at hero silhouette edges.
- Reproduce: `work/character-shader/run_stills.sh`, `python3 work/character-shader/diff.py <shot>`; proofs in `proof/`.
