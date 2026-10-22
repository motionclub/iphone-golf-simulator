export const meta = {
  name: 'postcard-look-finish-v2',
  description: 'Finish POSTCARD_LOOK: texture + Unity/gate fixes, rebuild staged holes 8/9/10, install, Unity import check, 9 Game-view stills, vision/gate review panel, repair loop',
  whenToUse: 'POSTCARD_LOOK continue pass, phase 3 (after foundation + hole builds)',
  phases: [
    { title: 'Fix', detail: 'texture finish + Unity/gate finish in parallel' },
    { title: 'Rebuild', detail: 'restage the 3 holes on the final textures/libs' },
    { title: 'Install', detail: 'copy staged blend/FBX, Unity import, checks, 9 stills, metrics' },
    { title: 'Review', detail: 'per-hole vision reviewers + gate-line reviewers' },
    { title: 'Repair', detail: 'shared fixers (textures, libs, Unity) then hole fixers' },
  ],
}

const ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'

const BRIEF = `PASTE — POSTCARD LOOK, CONTINUE · NEW CHAT

The last postcard chat paused at 10:33 PM ET on Oct 3. Do not resume that chat or its workflow. Read work/postcard-look/RESUME.md, then fix the fails below and install them.

Where it stopped
- Textures, the ground library, the props library, and the Unity look wiring exist. Reviewers failed them. Repair had just started and was halted. Treat those files as partial.
- hole_08, hole_09, and hole_10 are still the flat afternoon meshes (FBX times 5:56, 6:04, and 6:56 PM ET). Nothing textured is on the real holes. No Game-view proof shots.
- Hole 7, Hole.cs, and the scoring cuts are untouched. Leave them that way. One shore, one centerline, one pin, PLAY_Z = 6. No second green, no hovering green, no animated lava.

Do not touch tennis files, QualitySettings, the hero shaders, Serve, or the locker. Another chat pointed the iPhone quality level at HeroBaseStudioURP. Leave that file alone.

Fix these, in this order. Each one was measured.

1. Grass. Fairway, green, and rough read about 20 degrees too blue-green against needle.jpg and split.jpg. Shift the albedo toward the stills (their greens sit around hue 64-73). Re-check under the golf key light, not in the PNG.
2. Water shelf. The turquoise ring around each island is 10-24 m wide and is the loudest thing in the aerial. split.jpg is deep blue up to the foam. Narrow the shelf until it is a thin edge, not a halo.
3. Lava. Lava_C is dark polygonal cells with glowing borders. crater.jpg is swirling molten flow, mostly bright. Rebuild the map. Drop the emission multiplier so it stays orange without bloom. Post does not render: TennisURP_Renderer has no postProcessData, and a golf-only volume is invisible. Do not edit the tennis renderer. Do not add bloom. Make the lava read orange with emission alone.
4. Basalt and smoke. Basalt reads as brick, and the glow repeats as little ladders. Columns should read as prisms, glow only in the joints. Smoke_C is a hard grey ball. Make it a soft wisp. The crater wall still shows a band of smooth grass texture at the top. Cover it.
5. Rocks and plants. Sea stacks read as stacked boxes. Legacy rock swap stretches wall pieces past 2x. Plants from scatter() land on the water when no region is passed. Fix the library before any hole calls it. No 12-vertex rocks.
6. Foam. Delete the white foam strips. A continuous white surf band is not a pass.
7. Cart path. On Needle it sits up to 11 cm above the play surface and hides the ball. Keep it under the ball.

Then install. Rebuild holes 8, 9, and 10 from the existing scoring meshes. Call postcard_look_lib, then export with postcard_look_lib.export_look_fbx. Do not use postcard_lib.export_fbx. Update PostcardImportCheck so LK_ materials pass. Do not weaken the ground, lie, or marker gates.

Proof, in the Game view, into ArtDir/screenshots/golf_postcards/look/.
- Needle, Split, and Crater: tee, approach, and one landmark each (arch, ruin ridge, lava rim).
FAIL if a hole is still one flat colour, the water halo is the brightest shape, the lava is dark cells, or a plant sits on the sea.

GATE POSTCARD_LOOK. Every line is PASS or FAIL.
- Holes 8-10 show albedo and normal in the Game view. Hole 7 is byte-identical.
- Grass hue, water edge, lava, basalt, and smoke match the lines above.
- No plant on water. No rock stretched past 2x. No white foam strip. Path does not cover the ball.
- Scoring cuts unchanged. Tennis files, QualitySettings, shaders, and Serve untouched.`

const TARGETS = `MEASURED FROM THE STILLS (16x16 px means; hue in degrees, then S, V):
- Needle fairway/green (172,186,66) h67 S.65 V.73 and (171,181,64) h65; Needle grass left/rough (135,134,57) h59 S.58 V.53.
- Split green (154,173,75) h72 S.57 V.68; fairway (133,152,52) h71 S.66 V.60, (142,161,58) h71, (125,143,62) h73; ridge scrub (122,111,75) h46 S.39 V.48, dark scrub (63,59,41).
- Crater fairway (136,161,26) h71 S.84 V.63; pillar green (156,173,28) h67 S.84 V.68; pillar rim (71,89,13) h74 V.35; lava (212,62,14) h15 S.93 V.83 and (193,70,18) h18; basalt (26,25,29).`

