# PLAN — Bowling venues (2026-10-25)

Ask (Adnan, 10-25): make more bowling maps with solid lighting and unique settings; they have to look and feel different.

Inputs:
- `work/bowling-venue-refs/ALLEYS.md`: PBA TV sets, Lucky Strike, Bowlero, Brooklyn Bowl, Round1, the Seoul neon centre, LED masking walls, lane projection.
- The brand guide (navy/royal/gold, the swing arc).
- The other sports' venues: tennis has Resort, Skyscraper and Volcano; golf has Cliffside, Wild Isles and Magma.

## 1. The line-up: four venues, four different nights out

| # | Venue | Setting | Time / mood | Light idea in one line | Ties to |
|---|---|---|---|---|---|
| 1 | **Club Lanes** (exists) | Sky lounge at the top of the club tower | Sunset, upscale | Bright stage-lit lanes in a navy room; sunset through glass | Tennis Skyscraper sky, brand navy/gold |
| 2 | **Neon Nights** | Cosmic bowling hall | Midnight, party | Blacklight: the room is dark, everything glows; cyan/magenta ceiling grid, per-lane LED totems, glowing pins and balls | The tagline "Neon lanes, perfect strikes"; Seoul neon centre ref |
| 3 | **Tiki Shores** | Open-air lanes under a beach pavilion roof | Late afternoon, holiday (the only daylight venue) | Warm sun raking in from the sea side, pergola-slat shadows striping the lanes, blue sky fill, lanterns warming up | Tennis Resort / golf Wild Isles; the SportsLibrary coastal concept |
| 4 | **Magma Lanes** | Lanes carved into a volcano | Night, epic | Lava below the gutters lights everything from beneath in orange; cold blue moonlight from a crater opening above; embers | Tennis Volcano / golf Magma |

Each venue differs on every axis a player feels at TV distance:
- the colour of the light;
- where the light comes from (above, sun-side, below, everywhere-glow);
- indoor vs. outdoor;
- what is behind the pins;
- what the crowd sits on;
- the sound bed (later, audio pass).

### Later candidate, not in this pass
**Starlite Bowl:** a 1960s googie Americana alley with tungsten warmth, a checker floor, red banquettes and a neon script.

## 2. What stays the same (shared lane kit)

The regulation lane, gutters, capping, kickbacks, pin deck, shadow box, markings, pins, ball, physics and HUD are shared. Every venue gets:
- **the same camera shots**;
- **the same light budget**: the main directional light is the key, and each pin has 2 additional-light slots (deck spot + face light; TennisURP limits objects to 2 additional lights);
- **two reflection probes**: lanes and pin deck;
- **a post volume**: bloom, ACES, grade, vignette.

Code (as built 10-25):
- `BowlingVenue.cs`: `enum BowlingVenueKind { ClubLanes, NeonNights, TikiShores, MagmaLanes }`, `Selected`/`Parse`/`Current` (as `TennisVenue` has; `BOWL_VENUE` forces one), `Build()` dispatch, shared dressing helpers (faceted `Rock`, `Palm`, `Combine`, `Additive`, `Settee`, `Ambient`, `Fog`), and `BowlingVenueFx` (lava scroll, LED pulse/cycle, torch flicker, strike flash).
- The shared lane kit lives in `BowlingClubLanes.cs`: `LaneTheme` + `Lanes()` build the five lanes with per-venue materials; `Key()`, `BowlerLights()`, `Probes()` and `Post(PostLook)` give every venue the same light budget with its own colours and grade.
- One builder per venue: `BowlingClubLanes.Build`, `BowlingNeonNights.cs`, `BowlingTikiShores.cs`, `BowlingMagmaLanes.cs`.
- Selection: the launch JSON's `venue` key. `NativeSportsSession.Load` sets `BowlingVenue.Selected` beside the existing `TennisVenue.Selected` line. `BowlingGame` calls `venue.Fx.Strike()` on every strike.
- Proof: `work/bowling/tools/venues.sh` films every venue (`BOWL_FILM_STILLS=1`: setup, wide, side, pins, lounge, react, ball stills + `meta.json`) and runs `light_gate.py`.

## 3. Per-venue design

