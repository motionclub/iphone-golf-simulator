# Can it be majestic and still hold 60 fps at 1080p?

Research chat 9, 2026-10-17. This is measurement and judgement only; nothing in the game was changed.

**Short answer: yes, for the look Adnan described** (Wii / Fall Guys / Mario majestic, not simulation).

On an **iPhone 17 Pro** today's venues appear to leave **5–8 ms of GPU headroom** (estimate from Mac measurements), which is enough for the whole majestic layer. Two hot spots need work first:
- **golf weather**, which roughly doubles a golf frame's per-pixel cost;
- **hole 12**: 5.5 M triangles per frame.

On **older phones (iPhone 15/16) and in two-player split screen** the budget is tight to over. There the "make room" work comes first:
- character LOD (two characters are ~1.06 M triangles per frame);
- fewer shadow casters;
- weather drawn inside the materials.

These do **not** fit at 60/1080p and the game doesn't need them: real-time volumetrics, simulation grass, real reflections, and denser geometry.

> No frame time has ever been measured on a phone for this project. Every iPhone number below is scaled from the Mac and should be read ±40 % until the device run (PROPOSAL P0) replaces it.

---

## 1. How this was measured, and how far to trust it

- **Where:** a private APFS clone of `Unity/` at `/private/tmp/majestic-UnityClone`. Muted (`GOLF_MUTE=1`, Editor mute and `AudioListener.volume = 0` every frame). Unity 6000.3.24f1, Metal, **Apple M5, 10-core GPU**. Pipeline `TennisURP`: 4× MSAA, HDR, depth texture, 4096 shadow map, soft shadows. Harness [tools/MajesticCost.cs](tools/MajesticCost.cs), runner [tools/run.sh](tools/run.sh), summariser [tools/summarize.py](tools/summarize.py).
- **What:** the production gameplay camera, rendered into a **1920×1080** target with the pipeline's own MSAA:
  - all 16 golf holes at the tee address view;
  - the 3 tennis venues from the near-player shoulder view;
  - the plaza hub.

  Weather: 5 golf slots, plus each tennis venue in rain, storm and fog. HUD canvases were off.