const RULES = `HARD RULES (every agent):
1. No git add/commit/stash/checkout/reset/restore/clean/rebase. The working tree holds other chats' uncommitted tennis, hero, menu and Swift work: never revert, reformat or "tidy" a file you do not own.
2. READ-ONLY, never edit: blender/hole_07.blend, Unity/Assets/Resources/Course/hole_07.fbx(+.meta), blender/scripts/hole07_*.py, Unity/Assets/Scripts/Course/Hole.cs (scoring), anything under Unity/Assets/Scripts/Tennis/, Unity/Assets/Resources/Tennis/ (TennisWater/TennisSky shaders, TennisPost, TennisURP*), Tennis.unity, Unity/Assets/Characters/** (HeroBaseStudioURP and hero shaders), Unity/ProjectSettings/QualitySettings.asset, Serve/locker/menu/Swift files. work/postcard-look/guards.sh must print 7 PASS when you report.
3. Scoring is frozen: no change to LieAt, shore polygons, centerlines, pin positions, PLAY_Z (6 m), par, hazard counts. Top surfaces of TERRAIN/FAIRWAY/GREEN/TEE_BOX/BUNKER keep exact outlines and heights. No second green, no hovering green, no animated lava, no bloom, no new post stack, no edit of the Tennis renderer. Post renders nowhere in this project and there is no tone mapper: everything must read right with lights and emission alone.
4. Collision prefixes: only TERRAIN, FAIRWAY, GREEN, TEE_BOX, BUNKER, CART_PATH meshes collide in HoleView. New objects use ROCK_, PLANT_, DRESS_, WATER_, LAVA_ only.
5. Unity ONLY through work/postcard-look/heavy.sh <label> <command...> (Unity batch runs and xcodebuild must never overlap; it waits for other chats). Binary: /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath Unity -executeMethod <Type.Method> -logFile <absolute log>; run long ones with run_in_background. Never kill another chat's process. If Unity fails to compile because of a NON-golf file, report it and do not edit that file. Ready-made wrappers: work/postcard-look/v2/runtime/run_importcheck.sh, run_smoke.sh, run_stills.sh, protected_check.sh (read them first).
6. Blender headless only: /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python <script> -- <args> (Blender 5.2). Do NOT use the Blender MCP or the GUI. numpy exists only in Blender's python (/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13); system python3 has Pillow but no numpy.
7. Evidence under work/postcard-look/v2/<area>/. Proof shots only in ArtDir/screenshots/golf_postcards/look/ (Game view). Blender renders are previews, NOT Game-view proof.
8. Every claim is a binary line "GATE: <ID> PASS|FAIL - <measured numbers>". "Looks better" is not a result. Unmeasured = unverified, never PASS. Report failures and skipped steps plainly. Do not weaken a gate to make it pass.
9. Keep notes current in the area's notes file ("v2 2026-10-04" sections). Your final message is your return value: fill the requested schema honestly.`

const COMMON = `You are one agent in the POSTCARD_LOOK CONTINUE job, phase 3 (install + Game-view proof + review + repair) of the golf holes 8 Needle, 9 Split, 10 Crater look pass. Look only; scoring is frozen. Today is 2026-10-04.
Repo root (absolute paths, never rely on the cwd): ${ROOT}
Job folder: ${ROOT}/work/postcard-look/ (evidence under work/postcard-look/v2/).

State: the foundation (textures, ground/water lib postcard_look_lib.py, props lib postcard_props_lib.py, Unity runtime GolfLook/GolfAtmosphere/HoleView/GolfSurf, gate tool postcard_look_verify.py, Game-view calibration) is finished and was skeptic-reviewed; the three hole builds are STAGED in work/postcard-look/v2/hole08|09|10/stage/ (not installed) with INSTALL.md, landmarks.json, run_all.sh in each hole folder. Read: work/postcard-look/RESUME.md (old, for history), work/postcard-look/v2/hole0N/INSTALL.md + landmarks.json + GATES_hole0N.*, RUNTIME.md (stills schema, v2 sections), LIB_GROUND.md / LIB_PROPS.md / GATES.md / TEXTURES.md ("v2" sections). View the look targets with the Read tool: ArtDir/environments/refs/needle.jpg, split.jpg, crater.jpg, and ArtDir/environments/14_POSTCARD_LOOK.txt (the full look brief).

THE USER'S BRIEF FOR THIS PASS (verbatim, authoritative):
<<<
${BRIEF}
>>>

${TARGETS}

${RULES}`

const RESULT = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['done', 'partial', 'blocked'] },
    summary: { type: 'string' },
    gates: {
      type: 'array',
      items: {
        type: 'object',
        properties: { id: { type: 'string' }, pass: { type: 'boolean' }, detail: { type: 'string' } },
        required: ['id', 'pass', 'detail'],
      },
    },
    files_changed: { type: 'array', items: { type: 'string' } },
    open_issues: { type: 'array', items: { type: 'string' } },
  },
  required: ['status', 'summary', 'gates', 'files_changed', 'open_issues'],
}

