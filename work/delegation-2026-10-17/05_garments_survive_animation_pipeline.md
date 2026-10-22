# Chat 5 — Clothes that never break in animation + a fast pipeline for new skins/clothes

You are one of 5 parallel chats in this repo; see `work/delegation-2026-10-17/README.md` for who owns what. Read `AGENTS.md` and `CLAUDE.md` first, then `work/clothing-v2/README.md`, `work/female-soulful/CURRENT_STATUS.md` + `GATE_RESULTS.md`, `HANDOFF_CODEX_TO_CLAUDE.md`, `work/cloth-overhaul/REPORT.md`, `work/emote-standard/CLIPPING_AUDIT.md`, and the memory notes `clothing-v2-all-heroes`, `clothing-v2-fixes-shoes-straps`, `clothing-v2-polo-pipeline`, `female-shirt-fixes-2026-10-16`, `herobase-female-custom-normal-offsets` and `anim-deformity-breakdown`.

## Goal (one system, two results)
Adnan: "make sure clothes don't break on animations" **and** "when we are creating new skins and clothes it doesn't take a super long time to figure out how to fit animations around it."
- **A.** Every current garment on all 4 heroes (male/female tennis, male/female golf) survives every clip with no tears, pokes, shredding or layer fights.
- **B.** A new garment or skin goes from mesh to "passes every animation" in **≤ 30 minutes** with one command and no hand-written binding script.
The fix for A has to *be* the B pipeline. Don't make another garment-specific binder.

## Added 10-17: match the reference images
Adnan: "combine with this chat working on clothes and getting them closer to ref images, especially girl tennis shirts. then [...] improving [the male characters'] clothes and their fit, especially shoes — the shoes for tennis and golf are super far off of what they need to be."
- **Female:** bring every female garment closer to `ArtDir/style/alive/neutral-reference-pack-2026-10-15`. The **tennis top comes first**: sheets 01, 02, 09 and S3 (clothes-with-weight); golf 03/04/10; skorts 11; shoes 12. Shape, fit, construction, seams, hem/armhole and fabric weight/material (you also own `TennisCloth`). Colours stay customizable.
- **Male:** chat 7 (`female-face-shader`) is making a male reference pack at `ArtDir/style/alive/male-reference-pack-2026-10-17/` with tennis-shoe and golf-shoe detail sheets. When it says the pack is accepted, fit all male garments to it. **Shoes are the top priority.** Until then, start the shoes from `ArtDir/hero/targets-2026-10-13/clothing-v2-fixes/05_shoes_ref.jpg` plus real tennis and golf shoe construction (outsole, midsole, upper panels, heel counter, toe box, lacing; golf spikes).
- Gate REF_MATCH per garment: matched-view overlays/side-by-sides against the governing sheet, Adnan-reviewed.
- Everything goes through your general pipeline. Reference matching must not add per-garment binders.

## Known state
- Tears at armpit/shoulder blade/side seam on arm-up and trunk-fold motions; Scuba shreds the shorts seat and polo hem; the golf shirt tears above the belt; the skirt fails in floor poses/kneels/lunges; the male polo armpit poke was barely improved (1363 → ~1256).
- Each fix so far was a one-off binder (`bind_polo_harmonic.py`, `bind_tank_follow.py`) that cost hours. Root causes found: weights copied from the wrong panel/layer; hard Neck 1.0 steps; chest skin carries 16–21 % UpperArm weight while the top was torso-only; the body cover mask removes rest-space skin that's needed when arms move (untested hypothesis).
- Rejected: DQ skinning on the tank (armhole wings), CPU per-vertex projection (destroyed layers, 64–69 ms), partial follow 0.6.
- The female polo/tank fixes from 10-16 are **staged, not installed**. Start from them, not from production.
- Full export + cover + maps + Unity takes 40–60 min. The 5 s fast loop (`work/clothing-v2/scratch2/server.py`) is shape only.