### 2. Neon Nights (cosmic)
- **Room:** near-black walls (N900), a ceiling lattice of thin cyan and magenta light lines, and a mirrored-black floor behind the approach.
- **Lanes:** dark-stained lanes with a faint UV-reactive star pattern. The lane-guard LEDs alternate cyan and magenta per lane. A vertical LED totem stands at the foul line of each lane.
- **Masking:** a single LED wall across all lanes, with scrolling brand arcs in cyan/magenta/gold that flash gold on strikes.
- **Pins:** "blacklight" pins, white with a faint cyan glow (emission 0.35). Balls glow on the return.
- **Crowd:** lounge sofas with fans, side standing rail, haze.
- **Light:**
  - key: a low-intensity violet main light, high and frontal;
  - ambient: deep violet;
  - pin deck: a UV spot (violet-white);
  - fog: violet;
  - post: strong bloom (0.7 threshold), +15 saturation, a cool white balance.

### 3. Tiki Shores (beach, late afternoon)
- **Structure:** a thatched pavilion roof over the approach and the lounge, a slatted pergola over the lanes (the sun stripes the wood through it), open at the sides onto sand, palms and the sea.
- **Furniture:** wooden kickbacks, rope-wrapped posts, tiki torches (emissive flames) and paper lanterns.
- **Masking:** carved wood boards with a painted sunset and a palm silhouette.
- **Backdrop:** the Luminous Coast archipelago panorama (sea, karst islands, clouds) past the sand, with palm groves along the sides.
- **Crowd:** on driftwood bleachers in the sand on both sides, plus a beach-bar lounge behind the bowlers.
- **Light:**
  - key: the sun, 34° up, warm, from the sea side and a little behind (lower and the bleachers' shadows cover the main lane);
  - shadows: palm and roof-slat shadows striping the lanes (cookie-free, from real geometry);
  - ambient: a sky/equator/ground trilight (sky blue, warm sand bounce);
  - pin deck: a warm spot under the roof;
  - post: a warm grade with gentle bloom.

### 4. Magma Lanes (volcano)
- **Room:** a basalt cavern (faceted dark rock); the lanes sit on obsidian slabs.
- **Lava:** a glowing lava channel runs **under** each gutter and along the walls (emissive orange, animated flow), with embers drifting up.
- **Masking:** a basalt arch with glowing magma cracks and a gold brand crest.
- **Above:** a crater opening in the ceiling showing the volcanic sky panorama, with cold moonlight streaming down through the opening.
- **Crowd:** on carved rock terraces with lava-lit edges.
- **Light:**
  - key: moonlight (cool blue-white, high, from the crater);
  - lava bounce: from below (orange, via ambient ground colour plus emissive);
  - pin deck: a hot white spot;
  - post: an orange/teal grade with strong bloom on the lava.

### 1. Club Lanes (refine, from the ALLEYS steal list)
- A navy **LED masking strip with a gold crest** that flashes gold on strikes.
- **Brass marquee lane numbers.**
- **Tufted navy-leather banquettes** in rows behind the approach.
- Gold-edged ceiling coves.

## 4. Lighting gates (binary, measured on captures; every venue)

Shots: setup, pin cam, reaction and wide. All at 1280×720, measured with `work/bowling/tools/light_gate.py` on mean luma (0–1).

| Gate | Measure | Pass |
|---|---|---|
| L1 Lane reads | mean luma of the main lane bed in the setup shot | 0.30–0.75 |
| L2 Pins pop | pin-body luma ÷ the masking/shadow-box luma behind them, in the pin cam | ≥ 3.0 |
| L3 Pins not clipped | share of pin-body pixels ≥ 0.98 | ≤ 15 % |
| L4 Bowler face | head-region luma in the reaction shot | 0.25–0.80 |
| L5 Distinct | mean colour (hue, sat, luma) of the setup shot against every other venue | ΔE (Lab) ≥ 20 to each |
| L6 Ball visible | ball vs. local lane contrast during the roll | ≥ 1.4 |
| L7 HUD legible | the score plate area is not brighter than 0.6 behind it | pass |
| L8 Perf | draw calls ≤ 180 and on-screen tris ≤ 450k in the setup shot (editor stats) | pass |

Proof for each venue goes in `work/bowling/proof/venues/<venue>/`: four shots plus a 1-ball GIF, and `GATE_RESULTS.md`.

## 5. Order of work
1. Venue system and shared lane kit. Move Club Lanes onto it (no visual change).
2. Neon Nights, the most different from Club Lanes.
3. Tiki Shores.
4. Magma Lanes.
5. Club Lanes refinements.
6. Lighting gates for all four; Adnan picks his favourites.
7. Integration (P5): a venue picker on the phone and the plaza bowling bay. Not in this pass.

Rules: one Unity job at a time through heavy.sh, short films (`BOWL_FILM_SHOTS`), no AssetPostprocessor, no edits to `TennisURP`.