const VERDICT = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['PASS', 'FAIL'] },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          hole: { type: 'string', enum: ['08', '09', '10', 'all'] },
          area: { type: 'string', enum: ['hole_script', 'texture', 'lib_ground', 'lib_props', 'unity_runtime', 'gate_tool', 'install', 'other'] },
          user_line: { type: 'string' },
          where: { type: 'string' },
          evidence: { type: 'string' },
          repro: { type: 'string' },
          fix_hint: { type: 'string' },
        },
        required: ['severity', 'hole', 'area', 'user_line', 'where', 'evidence'],
      },
    },
    measured: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict', 'findings', 'measured'],
}

const INTEGRATE = `AREA I - INSTALL + GAME-VIEW PROOF (you are the only agent running Unity right now besides the lock-serialised helpers; always via heavy.sh).
1. Preconditions: work/postcard-look/guards.sh 7 PASS; the staged files of each hole exist and match the sha256 in work/postcard-look/v2/hole0N/INSTALL.md (if a hole's stage changed after INSTALL.md was written, trust the files, recompute the sha and note it). Check the lib/texture sha256 recorded by the hole builders vs now and report if the libs changed after the last stage build (then the hole must be rebuilt: run work/postcard-look/v2/hole0N/run_all.sh, which stages again).
2. Install (copy the .blend and the .fbx ONLY; NEVER touch an existing hole_NN.fbx.meta; never touch hole_07.*): blender/hole_NN.blend and Unity/Assets/Resources/Course/hole_NN.fbx for NN = 08, 09, 10 (INSTALL.md has the commands; also copy the staged overview preview to blender/previews/hole_NN_overview.png if INSTALL.md says so). Keep a rollback copy of what you replaced in work/postcard-look/v2/install_backup/ (the baseline is also in work/postcard-look/baseline/). Make a re-runnable script work/postcard-look/v2/proof/run_proof.sh that does steps 2-5 end to end (idempotent: copies only when sha differs), because later repair rounds re-run it.
3. Unity import + checks (heavy.sh): confirm the FBX metas still say isReadable 1 and tangentImportMode 3 and kept their GUIDs; run PostcardImportCheck (GolfArcade.EditorTools.PostcardImportCheck.Run: all ground-height / lie / marker lines MUST PASS, plus the LK_ lines: albedo AND normal on every ground material, no flat postcard ground, no foam strip, lava lights, rock chunking...), GolfLookSmoke, and the real-geometry probes the runtime owner built (RUNTIME.md). Also run Tools/PostcardCheck/run.sh (real Hole.cs gates + tests) if it needs no Unity editor, and the EditMode PostcardHoleTests if the project has a working batch test runner (report if not). Any FAIL: say whether it is an install problem you may fix inside your remit (PostcardImportCheck.cs and the wrapper scripts only: never weaken a ground/lie/marker line), or a content problem for the repair stage (do not fix content yourself).
4. Game-view stills: build one cfg JSON for the 9 shots from the three landmarks.json (names hole08_1_tee, hole08_2_approach, hole08_3_arch, hole09_1_tee, hole09_2_approach, hole09_3_ruin, hole10_1_tee, hole10_2_approach, hole10_3_lavarim; address shots use FrameAddress with the ball/aim in the landmarks.json; landmark shots use pos/look/fov) and run PostcardLookStills (GOLF_STILLS_CFG, GOLF_STILLS_OUT=${ROOT}/ArtDir/screenshots/golf_postcards/look/) under the active quality asset (note which one; the iPhone level currently uses HeroBaseStudioURP) and, for the grass/lava/shelf measurements, also once under TennisURP if the pipeline allows it (RUNTIME.md v2.9 explains the in-memory switch). The older files in that folder (props_sheet.png, textures_sheet.png from the paused pass) may stay; delete nothing else. Verify each PNG is 900x1600, not blank, and view every one with the Read tool.
5. Measurements from the PIXELS of the stills and the Unity runs (not from textures): per hole: grass mean HSV of the central lower third (fairway/green/rough regions: hue bands from the user's line 1), fraction of clipped pixels, luminance sd of the lower 60% (is it still a flat colour?), shelf/halo (is any turquoise ring the brightest shape?), lava pixels (hue 8-28, S>=.75, V>=.7, dark-cell fraction), basalt joint glow, smoke visibility, plants on water (mesh-level, from the installed FBX), rock scales, foam strips, path vs ball. Write work/postcard-look/v2/proof/metrics.json and a human table work/postcard-look/v2/proof/METRICS.md.
6. Contact sheets: for each hole one side-by-side sheet (reference still | tee | approach | landmark) in work/postcard-look/v2/proof/sheet_holeNN.jpg, and one overall sheet of all nine stills. Also copy nothing else into ArtDir/screenshots.
Report gate lines: INSTALL_SHA_MATCH (per hole), META_KEPT (per hole), GUARDS_7_OF_7, PROTECTED_FILES (compare Unity/Assets/Scripts/Tennis, Unity/Assets/Resources/Tennis, Unity/Assets/Characters, Unity/ProjectSettings with work/postcard-look/v2/protected_hashes_start.txt; list every difference and say whether our job could have written it), UNITY_COMPILE_0_ERRORS, IMPORTCHECK (counts; list every FAIL), SMOKE, STILLS_9_OF_9, STILL_SIZE_OK, plus one metric gate per user line measured on the stills (GRASS_HUE_GAMEVIEW per hole, NOT_FLAT_PER_STILL, SHELF_NOT_LOUDEST, LAVA_ORANGE_AND_BRIGHT, BASALT_JOINTS, SMOKE_SOFT, NO_PLANT_ON_SEA, NO_ROCK_STRETCH_2X, NO_FOAM_STRIP, PATH_UNDER_BALL) with numbers; a metric you could not take is reported as not measured.`