## Do
1. **Stress pose library.** From every clip (tennis, golf, plaza, emotes) and both heroes, auto-extract the worst frames per region: axilla, shoulder blade, side seam, waist/belt, seat/hip fold, kneel/lunge, arms crossed, overhead. Save them as a compact pose set (~100–200 poses) that Blender headless can load. This is the test suite.
2. **General binding method**, the same code for every garment:
   - Transfer weights from the *full* body (not the cover-trimmed one), with panel/layer awareness (lining follows its own shell panel) and graph smoothing (no hard steps).
   - Pose-space correctives auto-generated from the stress set: solve garment-vs-body clearance per pose, then fit shape keys/blend-shape correctives driven by joint angles. Use the GPU/cheap runtime only if it fits the budget.
   - Revisit the cover mask: hide only skin that's covered in *every* stress pose.
   - Layer ordering: outer garment stays outside inner (top over shorts/skirt, socks under shoes).
3. **One command:** `garment_fit <garment mesh or builder design> <hero>` → bind → correctives → stress-suite render + metrics → PASS/FAIL report + contact sheet of the worst 12 poses. Blender headless, warm server, parallel. Then one more command installs into Unity and native SceneKit (cover, maps, lobby `.ktx` via `compress_maps.py`).
4. **Apply it to all current garments** for A. Show Adnan worst-pose before vs after for the male polo first, then the rest.
5. **Prove B:** take a garment that wasn't in the set (e.g. a new tee or hoodie variant from `polo2.py`/`tank2.py`, or a long-sleeve) through the pipeline from scratch, timing it with a wall clock.
6. **Document** `work/clothing-v2/GARMENT_PIPELINE.md`: how to add a new skin or garment, what to run, and how to read the report.
7. If chat 3 (hand clearance) wants per-garment body offsets, write them to a manifest the pipeline emits (agree on the format via REQUESTS.md).

## Preserve
Body/head/face/hair/skin assets, body bindings, rig and source clips, lights, cameras and maps. Garment look in bind pose: shape, seams, fabric. Customizable colours and saved selections (check light, dark and saturated swatches).

## You own
`work/clothing-v2/**` builders/binders/pipeline, garment meshes and their correctives, cover masks, `ClothingV2Install.cs`, `MatchHeroLook` kitV2Covered logic, and garment materials only where binding needs it. Not body skinning, clips, `HeroPoseSafety` or skies.

## Gates (work/clothing-v2/pipeline/GATE_RESULTS.md, binary)
- TEARS: 0 body-skin pixels through any garment, above the noise threshold, in every stress pose × 4 heroes × all garments; plus a live check on 5 filmed clips per hero.
- LAYERS: edge-crossings between garments vs the reference pose ≤ threshold in all stress poses.
- SHAPE: bind-pose garment silhouette change ≤ 3 mm vs current staged garments.
- COLOURS: light/dark/saturated swatches render correctly; saved selections load.
- PERF: runtime cost of correctives ≤ 0.3 ms per hero (Editor profiler).
- NATIVE: SceneKit lobby renders match Unity at 3 poses per hero (or the reason it can't yet).
- NEW_GARMENT_30MIN: an untouched new garment goes from mesh to PASS report in ≤ 30 min wall clock, with zero new code.
- DOC: GARMENT_PIPELINE.md lets a fresh chat fit a garment (dry-run by following it literally).

## Rules
Branch `10/13`, big pre-existing staged index: preserve it. Stage only your reviewed files; no commits, resets or broad `git add`. Unity only in your own APFS clone (`cp -cR Unity /private/tmp/garments-UnityClone`, copy `Library/` too, see pitfalls), one Editor, `GOLF_MUTE=1`. Headless Blender, not the MCP. Disk ~38 GB: keep proof small and delete nothing that isn't yours. Install into `Unity/` only files you own; hero prefabs go as a patch plus install script to chat 6. Push proof images to Adnan every ~15–20 min. Needs from other chats go in `work/delegation-2026-10-17/REQUESTS.md`.
