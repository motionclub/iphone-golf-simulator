# Menu background — GATE RESULTS (2026-10-26)

Branch `menu/background-2026-10-26` (worktree `~/Documents/Codex/2026-10-26/menu-background`), base origin/main `59aeee0a62`.
Scope: the plaza behind the pointer menu (buildings, materials, lighting, the hub camera's render settings). MenuHud / Brand /
Swift / hero code untouched; MenuStage / MenuShots read only.

Final runs: flicker/z-fight from `after4`, shots and look from `after5` (= the staged code). All renders are real Unity captures (`tools/MenuBackgroundCapture.cs`, editor PlayMode in an APFS clone, the phone's own
start message with `menu = true`), every MenuShots shot at the TV's 1920x1080 with the pipeline's MSAA 4x (= the iOS High
tier: MSAA 4, 60 m / 1 cascade / 4096 sun shadows). BEFORE = origin/main run through the same harness (`before2`).

## Root causes

1. **Flicker = z-fighting, exposed by the menu camera's idle drift** (MenuStage breathing, 1–2 cm). Faces in exactly the same
   plane, found by `tools/coplanar.py` over a world-space dump of the plaza meshes:
   - house plinths stood 7 cm proud = exactly the depth of the arch surround (CLUBHOUSE) and the shop's navy kick panels (LOCKER);
   - the LOCKER sign's gold frame shared the entablature's front plane (the sign "lost" its frame every other frame);
   - MOTION CLUB sign frame top = cornice top; hip-roof side fascias overlapped the front/back fascias at every corner;
   - pennants overlapped the bunting rope's band in its own plane (a dotted flicker along every string);
   - hedge foot top = plaza kerb top; bunker dish dipped into the putting green; PLAY hall/portico plinth tops met.
   Shadows were not the cause (still-camera sequences were clean); a golf-left shadow setup was a phone-only risk (below).
2. **No sky in the menu**: the sky dome (radius 760 m) lay outside MenuStage's 600 m far clip, so the menu showed the hub
   camera's flat peach clear colour.
3. **Low detail**: facades were plain URP Lit with 256 px greyscale tint textures and no relief; windows were flat yellow glow.
4. **Phone-only**: the plaza inherited golf's 180–320 m, 2–4 cascade sun shadows when golf had run first
   (`TennisQuality.SetGolfShadows(true)`); the plaza now sets its own (`SetGolfShadows(false)` in `HubArt.Lighting`).

## Gates

| Gate | Measure | Before | After | Result |
|---|---|---|---|---|
| FLICKER_BUILDINGS low | building-pixel pops, 120 frames at 60 fps, breathing camera (mask eroded 2 px) | 254,933 (2,160/frame) | 737 (6.2/frame) | **PASS** |
| FLICKER_BUILDINGS close | same | 231,517 (1,962/frame) | 394 (3.3/frame) | **PASS** |
| FLICKER_BUILDINGS arrival | same | 69,312 (587/frame) | 874 (7.4/frame) | **PASS** |
| FLICKER_DRIFT_ADDS_NOTHING | breathing mean ≤ still-camera mean + 5 pops/frame (still = aliasing/sway floor) | low +2,158 / close +1,960 / arrival +581 | low +4.0 / close +0.9 / arrival +1.1 | **PASS** |
| FLICKER_WHOLE_FRAME low | all pixels (incl. trees/pennants swaying), breathing | 268,529 | 6,151 (after3) | **PASS** (≥ 95 % fewer) |
| ZFIGHT | coplanar overlapping faces of *different* materials, ≥ 0.01 m² (`coplanar.py`) | 6 material pairs (2.7 m² sign frame/entablature, 1.07 m² arch/plinth, 0.72 m² kick panel/plinth, 0.43 m² hedge/kerb, 0.19 m² bunker/green, 0.06 m² sign/cornice) + 0.71 m² pennant/rope (vertex colours) | 0 (largest 0.0036 m², a bench top seen from above) | **PASS** |
| SKY | the sky dome inside the menu camera's far clip from every shot (560 m + ≤ 25 m camera offset < 600 m) | 760 m: clipped, flat clear colour | rendered sky + clouds in every shot; sea + headlands kept | **PASS** |
| SHADOWS_OWN | plaza sets its own sun shadows regardless of the scene before it | inherited golf's | `SetGolfShadows(false)` at plaza build | **PASS** (code; phone run not done) |
| GPU_COST | ms per 1920x1080 MSAA 4 render, home shot (M5 GPU, shared with other jobs: noisy) | 9.40 (7.2–9.4 across runs) | 5.6–7.5 across runs | **PASS** (≤ +10 %) |
| SMOOTH | p95 frame ≤ 16.7 ms on each menu screen and camera move (Mac standalone player, uncapped) | 3 of 9 phases over | 1 of 9 over (arrival 21.1 ms) | **FAIL** (arrival; see below) |
| LOOK | before/after per shot (`proof/after/before_after_*.jpg`) | | | **Adnan** |

Frame stats per render (after): ~300 batches, 57 SetPass, ~1.0 M triangles on the home shot (before: 310 / 57 / 1.0 M).

## SMOOTH (frame time)

Measured in a **macOS standalone player** (no editor; `tools/player/`, Mono, M5 Mac, 1920x1080 windowed, MSAA 4, the
High tier's shadows), booted with the phone's own start message and walked Arrival → Home → Sport → Tennis modes → Locker
→ Home with the pointer drifting. Uncapped (each frame's interval = its cost). BEFORE = origin/main built the same way,
run back to back under the same machine load (the Mac was running 1–3 other heavy jobs: `proof/smooth/*_machine_load.txt`).
**No phone or TV run** (needs Adnan's OK for a device install).

| Phase | BEFORE p50 / **p95** ms | AFTER p50 / **p95** ms | AFTER GPU p95 | ≤ 16.7 ms p95 |
|---|---|---|---|---|
| arrival swoop | 5.5 / **21.3** | 5.5 / **21.1** | 5.3 | **FAIL** (both) |
| home (still) | 5.7 / **17.3** | 4.9 / **14.2** | 6.7 | PASS (before FAIL) |
| move → sport | 5.9 / **18.8** | 4.9 / **16.7** | 6.0 | PASS (borderline; before FAIL) |
| sport (still) | 5.9 / 11.0 | 5.0 / 10.2 | 10.5 | PASS |
| tennis modes (still) | 6.1 / 15.9 | 5.3 / 8.6 | 11.0 | PASS |
| move → locker | 5.8 / 15.8 | 5.1 / 9.7 | 10.1 | PASS |
| locker (still) | 6.1 / 15.4 | 5.7 / 11.6 | 9.3 | PASS |
| move → home | 6.5 / 11.5 | 6.0 / 16.5 | 8.0 | PASS |
| home again (still) | 5.8 / 12.3 | 5.8 / 9.4 | 6.6 | PASS |

(Sport → Tennis modes is the same Close shot: no camera move to measure.) GC allocated per frame: **0 bytes** in every
phase, before and after. **SMOOTH: FAIL on the arrival swoop** (p95 21 ms, unchanged by this work). The slow frames are
spread evenly through every phase rather than at screen changes or shot starts (`player-*_frames.csv.gz`), which looks like
CPU contention from the other jobs on this Mac rather than menu work; the medians (5–6 ms ≈ 170 fps) leave headroom. Only a
phone/TV run can confirm the real 60 fps budget.

Editor PlayMode profile (origin/main, `proof/smooth/editor_before_frametime.txt`): per-script A/B shows no game script
allocating per frame (the 0.7–1 MB/frame the editor reports is its own GameView/IMGUI); screen-change hitches came from
MenuHud (CanvasGroup AddComponent 2.5 ms, single-canvas re-batch 3–4 ms) and ~1 ms/frame each in HubHeroAnimator, HeroLod,
KitV2PoseCorrectives LateUpdate. All of those belong to the main chat, which applied the MenuHud fixes in
`menu/tv-flow-2026-10-26`. This branch's own render changes kept the GPU cost flat or lower (GPU_COST above).

## What changed (files)

- `Unity/Assets/Scripts/Hub/HubArt.cs` — z-fight offsets (plinths, LOCKER/MOTION CLUB signs, PLAY plinth tops, bunker), sky dome
  560 m, plaza resets golf shadows, bloom high-quality filtering, lit-room windows on the houses and PLAY hall, far headlands
  hazed into the warm horizon.
- `Unity/Assets/Scripts/Hub/HubClub.cs` — hip-roof fascia corners, hedge foot; `LitTex` on the new HubFacade shader;
  `Relief()` bakes a normal + cavity map from each painted texture; relief on textured ground (`Surface`); 512 px stone,
  slate, cobbles, flagstones, 256 px planks; richer stone (per-block warm/cool, pits); `RoomInterior` + `WindowRoom`.
- `Unity/Assets/Resources/Hub/HubFacade.shader` (new) — URP PBR + relief (screen-derivative tangents, no mesh tangents),
  cavity, weathered wall foot, macro variation; no keywords of its own (runtime materials never lose a stripped variant).
- `Unity/Assets/Resources/Hub/HubSurface.shader` — optional relief (normal + cavity) for the paving and lawns.
- `Unity/Assets/Scripts/Majestic/MajesticMesh.cs` — pennants hang below the rope, 4 mm off its plane (also fixes the same
  flicker on the skyscraper venue's bunting, which uses this builder).

## Proof

- `proof/before/` — origin/main: 5 shots, flicker heat maps, the LOCKER z-fight in 4 consecutive frames, coplanar scan, costs.
- `proof/after/` — `before_after_<shot>.jpg` (5 shots), building flicker heat maps, the same 4 frames, coplanar scan, costs.
- Tools: `tools/run.sh` (sync + capture through heavy.sh; `MB_REPO` measures another checkout), `MenuBackgroundCapture.cs`,
  `MenuFrameTime.cs`, `flicker.py`, `gates.sh`, `coplanar.py`, `sheet.py`, `player/` (standalone-player SMOOTH run).

## Not done / notes

- No phone or TV run (needs Adnan's OK for a device install); SMOOTH uses a macOS standalone player as the proxy.
- The Majestic bunting crosses the MOTION CLUB sign in the home shot (composition, not a bug): left as is.
- Arrival swoop only: the far headlands are still flat silhouettes (now hazed), and a cloud card's lower edge shows top right
  (both present before this work).
- `proof/before/report.txt` (first run) has cumulative frame stats; `report_before2.txt` is the comparable one.
- Heroes (not mine): HubHeroAnimator / HeroLod / KitV2PoseCorrectives LateUpdate cost ~1 ms each — sent to the main chat.