function holeBlock(h) {
  return {
    '08': 'HOLE 8 NEEDLE: stills hole08_1_tee, hole08_2_approach, hole08_3_arch; reference ArtDir/environments/refs/needle.jpg (a broken chain of grass cliff-islands over deep blue water; stone path, shrubs, purple flowers, vine-covered masonry arch beside the bunker, waterfall off the lower right pad, dark stratified cliffs with hanging vines, sea stacks, thin shelf, sparse foam).',
    '09': 'HOLE 9 SPLIT: stills hole09_1_tee, hole09_2_approach, hole09_3_ruin; reference ArtDir/environments/refs/split.jpg (one rugged island cut by a turquoise channel; manicured emerald fairway on the right ribbon, sand bunkers that read as sand, clifftop green, left ridge of olive dry scrub with rocks and a ruin of broken stone masonry, jagged rock shore with sparse whitewater, deep blue sea up to the foam; one green only).',
    '10': 'HOLE 10 CRATER: stills hole10_1_tee, hole10_2_approach, hole10_3_lavarim; reference ArtDir/environments/refs/crater.jpg (a black columnar basalt bowl; swirling mostly-bright orange lava; a grass shelf with two bunkers; the pin pillar whose top is fairway height, sides dropping into the lava; square tee pad; agave plants; background cone and soft smoke; lava lights the nearby rock).',
  }[h]
}

function visionReview(h, round, prev) {
  return `${COMMON}

YOU ARE AN INDEPENDENT SKEPTIC VISION REVIEWER of the INSTALLED look of ${holeBlock(h)}
${round > 0 ? 'This is a RE-REVIEW after a repair round: first check every earlier finding (listed below) is really fixed in the NEW stills, then hunt for regressions.' : ''}
Look at the three Game-view stills in ArtDir/screenshots/golf_postcards/look/ with the Read tool (900x1600 phone frames), the contact sheet work/postcard-look/v2/proof/sheet_hole${h}.jpg, the reference still, and the metrics in work/postcard-look/v2/proof/metrics.json. You may re-measure pixels yourself with Pillow (system python3). You may NOT edit anything outside work/postcard-look/v2/review3_${h}/ (scratch). You may run Unity via heavy.sh only if you need a fresh Game-view render for a specific check (scratch output dir). Judge, as the user would on a phone:
- User FAIL conditions: is the hole still ONE FLAT COLOUR (look at the lower two thirds: does the ground have visible texture, mow stripes, variation, and a normal-map relief at 2-20 yd)? Is a water halo the brightest/loudest shape? Is the lava dark cells (Crater)? Is any plant sitting on the sea? A faceted grey blob, solid blue plane, solid orange plane?
- Look match to the reference: silhouette, colour blocks, landmarks (are they present, readable, in frame, not blocked?), grass hue (measure vs 64-73), rock/cliff character (strata / basalt prisms with glow only in joints, no brick, no ladders, no stacked boxes), foam (sparse broken whitewater, never a continuous white band), sand reads as sand, soft smoke wisp (Crater), path under the ball (Needle), nothing hides the ball or the flag.
- Anything that would embarrass the product on a phone: floating or buried objects, z-fighting/flicker bands, texture stretching, tiling grids, seams, black/pink materials, popping lava, clipped whites, the golfer hidden or clipped.
Be harsh and specific: every finding needs the still file, the pixel region, the measured numbers and what to change (area: hole_script / texture / lib_ground / lib_props / unity_runtime / gate_tool / install). Verdict PASS only if you would sign the user's POSTCARD_LOOK lines for this hole from the pixels.
${prev ? '\nEarlier findings to re-verify:\n' + JSON.stringify(prev, null, 1) : ''}`
}

