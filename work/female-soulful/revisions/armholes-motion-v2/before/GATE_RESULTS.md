# Implementation evidence

The user owns visual verification and requested images at each finished component. The expression requirements in START_HERE.md were superseded: retain the original face and restrained existing expressions.

- GATE: Original face/source preservation PASS — MatchHeroLook.cs, HeroFaceReferenceFit.cs and HeroFaceSkin.shader retain their original production hashes. No new mouth/teeth component.
- GATE: Separate garments PASS — four editable pattern-based Blender sources; separate top/bottom Unity meshes, approximately 19,800 triangles per piece.
- GATE: Game/native integration PASS — installed in the repository, including female native rig/morph exports and compressed maps. Original body/rig/clip assets, male assets, maps, cameras and lights preserved. No unexpected changes among 2,719 protected Unity files.
- GATE: Existing female regressions PASS — 17 passed, 0 failed, proof/female-tests-implemented.json. Native hero renderer compiles with the app's actual data/material/motion sources.
- GATE: Captured motion integration PASS — actual idle/wave/overhead celebration/recovery and full golf swing captured. Golf returned to Aim after 406 video frames, 627 flight simulation frames; 13.53 seconds, no audio, no flight compression. This is evidence of those observed motions, not a blanket no-clipping claim.

Appearance acceptance remains the user's judgment: proof/review/implemented-female-kits.jpg, polo-current.jpg, tennis-current.jpg, tennis-overhead.jpg and the muted comparison clips.

Phone performance was explicitly deferred by the user. Inherited body triangle count remains 68,476 rather than the nominal 35–50k target; identity was preserved instead of remeshing it. No target-device readiness claim.
