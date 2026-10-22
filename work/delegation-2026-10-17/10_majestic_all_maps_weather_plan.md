# Chat 10 — Majestic look on every map + top-quality weather: audit, reference images, plan

Adnan (10-17): "look at the recent finishes for the majestic maps, we need to perform this for all maps and make sure weather looks super high quality as well. spin up a chat to do an audit and create a plan to implement this across all maps, which requires creating ref images for all golf holes first then proceeding, also ref images for weather effects including each effect".

## Read first
- `AGENTS.md`, `CLAUDE.md`, `work/delegation-2026-10-17/README.md`, especially **"Sharing the machine"** (heavy.sh gate, SCHEDULE.md board, one heavy job at a time, no helpers that launch Unity/Blender).
- Chat 9's work: `work/majestic-maps-research/` (RESEARCH, FEASIBILITY, PROPOSAL, `concepts/`, `build/README.md`, `proof/`, `reference-board.html`), plus the memory note `majestic-maps-research`. The Majestic layer is INSTALLED for 6 places: Resort, Skyscraper, Volcano, golf hole 12 (Cliffside), Plaza, and one more; check build/README. Its concept targets were AI repaints of real game frames (Higgsfield `gpt_image_2_5`). Adnan wants it "exactly like the AI renders".
- Chat 2's rendered skies/clouds/scenery: `work/rendered-backgrounds/` and the memory note `rendered-backgrounds-2026-10-17`.
- Golf: memory notes `golf-three-courses-hole-flow` (3 courses, 5/6/5 holes), `golf-postcard-look-pass`, `golf-postcard-holes-8-9-10`, `golf-read-wind-lie-pass`. Weather: `GolfAtmosphere` weather cases, `Golf/StormSky.shader`, PR #27 weather shaders, chat 9's finding that golf weather is the biggest pixel cost (~+3 ms).
- The 60 fps at ≥1920×1080 floor (`work/frame-rate-60b/BUDGET.md`).

## Phase 1: Audit
- List every map/place in the game (all golf holes on every course, every tennis venue, plaza/hub, dream worlds) and every weather state each one can show (rain, storm, wind, fog, overcast, snow, golden hour, …, whatever the code supports).
- For each one, record whether it has a Majestic pass, what's missing vs chat 9's targets, current GPU cost, and the weather quality problems. Capture current frames: one batched muted Unity run through `heavy.sh unity`, booked on SCHEDULE.md. Reuse chat 9's captures where they're fresh, and ask chat 9 (local_411d0850-eb36-4821-aff6-886ad7a61e23) to add shots to its queued capture run instead of launching your own if that's quicker.
- Output: `work/majestic-all-maps/AUDIT.md` + a contact sheet.

## Phase 2: Reference images (before any building)
- **Every golf hole:** a target image per hole, made the way chat 9 made its concepts (AI repaint of the real game frame at the gameplay/tee camera, plus the flyover or aerial shot if the hole intro uses one). Keep hole layout, routing and gameplay readability identical; change only look, light, dressing and atmosphere. Keep one consistent art direction across a course and distinct identities between courses.
- **Weather:** a reference image for **each weather effect**, at a representative golf hole and tennis venue: rain, storm/lightning, wind, fog/mist, overcast, plus any others the audit finds. Show what top quality looks like at phone/TV distance (wet surfaces, droplets, sky, light, particles, foliage motion) while the ball stays readable.
- Before generating, give Adnan the credit estimate (chat 9 paid 16.5 credits for 6 images). Generate in batches of up to ~6 and push each batch to Adnan as it lands. Save to `work/majestic-all-maps/refs/` with a MANIFEST (source frame, prompt, model, credits).
- Put everything on a reference board (an HTML artifact).

## Added: the whole hole must look majestic
Adnan: "we need the entire hole to look majestic, so figure out the best practice to make sure that happens."
- Build a per-hole camera set from what the game really shows: tee, flight follow, landing/ball-cam, fairway/rough lies, approach, chip, putting from several sides, flyover, hole-out, reverse views. Sample real played-through shots, good and bad.
- Refs from several cameras per hole (at least tee, mid-fairway, green looking back, aerial, one off-line view), all made from one written per-hole design brief so they agree.
- A per-hole design sheet: top-down corridor + 360° backdrop per direction, landmarks so every view has a focal point, dressing density zones, palette/light, weather.
- Cite best practice from top golf/sports games: sightlines, landmark/skyline layering, scatter, LOD/impostors.
- Gates: REF_MATCH + "no empty/ugly view" at every sampled camera, a contact sheet per hole, perf at the worst view, ball readability.
- Give Adnan a revised credit estimate and a proposed number of views per hole.

## Phase 3: Plan
`work/majestic-all-maps/PLAN.md`:
- Per map and per weather effect: what to build (lighting/grade, dressing, props, sea/sky hand-off to chat 2's system, weather shaders/particles/wet surfaces/audio hook to the VFX + sound research), the cost budget at 1080p/60, and binary gates (REF_MATCH vs the refs, perf, readability).
- Reuse chat 9's Majestic layer architecture: new files, self-attaching.
- Order of work and a parallel-chat split that respects the machine-sharing rules: the slot limits mean at most ~2 heavy builders at once.
- Show Adnan the refs and the plan, then **stop and wait for his go-ahead before implementing.**

## Rules
Branch `10/13`: stage nothing, commit nothing in this phase. Edit only `work/majestic-all-maps/`. All Unity/Blender work goes through `heavy.sh`, booked on SCHEDULE.md, muted (GOLF_MUTE=1 + Editor mute), with clones in `~/`, not /private/tmp. Proof and refs at ≥1080p, but keep files reasonably small.