function gateReview(round, prev) {
  return `${COMMON}

YOU ARE AN INDEPENDENT SKEPTIC GATE-LINE REVIEWER of the whole INSTALLED pass. ${round > 0 ? 'This is a RE-REVIEW after a repair round: verify every earlier finding is fixed, then hunt for regressions.' : ''}
Walk every line of the user's GATE POSTCARD_LOOK and measure it yourself (do not trust the integrator's metrics):
1. Holes 8-10 show albedo AND normal in the Game view (run PostcardImportCheck/smoke yourself via heavy.sh and inspect the instantiated materials; no flat _BaseColor-only postcard ground); hole 7 byte-identical (guards.sh, sha256 of hole_07.blend/.fbx/.meta/Hole.cs).
2. Grass hue, water edge (shelf thin, not the loudest shape), lava, basalt, smoke match the user's lines: from the Game-view stills and Unity runs.
3. No plant on water (re-import the INSTALLED FBX, raycast bases; also the blend), no rock stretched past 2x (instance scale components within [0.5, 2.0], max/min <= 2.0; and 0 rocks with < 60 welded vertices, no icosahedron), no white foam strip (surf runs/gaps/coverage; no MAT_FOAM/WATER_FOAM), path does not cover the ball (Needle: height above ground at path vertices <= 1.2 cm, dense grid <= 1.5 cm, ball-hide test).
4. Scoring cuts unchanged: Hole.cs hash, postcard_emit_cs --check no drift, installed blends' TERRAIN/FAIRWAY/GREEN/TEE_BOX/BUNKER vertices AND up-facing faces identical to work/postcard-look/baseline/blender/hole_NN.blend, PostcardImportCheck ground/lie/marker lines PASS, Tools/PostcardCheck/run.sh PASS, markers/pin placeholders unchanged.
5. Tennis files, QualitySettings, shaders, Serve untouched: hash-compare Unity/Assets/Scripts/Tennis, Unity/Assets/Resources/Tennis, Unity/Assets/Characters, Unity/ProjectSettings against work/postcard-look/v2/protected_hashes_start.txt and list every difference; attribute each (this job cannot have written it if our agents' tools never touched that path: check mtimes against our job's file lists and git diff of those files; another chat's concurrent edits are a note, not our FAIL, but you must say which). Also confirm QualitySettings.asset and HeroBaseStudioURP.asset were not modified by this job, and that no tennis scene file/shader appears in the job's changed-file list (find files newer than work/postcard-look/v2/.start_marker outside the allowed set: blender/, Unity/Assets/Scripts/Course|Game/GolfGame|CameraRig, Unity/Assets/Editor Golf/Postcard files, Unity/Assets/Resources/Course/, ArtDir/screenshots/golf_postcards/, ArtDir/environments/, work/postcard-look/, and list the rest).
6. Proof exists: the 9 stills (900x1600, not blank), none a flat-colour ribbon on a solid plane (view them).
You may NOT edit anything outside work/postcard-look/v2/review3_gates/ (scratch). Output findings with the owning area and the exact gate line; verdict PASS only if every line measured PASS.
${prev ? '\nEarlier findings to re-verify:\n' + JSON.stringify(prev, null, 1) : ''}`
}

function sharedFixPrompt(area, items, round) {
  const scope = {
    texture: 'You own blender/scripts/golf_look_textures.py, the Look PNGs (not .meta), work/postcard-look/TEXTURES.md and may adjust the matching constants in Unity/Assets/Scripts/Course/GolfLook.cs (Table/HoleTint) when the Game view needs it. Regenerate with the Blender python (see TEXTURES.md for the exact command), keep names/sizes/seamlessness, keep the folder <= 25 MB; update the generator gates; re-verify in the Game view through the smoke/stills runs.',
    libs: 'You own blender/scripts/postcard_look_lib.py, postcard_props_lib.py, their smoke scripts, LIB_GROUND.md, LIB_PROPS.md and Plants_C.png. Keep every existing lib gate passing and the play tops bit-identical. After changing a lib, the hole scripts must be rebuilt: say which holes need a rebuild (the hole fixers run afterwards and rebuild).',
    unity: 'You own Unity/Assets/Scripts/Course/GolfLook.cs, GolfAtmosphere.cs, HoleView.cs (postcard rule only; hole 7 stays byte-for-byte), Unity/Assets/Scripts/Game/GolfGame.cs (the golf atmosphere hook only), CameraRig.cs (near plane only), Unity/Assets/Resources/Course/Shaders/GolfSurf.shader, Unity/Assets/Editor/GolfLookSmoke.cs, PostcardImportCheck.cs, PostcardLookStills.cs, RUNTIME.md, and postcard_look_verify.py / GATES.md (the gate tool: never weaken a gate; fix gates that are wrong or too strict for a legal build only with measured reasoning). Verify every change in Unity through heavy.sh.',
  }[area]
  return `${COMMON}

You are a REPAIR agent for the shared area "${area}" (repair round ${round}). ${scope}
Findings from the independent reviewers that are YOUR responsibility:
${JSON.stringify(items, null, 1)}
Fix each high and medium finding (low ones if cheap) at its root cause; do not paper over it in a hole script. Do not touch files owned by the other areas (texture / libs / unity+gates / hole scripts) except where your scope above says so. Keep the foundation gates passing (GolfLookSmoke, lib smokes, generator gates). Re-measure the affected numbers (Game view where the finding was a Game-view finding) and report the full gate table of what you touched.`
}

