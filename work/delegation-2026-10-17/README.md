# Delegation plan — 2026-10-17

Adnan's goals, split into **5 parallel chats + 1 integration chat afterwards**.

| # | Prompt | Goal(s) covered | Owns (only these chats edit these) |
|---|--------|-----------------|------------------------------------|
| 1 | [01_60fps_everywhere.md](01_60fps_everywhere.md) | All animations at 60 fps | Golf/plaza/hub/intro/lobby clips + their import metas, frame-rate/frame-budget code, SceneKit lobby frame rate |
| 2 | [02_rendered_backgrounds.md](02_rendered_backgrounds.md) | Painted backgrounds → rendered by us | Sky shaders, panorama textures, `Backdrop.cs`, distant scenery, venue sky/backdrop sections |
| 3 | [03_hand_arm_clearance.md](03_hand_arm_clearance.md) | Hands/arms never through body or clothes | `HeroPoseSafety.cs`, new clearance solver/proxy files, AnimationSafetyAudit tooling |
| 4 | [04_tennis_animation_integrity.md](04_tennis_animation_integrity.md) | Fix bugged tennis animations | Tennis source clips, `Resources/Tennis/Performance`, `HeroTennisDriver`, `TennisArmStrokeBuild`, `HeroGripPolish` |
| 5 | [05_garments_survive_animation_pipeline.md](05_garments_survive_animation_pipeline.md) | Clothes don't break + fast fit for new skins/clothes | `work/clothing-v2` builders/binders, garment meshes/correctives, cover masks, `ClothingV2Install.cs` |
| 7 | [07_female_face_shader_male_refs.md](07_female_face_shader_male_refs.md) | Female jaw + lips and skin shader to the reference; then the male reference pack (incl. tennis/golf shoes) | Female head geometry (jaw/lips), female skin/eye/lip shader branches + native surface code, `ArtDir/style/alive/male-reference-pack-2026-10-17/` |
| 5+ | (added 10-17 to chat 5) | Clothes closer to the reference, especially the female tennis top; then male clothes + fit, especially tennis/golf shoes, to chat 7's male pack | Same as 5, plus `TennisCloth` |
| 6 | [06_integration_after.md](06_integration_after.md) | **Run only after 1–5 finish** | Install order, shared prefabs, lobby re-export, whole-game audit |

## Why this split

- "Clothes don't break" and "new clothes fit fast" are **one** chat (5): the fix *is* the general pipeline. If two chats did them, they would edit the same binders and meshes.
- Hand clearance (3) is the **runtime/bake solver**. Tennis integrity (4) is the **source clips**. That way two chats never edit the same file. 3 also covers golf, plaza and the lobby.
- 60 fps (1) takes everything **except tennis clips**. Those were re-baked at 60 Hz on 10-16, and chat 4 keeps them at 60 Hz when it re-keys.
- Backgrounds (2) don't depend on the others.

## Shared rules (every prompt repeats them)

- **Performance floor (Adnan, 10-17): 60 fps at 1920×1080 or higher, everywhere**: phone, AirPlay/TV output and the SceneKit lobby. Never reach the budget by dropping resolution below 1080p or frame rate below 60. Measure perf and capture proof at ≥1080p. Chat 1 owns resolution/frame-rate settings and publishes the frame budget in `work/frame-rate-60b/BUDGET.md`.

- Branch `10/13`. The index already holds a lot of staged work: preserve it. Stage only your own reviewed files. No commits, resets or broad `git add`.
- Never open the real `Unity/` in an Editor. Each chat makes its own APFS clone: `cp -cR Unity /private/tmp/<task>-UnityClone`. Run one Editor per chat, with `GOLF_MUTE=1`.
- Use headless Blender (`/Applications/Blender.app/Contents/MacOS/Blender -b`), not the Blender MCP. The MCP is one shared instance.
- Disk had ~38 GB free on 10-17. Keep proof small and never delete another chat's data.
- Install directly into `Unity/` only files you own exclusively. For shared files (hero prefabs, scenes, ProjectSettings, shared manifests), write a patch plus an install script into your `work/` folder for chat 6.
- Use binary gates in `GATE_RESULTS.md` with proof images. Push images to Adnan every ~15–20 min.
- If you need a file another chat owns, write the request into `work/delegation-2026-10-17/REQUESTS.md` and tell Adnan.