- **Variants, interleaved in rounds:** full, no shadows, no post, no MSAA, no characters, sky only, empty.
- **Three runs:**

  | Run | When | Machine load | Slots | Use |
  |---|---|---|---|---|
  | Sweep | 02:28–02:50 | 24–64 (six other chats' Unity/Blender jobs) | 34 | Counts (after correction) and relative comparisons |
  | Quiet 1 | 09:30 | ~4 | golf 8, 12, 18 | **Absolute timing anchor.** Files lost in a reboot; log lines recovered in [proof/quiet/partial_from_lost_run.md](proof/quiet/partial_from_lost_run.md) |
  | Quiet 2 | 09:46–09:58 | 12–56 | 11 (golf 8/12/18 + storm, 3 venues clear + storm, hub) | Single-render counts for every place; same-load comparisons |

- **Counts** (triangles, draw calls, SetPass, shadow casters) are hardware-independent and reliable after one correction. On the loaded machine some profiler frames held **two** camera renders. The sweep's golf and hub counts were exactly double: sky-only read 36 draws against a single render's 18, and quiet run 2 gives exactly half on holes 8, 12, 18 and the hub. The summariser divides those out (rule in its docstring), and the harness now keeps the smallest non-zero read.
- **Timings:**
  - The Editor's own GPU timer counted editor drawing (an *empty* frame showed 3.5 ms), so I used two synchronous measures instead.
  - **Pixel GPU** = (render at 2× resolution − render at 1×) / 3. CPU work does not change with resolution, so this is the per-pixel GPU cost of one 1080p frame, free of editor overhead.
  - **Sync 1080p** = one synchronous render, CPU submit + GPU: an upper bound.
  - Load inflates pixel GPU by about **1.5–1.9×**: hole 8 was 1.25 ms quiet and 2.42 ms at load ~30; hole 12 was 2.10 against 3.07. Absolute numbers below are scaled to the quiet anchor. Single-slot ablation deltas are noisy (some come out negative), so group medians are used.

## 2. Baseline: what each frame costs today (M5, 1080p, 4× MSAA)

Per-slot tables: [proof/baseline.md](proof/baseline.md) (sweep, corrected counts) and [proof/quiet/run2_summary/baseline.md](proof/quiet/run2_summary/baseline.md). All 34 frames: [proof/contact_sheet.jpg](proof/contact_sheet.jpg). Raw JSON: [proof/frames/](proof/frames/), [proof/quiet/run2/](proof/quiet/run2/).

### Counts (single render, reliable)

| Place | Triangles / frame | Draw calls | Shadow casters | Characters' share |
|---|---:|---:|---:|---:|
| Golf, 16 holes | median **2.2 M** (1.4–3.3 M), **hole 12: 5.5 M** | 180–283 | 25–66 | golfer ≈ **0.54 M** |
| Tennis Resort | **2.53 M** | 376 | 85 | 2 heroes ≈ **1.06 M** |
| Tennis Skyscraper | 1.28 M | 247 | 74 | 1.06 M (**83 %**) |
| Tennis Volcano | 1.34 M | 205 | 57 | 1.06 M (**79 %**) |
| Plaza hub | 0.97 M | 252 | 134 | NPCs + player ≈ 0.76 M |

- **Characters:** each hero is ~0.53 M triangles per frame including its shadow pass. AGENTS.md's per-base budget is 35–50 k. Garments, hair and head detail carry full detail for the far player and into the shadow map.
- **Shadow pass:** 0.35–0.5 M triangles (median); 1.9 M on hole 12.
- **Weather adds almost no geometry** (+0.01–0.03 M); its cost is in pixels.

### Timings (M5)

| Scene | Pixel GPU, quiet-equivalent (ms) | Sync 1080p (ms, CPU+GPU upper bound) | Source |
|---|---:|---:|---|
| Golf hole 8 | **1.25** | 9.4 | quiet 1 |
| Golf hole 12 | **2.10** | 9.9 | quiet 1 |
| Golf hole 8, storm | ≈ 4.3 (7.39 at load ÷ 1.7) | 12.3 | quiet 2, scaled |
| Tennis venues | ≈ 1.6–1.8 (2.8–3.0 at load ÷ 1.7) | 10–12.7 | quiet 2, scaled |
| Tennis venues, storm | ≈ 2.3–2.7 (+1.0–1.8 at load) | 8.6–11.4 | quiet 2, scaled |
| Plaza hub | ≈ 1.4 (2.36 ÷ 1.7) | 5.9 | quiet 2, scaled |

### Cost drivers

| Driver | Measured | Read |
|---|---|---|
| **Golf weather layer** (full-screen cloud dome, ground fog, wet ground; rain/ash particles) | Pixel GPU **+4.97 ms** at load on hole 8 storm (quiet run 2), +3.0 to +4.1 ms on all 5 sweep slots. **About +3 ms quiet-equivalent: the per-pixel cost of a golf frame roughly triples.** | The clearest signal in the data, repeated in every golf weather slot in both runs. |
| Tennis weather | +1.0 to +1.8 ms pixel at load (~+0.6–1.1 quiet-equivalent) | Lighter view; still a full-screen layer. |
| Triangles | Quiet anchor: the resolution-independent part grows **~0.31 ms per M triangles** on the M5 (hole 8 → hole 12). Loaded sweep fit: 0.94 ms/M (r = 0.62, includes CPU). | Hole 12 pays ~1.1 ms more than hole 8 on the Mac for geometry. |
| Shadows | +0.5 to +3 ms sync (median 1.5) | Mostly CPU and vertex. Almost all scenery casts. |
| Characters | +1.1 to +2.8 ms sync | Skinning plus their shadow pass. |
| 4× MSAA | ~0.2–1 ms pixel, inside the noise | Cheap on Apple tile GPUs. **Keep it.** |
| Post (bloom + grade) | ±1–2 ms, inside the noise | Not a driver today. |

## 3. Scaling to iPhone (estimate)

Public 3DMark Steel Nomad Light GPU scores:
- **M5 (10-core) ≈ 4,000–5,000** (iPad Pro M5 3,978; MacBook Air M5 Unlimited 5,012);
- **A19 Pro 2,956**;
- **A18 Pro 2,102** (Notebookcheck).

Sustained-load stability of the iPhone 17 Pro family: **64–72 %** (GSMArena, Tom's Guide).

| Phone | Peak factor vs M5 | Sustained (20+ min) |
|---|---:|---:|
| iPhone 17 Pro (A19 Pro) | ×1.5–1.7 | ×2.2–2.6 |
| iPhone 16 Pro (A18 Pro) | ×2.1–2.4 | ×3.0–3.5 |
| iPhone 15 (A16) | ~×3 (EST; no Light score found) | ~×4+ |

M5 GPU per frame ≈ quiet pixel GPU + 0.31 ms × M triangles (vertex, skinning, shadow map). The **target** is ≤ 11 ms at peak, so a heat-soaked phone (×1.5) still makes 16.6 ms.

| Scene | M5 GPU est (ms) | 17 Pro peak | 17 Pro sustained | 16 Pro peak | iPhone 15 peak | Verdict today |
|---|---:|---:|---:|---:|---:|---|
| Tennis Resort | 1.7 + 0.8 = **2.5** | 4 | 6 | 6 | 7.5 | Fits everywhere |
| Tennis Skyscraper / Volcano | 1.7 + 0.4 = **2.1** | 3.5 | 5 | 5 | 6.5 | Fits everywhere |
| Golf, median hole | 1.6 + 0.7 = **2.3** | 3.7 | 5.5 | 5.5 | 7 | Fits everywhere |
| Golf hole 12 | 2.1 + 1.7 = **3.8** | 6 | 9 | 8.5 | 11.5 | Fits on 17 Pro; **at the limit on iPhone 15** |
| Golf in weather (hole 8 storm) | 4.3 + 0.6 = **4.9** | 8 | 12 | 11 | **15** | 17 Pro OK; **16 Pro at the limit; iPhone 15 fails** |
| Golf hole 12 in weather (not measured; sum) | ≈ 6.8 | 11 | 16 | 15 | **20** | **Fails below the 17 Pro** |
| Plaza hub | 1.4 + 0.3 = **1.7** | 2.7 | 4 | 4 | 5 | Fits |

Not in these numbers, and all of it adds:
- HUD/UI canvases;
- the device render thread (iPhone runs it in parallel with the GPU, but it must also fit 16.6 ms with 200–380 draws plus skinning);
- AirPlay encode (separate hardware, shared memory bandwidth);
- the phone's controller UI;
- **two-player split screen**: the scene draws twice, so geometry, shadow and draw costs double;
- shader warm-up hitches;
- crowds or effects that were not in the measured frame (contact VFX, confetti).

## 4. Budget left for the majestic layer

The majestic layer in PROPOSAL §5 is sky, clouds, far scenery and a landmark, global wind, life and crowd, cheap water, court detail and a weather event. It costs about **3–5 ms at peak on an A19 Pro** (EST).

| Scene | 17 Pro: room under the 11 ms target | 16 Pro / iPhone 15: room | Split screen (17 Pro) |
|---|---:|---:|---|
| Tennis venues | **7 ms**: fits the full majestic layer | 5 / 3.5 ms: fits with tier B on iPhone 15 | ~4 ms after doubling geometry/shadows: fits with LOD'd characters |
| Golf, typical hole | **7 ms**: fits | 5.5 / 4 ms: fits / tier B | fits with LOD |
| Golf hole 12 | 5 ms: fits | 2.5 / ~0 ms: needs the triangle diet | needs the diet |
| Golf in weather | **3 ms**: tight | 0 / **negative** | **negative** |
| Plaza hub | 8 ms | 7 / 6 ms | n/a |

**Conclusion:**
- On the iPhone 17 Pro the majestic layer fits everywhere except golf weather, which needs its full-screen layers replaced (R4).
- On older phones and in split screen it fits only after the make-room work (PROPOSAL §3: character LOD, shadow casters, hole 12 diet, weather in materials).

## 5. Verdict per ambition

| # | Ambition (Adnan's words → concrete) | Verdict | Why |
|---|---|---|---|
| 1 | **Majestic backdrop on every map**: rendered sky, real clouds, far scenery, a landmark you remember | **POSSIBLE** | Sky-only frames are cheap. An authored sky (chat 2's LUT sky: 1 fetch), cloud cards, low-poly distant scenery and one landmark cost ~1–1.5 ms on an A19 Pro (EST). Mario Kart World, Genshin and Sky do this at 60. |
| 2 | **Weather that feels super immersive**: rain, storm with lightning and thunder, fog, wind, snow, ash, sunsets | **POSSIBLE WITH TRADE-OFF** | Today's golf weather is drawn as full-screen layers and roughly triples a golf frame's per-pixel cost: ~+3 ms on the M5, ~+5 ms on a 17 Pro at peak, ~+9 ms on an iPhone 15 (EST). It breaks 60 below the 17 Pro and leaves no room for the rest of the majestic layer. Move wetness, snow, ash and fog into the materials (one global value each) and keep one rain layer plus a few hundred streaks: target ≤ 1 ms. Lightning, thunder, rainbow and wind cost ~0. Tennis weather wraps around play. |
| 3 | **Court and course look detailed and exquisite** | **POSSIBLE** | What reads at phone and TV distance is cheap (0.1–0.3 ms): mow stripes, wear that grows through the match, clay scuffs swept between sets, crisp lines, a bright net band, sheen. Micro-detail is invisible on both screens (note C §3.1), so "detailed" means big value bands and story. |
| 4 | **A living world**: crowds that react, birds, boats, balloons, flags, palms in the wind | **POSSIBLE** on 17 Pro / **WITH TRADE-OFF** on older phones and split screen | Instanced crowd with baked loops, half-rate far animation and one global wind ≈ 1 ms. On older phones and in split screen, budget comes from the characters (1.06 M triangles for two today): far-player LOD and a light shadow mesh. |
| 5 | **Time of day / sunset moods** | **POSSIBLE** | Parameter lerps (sun colour, ambient, fog, grade, sky LUT) from one curve. A moving key light with real-time GI is **NOT POSSIBLE**; keep it steady, as Mario Kart World does. |
| 6 | **Real volumetric clouds, scattering god rays, ray-marched fog** | **NOT POSSIBLE** at 60/1080p sustained | Per-pixel ray-marching across the screen; even consoles fake it. Use cloud cards, light-shaft cards and height fog. |
| 7 | **Real reflections** (planar water, SSR puddles) | **NOT POSSIBLE** in the play view | A second scene render or a full-screen pass with a colour copy. Sky-LUT/cubemap reflections and baked-depth water look right at this distance. |
| 8 | **Dense real grass / simulation foliage** (Ghost of Tsushima-style blades) | **NOT POSSIBLE** | GPU blade grass is console-only. Shell or card grass at court and fairway edges is **POSSIBLE** (0.3–0.8 ms). |
| 9 | **More geometry for richness** (hole 12-style 5 M+ triangle scenes everywhere) | **NOT POSSIBLE** on the phones below the 17 Pro, and wasteful on it | Hole 12 is already at the iPhone 15's limit, and in weather it fails below the 17 Pro (EST). Richness has to come from layers, light and motion, at ≤ 1.5 M submitted triangles per frame. |
| 10 | **Diorama / tilt-shift feel** | **POSSIBLE WITH TRADE-OFF** | Intros, flyovers and replays only (0.8–1.5 ms). Never on the play camera; that is Link's Awakening's 60→30 lesson. |
| 11 | **Same look in two-player split screen** | **POSSIBLE WITH TRADE-OFF** | Geometry, shadow and draw costs double. Needs character LOD, impostor far layers and half-rate life as split defaults. Measure on device. |
| 12 | **Same look on older phones** (iPhone 15/16) at 60 and 1080p | **POSSIBLE WITH TRADE-OFF** | 1.4–2× slower GPUs (EST). Keep 60 and 1080p by shedding effects: cloud shadows, crowd rate, bloom iterations, rain density. Never shed resolution: MetalFX upscaling from below 1080p would break Adnan's floor. |
| 13 | **Majestic and 120 fps** | **NOT POSSIBLE** (out of scope) | No benchmark game sustains 120 with a rich look; Genshin's 120 doesn't hold on a 15 Pro Max. |

## 6. What must be true before the majestic work starts

1. **A device baseline exists (P0).** An iPhone 17 Pro and one older phone; all venues, hole 12 and golf weather; a 20-minute heat soak; Metal HUD plus an `xctrace` GPU trace. This replaces every estimate above.
2. **Golf weather is rebuilt inside the materials.** It is the only measured cost large enough to break 60 on its own on the phones below the 17 Pro (EST).
3. **Characters fit a budget.** Far-player LOD and a shadow mesh, aiming at ≤ 300 k triangles for two characters including shadows. This buys the room for split screen and older phones.
4. **Hole 12 and the 3 M+ holes are cut** to ≤ 1.5 M submitted triangles.

## 7. Proof index

| File | What |
|---|---|
| [proof/baseline.md](proof/baseline.md), [proof/baseline.csv](proof/baseline.csv) | Sweep: 34 slots, single-render counts, timings at load, group medians, weather deltas |
| [proof/quiet/run2_summary/baseline.md](proof/quiet/run2_summary/baseline.md) | Quiet run 2: 11 slots |
| [proof/quiet/partial_from_lost_run.md](proof/quiet/partial_from_lost_run.md) | Quiet run 1: timing anchor (log lines; JSON lost in a reboot) |
| [proof/contact_sheet.jpg](proof/contact_sheet.jpg) | All 34 sweep frames. The labels show the uncorrected counts; use the tables. |
| [proof/frames/](proof/frames/), [proof/quiet/run2/](proof/quiet/run2/) | Raw harness JSON (every variant, every counter, scene inventories) and quiet-run frames |
| [tools/](tools/) | Harness, runner, summariser; re-runnable in any clone |