function holeFixPrompt(h, items, round) {
  return `${COMMON}

You are the HOLE ${h} REPAIR agent (repair round ${round}). You own blender/scripts/hole${h}_build.py, hole${h}_look.py (if any), the free-form SCENERY dict in blender/scripts/hole${h}_design.py (course data, shores, hazards, pin MUST stay identical: python3 blender/scripts/postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs must say no drift) and work/postcard-look/v2/hole${h}/. You do NOT edit the libs, textures or Unity files (the shared fixers did that in this same round, BEFORE you: check the sha256 of the libs/textures against work/postcard-look/v2/hole${h}/lib_sha_*.txt, expect them to have changed, and rebuild). ${holeBlock(h)}
Rebuild with work/postcard-look/v2/hole${h}/run_all.sh (or the commands in INSTALL.md; staged output in work/postcard-look/v2/hole${h}/stage/, never in the repo; the integrator installs after you), re-run every gate (postcard_look_verify.py on blend and FBX re-import, postcard_verify.py, postcard_check.py, the hole's own QA gates; Blender previews from the stills' viewpoints), update landmarks.json and INSTALL.md with the new sha256. Reviewer findings that are YOUR responsibility (hole script / geometry / placement / scenery):
${JSON.stringify(items, null, 1)}
Findings that are about libs/textures/Unity are not yours: ignore them (note them in open_issues if the shared fixers' change did not cure them). Do not weaken a gate. Keep all hole gates and scoring identical (compare to work/postcard-look/baseline/blender/hole_${h}.blend). Do not run Unity. Report the full gate table.`
}

function summarize(v) {
  return v ? v.verdict + ' (' + v.findings.length + ' findings: ' + v.findings.map((f) => f.severity[0] + ':' + f.hole + ':' + f.area).join(' ') + ')' : 'NO RESULT'
}

const HOLES = ['08', '09', '10']
const history = []

async function reviewPanel(round, prevByKey) {
  const tasks = HOLES.map((h) => () => agent(visionReview(h, round, prevByKey ? prevByKey[h] : null), { label: (round ? 're-review' + round : 'review') + ':vision ' + h, phase: 'Review', schema: VERDICT, effort: 'high' }))
  tasks.push(() => agent(gateReview(round, prevByKey ? prevByKey.gates : null), { label: (round ? 're-review' + round : 'review') + ':gates', phase: 'Review', schema: VERDICT, effort: 'high' }))
  const rs = await parallel(tasks)
  return { '08': rs[0], '09': rs[1], '10': rs[2], gates: rs[3] }
}


const OPEN_STATE = `STATE AT THE START OF THIS RUN (2026-10-04, after a usage-limit stop): foundation reviewed (textures, props lib, ground lib, Unity runtime PASS; gate tool V had 5 open findings; Game-view calibration K done with 4 open findings), the three holes are STAGED in work/postcard-look/v2/hole0N/stage/ and verdict FAIL only on the LOOK_FILES gate (grass textures too smooth) + Game-view proof absent. Nothing is installed in the repo. This run: (Fix) texture finish + Unity/gate finish in parallel -> (Rebuild) restage the holes on the final files -> (Install) -> Game-view proof -> review panel -> repair loop.`

const TEXTURE_FINISH = `AREA T - TEXTURE FINISH. You own blender/scripts/golf_look_textures.py, the PNGs in Unity/Assets/Resources/Course/Look/ (not their .meta), work/postcard-look/TEXTURES.md, work/postcard-look/v2/tex/, and ONLY the texture tint/smoothness constants (Table / HoleTint rows) of Unity/Assets/Scripts/Course/GolfLook.cs (another agent, the Unity/gate finisher, runs in parallel and owns everything else in that file and the other Unity files: do not touch them, and re-read GolfLook.cs right before you edit it). Read TEXTURES.md "v2" sections and v2/calibrate tools (run_probe.sh, run_smoke.sh, run_stills.sh wrappers) first.
Fix, in this order, measuring each:
1. GRASS FLATNESS (the lead's #1 risk: a flat lawn). gates 'LOOK_FILES': Fairway_C reaches luminance sd 0.03 in only 1% of its 1/16-tile windows, Green_C 0%; the lower 60% of the Needle tee frame has albedo luminance sd about 16/255 and the stills' own grass is livelier. Add visible, stylised variation that survives the phone view at 2-20 yd: mid-frequency mottle (0.3-1.5 m patches), mow-stripe contrast (about +-8-10% luminance), fine blade grain/streaks, a touch of hue drift inside 64-73 degrees. Keep seamless tiling, no lone repeating blob, no photo noise. Do NOT chase the old 90% window floor blindly: the stills reach sd>=0.03 in only 31-67% of 16 px grass windows (v2/gates/calib/still_calib.txt), so match or modestly exceed the STILLS' window statistics at the same scale (measure them with Pillow on needle.jpg/split.jpg/crater.jpg), and ALSO require the Game-view result: lower-60% luminance sd of the real tee/approach frames (measure through the stills/probe wrappers, hole 8 flaky probe: run it 3 times and use only runs where the textured FBX is verified) at least the stills' level. Keep grass hue 64-73 under the golf key light (re-measure in the Game view, not the PNG), no clipping. Fairway_C, Green_C, Rough_C, Scrub_C.
2. LAVA (Lava_C/_E): keep the swirling molten flow, mostly bright orange, emission alone (no post, no bloom, no tone mapper: values must not clip); add a small share of darker crust plates and a few hotter yellow-orange veins so it reads as glowing flow, not orange paint (crater.jpg). Gate: still >= 85% of lava pixels in hue 8-28 / S >= .75 / V >= .70, G clipped 0.0%.
3. BASALT (Basalt_C/_E): break the near-regular dash rhythm of the joint glow, branch/irregular cracks, charcoal near-black tint (not greenish slabs), prisms readable as faceted columns, glow only in the joints. 4. SCRUB (Scrub_C): streakier dry scrub like split.jpg instead of large soft blobs; hue ~46-49 kept.
Keep names, sizes, seamlessness, determinism (same seeds => byte-identical), folder <= 25 MB, generator gates passing. After regenerating: run GolfLookSmoke and a stills/probe check through the wrappers (heavy.sh) and report Game-view numbers. Record new sha256 of every Look PNG in work/postcard-look/v2/tex/look_png_sha_final.txt. Hole rebuilds happen after you (another step): do not rebuild holes.`