## Update 10-17: chat 9 now builds
Adnan told chat 9 (majestic maps) to proceed toward the AI concept targets. It owns new files only (`Unity/Assets/Scripts/Majestic/*`, `Resources/Majestic/*`): light/grade, court, props, bunting, crowd, boats, gulls, sea look. Chat 2 keeps sky/clouds/karst/lighthouse. The one-line `DreamEnvironment.Apply` AfterApply hook goes through chat 2's patch or chat 6.

## Update 10-17: memory limits (Adnan: the computer was freezing)
This Mac has 16 GB of RAM. It hit 7.5 of 8 GB swap with 2 Unity + 3 Blender processes running at once. From now on:
- **Every Unity and Blender launch goes through `work/delegation-2026-10-17/heavy.sh`**: `heavy.sh unity <cmd…>` or `heavy.sh blender <cmd…>`. Machine-wide that allows 1 Unity and 2 Blender jobs at a time, and nothing starts below 20 % free memory. It waits instead of piling on. `heavy.sh status` shows who holds what.
- One heavy job at a time per chat; no parallel Blender/Unity fan-out inside a chat.
- Quit Editors and warm Blender servers when you're not actively using them (a kept-open Editor holds the Unity slot).
- Keep proofs at the needed resolution, and close Browser-pane tabs you no longer need.

## Sharing the machine (Adnan, 10-17, after a second freeze + restart)
The Mac (16 GB) must stay usable for Adnan while chats work. Five chats used to be fine. The freezes came from each chat running its own Unity clone **and** Blender jobs **and** parallel helpers all at once. Protocol:
1. **Gate:** every Unity/Blender launch goes through `heavy.sh unity|blender <cmd…>`: 1 Unity, 2 Blender machine-wide, and only when ≥20 % memory is free.
2. **One heavy thing per chat:** never two Unity/Blender jobs from one chat at once. No subagents/helpers that launch Unity or Blender. No warm servers or Editors left open while idle; batch-mode runs that exit are preferred.
3. **Book it on the board:** before a heavy run, add a line to `SCHEDULE.md` (chat, what, expected minutes) and remove it when done. If the board is busy, do light work meanwhile (code, analysis, writing gates, reviewing proof) instead of starting anyway.
4. **Delegate instead of duplicating:** if another chat already has a warm clone or a pending run that covers your need (same scene, same clip, same capture), message it (SendMessage to its local_ id) and ask it to add your shot/test to its run. Reuse its output files. Don't re-render what exists.
5. **Batch your asks:** collect several captures/tests into one Unity run instead of many short launches; each Editor start costs ~3–5 GB and minutes.
6. **Keep clones out of /private/tmp:** restarts wipe it. Use `~/<task>-UnityClone`, and delete your clone when your brief is done.
7. **Be polite to Adnan's foreground:** keep proof images small, don't open Browser-pane pages you don't need, and if `memory_pressure` shows < 20 % free, pause and wait.

## Update 10-17 20:15: capacity test (Adnan: get more done, but no "out of application memory" pop-up)
- heavy.sh now allows **2 Unity + 3 Blender** machine-wide. The first slot of each kind starts at ≥20 % free memory; every extra slot only at ≥35 % free AND swap use < 7 GB.
- A chat may now run **one Unity and one Blender job at the same time** (both through heavy.sh). Still no helpers that launch them, and no idle Editors or servers.
- `memlog.csv` (from `memlog.sh`) logs free memory, swap and job counts every 30 s. If Adnan reports the pop-up, the limits go back down.

## Update 10-17 ~21:00: out-of-memory pop-up hit, limits tightened
1 Unity + 2 Blender pushed swap to 12 GB and macOS showed the out-of-memory pop-up. heavy.sh now allows **1 Unity + 1 Blender**. A job can only run alongside another heavy job if memory is ≥35 % free and swap is < 5 GB; otherwise it waits. One heavy job per chat again.

