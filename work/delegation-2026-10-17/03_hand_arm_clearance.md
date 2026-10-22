# Chat 3 — Hands, arms and racket never go through bodies or clothes

You are one of 5 parallel chats in this repo; see `work/delegation-2026-10-17/README.md` for who owns what. Read `AGENTS.md` and `CLAUDE.md` first, then `work/animation-safety-20261015/HANDOFF.md`, `phase2/PLAN.md`, `phase2/proof/GATE_RESULTS.md`, `work/emote-standard/CLIPPING_AUDIT.md`, and the memory notes `anim-deformity-breakdown`, `emote-clipping-audit` and `emote-overhaul-build` (it has a body-clearance engine).

## Goal
Adnan: "need to figure out how to make sure hands/arms do not go through clothes/bodies." This needs **one general system**, not per-clip hand fixes: it works for every clip in tennis, golf, plaza and the lobby, both heroes, and **any garment, including future ones, without re-tuning**.

## Known state
- `Unity/Assets/Scripts/Tennis/HeroPoseSafety.cs` uses six bone-local ellipsoids for the torso/head, moves elbows and keeps wrists locked. The last sweep still had 85 male and 12 female poses over 1 mm. It's approximate, ignores thighs/hips/head detail/garments, and is not used by the lobby.
- Measured problems: hands sink into thighs/hips/shorts in almost every low-hands clip (Free Walk/Run every stride; Slump/Defeat hands vanish); Shock fingers go into the scalp; two-hand grips interpenetrate; the racket goes into the leg/skirt; forearms go through the polo.
- `emote-overhaul` has a bake-time body-clearance engine (arms never through the body) that may be reusable.
- Pitfalls: forearm twist bones are `ArmBlend_*`, so exclude the whole own arm in self tests; BakeMesh garments ≠ rendered garments; the runtime body has covered skin removed (use the full body, `kitV2CoverSource`).

## Do
1. **Collision proxy built automatically** from the skinned body mesh: capsules/ellipsoids per bone (torso, pelvis, thighs, shins, head, neck, upper arms) fitted at load or import. Garments add an offset per proxy, computed from the garment mesh's distance to the body. No hand-tuned numbers per garment. If chat 5 provides a garment offset manifest, read it; otherwise compute the offset.
2. **Solver:** resolve hand, forearm, upper-arm and held-prop (racket/club) penetration against the proxy, including hand-vs-hand and prop-vs-body. Keep what matters: racket/club contact position and time, two-hand grip relationships, planted-hand contacts that are meant to touch (hands on knees, a clap). Move the elbow/shoulder chain with IK and keep segment lengths; never flip elbows or snap. Smooth the correction over time so it doesn't pop.
3. **Two outputs from one solver:** a runtime pass (cheap, after animation, before render) and an **offline bake** that writes corrected clips. The SceneKit lobby can't run Unity code, so it gets baked tracks. Chat 6 does the actual lobby re-export; you give it a working bake entry point.
4. **Audit tool:** extend `AnimationSafetyAudit` into one command that sweeps every clip × hero × kit at 60 Hz and reports penetration depth per body part and per garment outer surface, plus contact drift. Use it for before/after.
5. Show Adnan the worst 20 poses before vs after early. Then do the full sweep.

## You own
`HeroPoseSafety.cs` (rework it or replace it), new proxy/solver/bake files, `AnimationSafetyAudit*` tools, and the wiring that calls the solver from tennis/golf/plaza pose pipelines. Not source clips (chat 4 tennis, chat 1 others), `HeroGripPolish` finger shaping (chat 4), garment meshes/bindings (chat 5), or the lobby exporter rate (chat 1).

## Gates (work/hand-clearance/GATE_RESULTS.md, binary)
- BODY: across all clips × both heroes × all kits, 0 frames with hand/forearm/prop penetration > 3 mm into the full body.
- CLOTH: 0 frames with hand/forearm/prop > 3 mm inside a garment's outer surface (excluding intended contact, e.g. hand on hip, listed per clip).
- CONTACT: racket/club position at contact within 1 cm, and contact time unchanged, vs baseline.
- NO_POP: no elbow/shoulder angular velocity spike > 2× the clip's own peak introduced by the solver; no elbow flips.
- NEW_GARMENT: swap in a garment you never tuned for (e.g. scale a top outward by 1 cm), rerun, and CLOTH still passes with zero code/number changes.
- COST: runtime pass ≤ 0.3 ms per hero (Editor profiler, report the device estimate).
- BAKE: baked clip = runtime result within 2 mm on 3 sample clips.
- Visual: worst-20 before/after sheet, plus filmed in-game tennis rally, golf swing and 3 emotes.

## Rules
Branch `10/13`, big pre-existing staged index: preserve it. Stage only your reviewed files; no commits, resets or broad `git add`. Unity only in your own APFS clone (`cp -cR Unity /private/tmp/clearance-UnityClone`), one Editor, `GOLF_MUTE=1`. Headless Blender, not the MCP. Disk ~38 GB: keep proof small and delete nothing that isn't yours. Install into `Unity/` only files you own; shared prefabs/scenes go as a patch plus install script to chat 6. Push proof images to Adnan every ~15–20 min. Needs from other chats go in `work/delegation-2026-10-17/REQUESTS.md`.