const UNITY_FINISH = `AREA U - UNITY + GATE-TOOL FINISH. You own Unity/Assets/Scripts/Course/GolfAtmosphere.cs, GolfLook.cs (EXCEPT the texture Table/HoleTint tint rows, owned by the texture agent running in parallel: re-read the file before every edit and keep your edits away from those rows), HoleView.cs (postcard rule only; hole 7 stays byte-for-byte), Unity/Assets/Scripts/Game/GolfGame.cs (golf atmosphere hook only), CameraRig.cs (near plane only), Unity/Assets/Resources/Course/Shaders/GolfSurf.shader, Unity/Assets/Editor/GolfLookSmoke.cs, PostcardImportCheck.cs, PostcardLookStills.cs, the probe tools under work/postcard-look/v2/calibrate/tools/, RUNTIME.md, blender/scripts/postcard_look_verify.py and GATES.md. Read RUNTIME.md and GATES.md "v2" sections and the wrappers in work/postcard-look/v2/runtime/ first. Fix, measuring each (all Unity runs through heavy.sh):
a) CRATER GOLFER CLIPPING (reproduced 3 of 3): probe gate GOLFER_NOT_CLIPPED hole10: skin pixels with a channel >= 250 are 17.9% (limit 5%); the shirt blue is crushed to (37,49,64) over 5,396 px vs (47,90,128) under the legacy light; hole 9 is 3.5%/1.1% (passes, legacy 0.0%), Needle 2.0%. There is no tone mapper and no post, so lights must stay inside range. Prefer the LIGHTING-SIDE fix in GolfAtmosphere/GolfLook for hole 10 (key, ambient, fill, lava point lights as the golfer sees them) while the dusk stays orange and the lava still lights nearby rock; changing GolferView.cs (the golfer, not a tennis hero) is a last resort: minimal, per-hole, disclosed. Use GOLF_LOOK_PROBE_KEYSWEEP to measure; also bring Split below 1% if cheap. Do not reduce lava/wall emission readability. Gate: golfer clipped <= 5% skin and shirt not crushed on all three holes, repeated twice.
b) HOLE 8 PROBE NON-DETERMINISM: the real-geometry probe rendered the FLAT baseline Needle in 3 of 6 runs (the swap of the 'Course model' did not take effect). Make the probe wait for / assert the swap (for example fail loudly unless the instantiated model carries LK_ materials), then run it 5 times: all must be textured.
c) GATE TOOL (postcard_look_verify.py, 5 reviewer findings; never weaken a gate; mutants must still FAIL): (1) rock/sea-stack/stack-taper gates select by OBJECT NAME only: a noisy 42-vertex icosphere named DRESS_BOULDER, 13-vertex icosahedra, welded icosahedron clusters and a stacked-box ziggurat named DRESS_STACK pass: classify by MESH SHAPE and MATERIAL (LK_ROCK / LK_ROCK_WET / LK_BASALT / LK_MASONRY-less rock-like props anywhere), not by prefix; (2) NO_ROCK_STRETCH_2X: judge anisotropy (max/min scale <= 2.0) and an absolute upper cap separately from a lower scale bound; a uniform 0.4 pebble is not 'stretched' (fix the wording; library kinds may scale 0.4..2.0 uniformly; stretch = anisotropy or non-uniform past 2x); (3) LOOK_FILES floor (lead decision, made here): floors = the stills' own window statistics at the same window scale (measure with Pillow; v2/gates/calib/still_calib.txt has a first calibration), plus a Game-view luminance-sd floor for the lower 60% of the tee/approach stills when stills exist; keep the flat+noise / checkerboard / downsample mutants FAILing; do NOT use a number that the stills themselves fail; the textures are being changed in parallel by the texture agent: set the floor from the stills, then re-run on the final PNGs near the end of your work and report; (4) NO_FOAM_STRIP: apply the white test to the sRGB-converted base colour too, so a pale non-LK band cannot slip through; (5) document the 1 mm collision-tolerance in GATES.md. Re-run the tool's own mutation suite.
d) PostcardImportCheck: confirm LK_ materials pass (no flat postcard ground, albedo AND normal on every ground material, no foam strip, lava lights), PALETTE lines accept LK_ names, ground-height/lie/marker lines unchanged (3000 samples). The check may only wait on install for holes still baseline; say which.
Keep GolfLookSmoke passing, guards.sh 7 PASS, hole 7 byte-identical, tennis files untouched.`