## Update 10-18: coordinator decisions
- Male body: Adnan keeps the locked body plate (base_lock/male_body_plain.jpg). Don't bulk toward male pack sheet 15.
- Female tennis top: Adnan approved the fit; the visible rips must be cleaned up (garment-pipeline).
- Male prefabs: male-garments-refpack may apply its male_prefabs.patch to the working tree (unstaged, with a backup, logged in REQUESTS.md), because new meshes with the old prefabs break every copy of the tree.
- 10-18 ~00:50: side-by-side rule relaxed to ≥30 % free and swap < 7.5 GB (swap never drops below 5 GB once grown, so Unity sat idle). The pop-up was at 11–12 GB with 3 jobs.
- 10-18 ~05:50: heavy.sh is now first come, first served per class (only the oldest living waiter may take a slot). Waiters started before this keep racing until they finish.
- 10-18 ~10:10 (Adnan): up to 2 heavy jobs at once in any mix (2 Unity, 2 Blender, or 1+1); the 2nd still needs ≥30 % free and swap < 7.5 GB.
- 10-18 ~11:55: fairness rule: a class takes its 2nd slot only if no job of the other class is waiting (so 1 Unity + 1 Blender when both are queued).
- 10-18 13:30 TEST (Adnan): 3 heavy jobs = 2 Unity + 1 Blender. Watch memlog.csv; revert if the pop-up appears.
- 10-18 ~15:15 Adnan: pine walls on holes 7/15 STAY. VFX + sound research is on hold (ignore for now). Order: finish maps + weather → integration chat → test.
- 10-18 ~15:30 TEST (Adnan): 2 Blender slots (total cap still 3).
- 10-18 ~16:05: two parallel garments cover.py runs ballooned to ~45 GB each (swap 8.9 GB, out-of-memory pop-up). Killed them. Blender back to 1 slot; added an emergency brake: when swap > 9 GB and free < 25 %, the newest heavy job stops itself (logged in ~/.heavy-slots/brake.log, exit 137).
- 10-18 ~18:00: 2 heavy Unity jobs (~7 GB each) pushed swap to 12 GB. A 2nd concurrent job now needs swap < 6 GB; the brake also fires on swap > 12.5 GB alone.
- 10-18 ~18:25 (Adnan): 3 heavy jobs = 2 Unity + 1 Blender. Swap gate for extra jobs raised to 11 GB (swap never shrinks, so 6 GB serialized everything); brake still fires at swap > 12.5 GB or >9 GB with <25 % free. Limits now live in ~/.heavy-slots/limits and are re-read every poll, so future changes reach waiting jobs.
- 10-18 ~18:45 Adnan: no more phone builds until all changes are done (finish fixes → integration → then one phone build).
- 10-18 ~19:05 Adnan: ball outline = A (ember, thin warm rim + short streak). Ball glow left as is; rain/gusty contrast 2.0–2.8:1 accepted.
- 10-18 ~19:20 Adnan: 3 heavy jobs in either mix: 2 Unity + 1 Blender OR 2 Blender + 1 Unity (limits file: unity 2, blender 2, total 3). Blender renders are capped at 4 GB footprint (gp/render), and the brake stays on.
- 10-18 ~19:45: fast lane: jobs whose command matches HEAVY_PRIORITY_PATTERN (limits file, now "integration") get the next free slot of their kind.
- 10-18 ~19:55 TEST (Adnan closed other apps): 4 heavy jobs total (Unity 3 slots, Blender 2). Brake unchanged.
- 10-18 ~20:00: in the 4-job test, swap reached 11.5 GB while memory stayed ~50 % free (219 GB disk free, so swap can grow). Extra-job swap gate raised to 13 GB; swap-only brake to 15 GB; the free-memory brake (swap > 9 GB AND free < 25 %) unchanged. Jobs started from now on re-read the brake thresholds live.
- 10-18 20:05: the brake stopped hand-clearance fb5_golf_male (old 12.5 GB swap-only rule, a job started before the change) while memory was 67 % free: a false brake. Swap grows ~1 GB per Unity start and barely shrinks, so the swap-only limits are now 18 GB gate / 20 GB brake. The real signal is the free-memory brake: swap > 9 GB AND free < 25 %.
- 10-18 20:27 (Adnan: "try running a 4th heavy job"): Unity slots 4 (total 4). Integration was asked to run its independent second-pass films on a separate clone in the 4th slot.
- 10-18 ~21:00 Adnan: strengthen the tennis ball warm outline for rain tonight (W12 resort rain was 1.54:1). Tennis ball only, never dark, golf unchanged; in the final build.
- 10-18 ~21:10 Adnan: "stop the shirt tearing stuff for now". Garment tear work is paused; tonight ships today's golf female top + the K8 polo. Later plan (on hold, not now): rebuild/adjust EMOTES to fit the clothes rather than the cloth chasing extreme emote poses. Tennis/golf gameplay clips are not part of this.