phase('Fix')
log(OPEN_STATE)
const finishRes = await parallel([
  () => agent(`${COMMON}\n\n${TEXTURE_FINISH}`, { label: 'fix0:T textures', phase: 'Fix', schema: RESULT }),
  () => agent(`${COMMON}\n\n${UNITY_FINISH}`, { label: 'fix0:U unity+gates', phase: 'Fix', schema: RESULT }),
])
history.push({ round: -1, finishRes })
log('finish T: ' + (finishRes[0] ? finishRes[0].status + ' ' + finishRes[0].gates.filter((g) => !g.pass).map((g) => g.id).join(',') : 'NO RESULT') + ' | finish U: ' + (finishRes[1] ? finishRes[1].status + ' ' + finishRes[1].gates.filter((g) => !g.pass).map((g) => g.id).join(',') : 'NO RESULT'))

phase('Rebuild')
const rebuildRes = await parallel(HOLES.map((h) => () => agent(holeFixPrompt(h, [], 0) + '\nTHIS IS A REBUILD-ONLY STEP: the texture agent regenerated the Look PNGs and the Unity/gate agent changed the gate tool; restage the hole on the final files (run_all.sh), re-run all gates, refresh INSTALL.md / landmarks.json / sha files. If a gate FAILs only because of a lib/texture/gate-tool problem, report it plainly (do not edit those files).', { label: 'rebuild0:hole ' + h, phase: 'Rebuild', schema: RESULT })))
history.push({ round: -1, rebuildRes })
log('rebuild: ' + rebuildRes.map((r, i) => HOLES[i] + ' ' + (r ? r.status + ' fails=' + r.gates.filter((g) => !g.pass).map((g) => g.id).join(',') : 'NO RESULT')).join(' | '))

phase('Install')
let integ = await agent(`${COMMON}\n\n${INTEGRATE}`, { label: 'install:I round0', phase: 'Install', schema: RESULT })
history.push({ round: 0, integ })

phase('Review')
let panel = await reviewPanel(0, null)
log('round 0 review: 08 ' + summarize(panel['08']) + ' | 09 ' + summarize(panel['09']) + ' | 10 ' + summarize(panel['10']) + ' | gates ' + summarize(panel.gates))
history.push({ round: 0, panel })

function allPass(p) {
  return ['08', '09', '10', 'gates'].every((k) => p[k] && p[k].verdict === 'PASS')
}

for (let round = 1; round <= 3 && !allPass(panel); round++) {
  phase('Repair')
  const all = []
  for (const k of ['08', '09', '10', 'gates']) {
    if (panel[k]) for (const f of panel[k].findings) if (f.severity !== 'low' || panel[k].verdict === 'FAIL') all.push(f)
  }
  const sharedAreas = { texture: 'texture', lib_ground: 'libs', lib_props: 'libs', unity_runtime: 'unity', gate_tool: 'unity' }
  const groups = {}
  for (const f of all) {
    const g = sharedAreas[f.area]
    if (g) (groups[g] = groups[g] || []).push(f)
  }
  const gk = Object.keys(groups)
  log('round ' + round + ' shared repair groups: ' + (gk.join(', ') || 'none'))
  const sharedRes = gk.length
    ? await parallel(gk.map((g) => () => agent(sharedFixPrompt(g, groups[g], round), { label: 'fix' + round + ':shared ' + g, phase: 'Repair', schema: RESULT })))
    : []
  // hole fixers: all findings that are hole_script/other for that hole, plus 'all' hole ones
  const holeItems = {}
  for (const h of HOLES) holeItems[h] = all.filter((f) => (f.hole === h || f.hole === 'all') && (f.area === 'hole_script' || f.area === 'other'))
  const needsRebuild = gk.includes('libs') || gk.includes('texture')
  const holeRes = await parallel(HOLES.filter((h) => holeItems[h].length > 0 || needsRebuild).map((h) => () => agent(holeFixPrompt(h, holeItems[h], round), { label: 'fix' + round + ':hole ' + h, phase: 'Repair', schema: RESULT })))
  history.push({ round, sharedRes, holeRes })
  phase('Install')
  integ = await agent(`${COMMON}\n\nThis is repair round ${round}. The installer script work/postcard-look/v2/proof/run_proof.sh from round 0 exists: re-run it (it reinstalls changed staged files, re-runs Unity checks, re-shoots the 9 stills, and re-measures); fix the script if the stage layout changed. If a hole was rebuilt after the libs changed, make sure you install the NEW stage.\n\n${INTEGRATE}`, { label: 'install:I round' + round, phase: 'Install', schema: RESULT })
  phase('Review')
  panel = await reviewPanel(round, { '08': panel['08'] && panel['08'].findings, '09': panel['09'] && panel['09'].findings, '10': panel['10'] && panel['10'].findings, gates: panel.gates && panel.gates.findings })
  log('round ' + round + ' review: 08 ' + summarize(panel['08']) + ' | 09 ' + summarize(panel['09']) + ' | 10 ' + summarize(panel['10']) + ' | gates ' + summarize(panel.gates))
  history.push({ round, integ, panel })
}

return { allPass: allPass(panel), finalPanel: panel, finalInstall: integ, rounds: history.length }
