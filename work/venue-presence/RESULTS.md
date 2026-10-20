# RESULTS — venue presence (sky and volcano)

**GATE: VENUE_PRESENCE PASS** (all eight gates, evidence below; known gaps at the end are not gate failures)

Open first: `proof/sheet_skyscraper.png` and `proof/sheet_volcano.png` (shipped capture on the left, new capture on the right, seven views each, measured numbers underneath).

| gate | verdict | evidence |
|---|---|---|
| AUDIT_WRITTEN | PASS | `AUDIT.md`: cites the screenshots by name, confirms each of the brief's complaints with a cause (UV stretch 3:1 on the crater wall, the 5.4 degree rule that hides a flat cloud sea, 18 resort props = 78% of the kit) |
| PLAN_WRITTEN | PASS | `PLAN.md`: every item names the reference-game idea it steals and how it is adapted; an "as built" section at the end lists every deviation |
| COURT_UNCHANGED | PASS | `GATE_RESULTS.txt`: `TennisVenue.cs` (deck half extents 12.6 / 21.6, `OverDeck`, `Drone` path and its end pose) is the same file, SHA-256 identical. All 10 kept court-kit objects (court, 4 lines, posts, net, apron, chair) have identical centre and size to 0.000 m on both maps. The painted lines land on the same pixels as in the shipped frames (score 94 to 100% vs 97 to 100% shipped; a deliberate 4 x 3 px shift drops it to 31%, so the test would notice) |
| SKY_HEIGHT | PASS | Solid, lit cloud sea 58 m under the deck (43,776 tris) with 229 cumulus lumps on it; towers enter it through cloud collars. Edge, below and drone rows of the sheet show the drop. 34 towers in 6 facade families (separate textures and window masks), 9 distinct tops, one landmark (Saucer Tower), a skybridge pair |
| VOLCANO_LIGHT | PASS | The same patch of floor on the slab's outer 2.2 m: warmth (red minus blue) -0.05 / -0.03 -> +0.18 / +0.22, red 0.16-0.19 -> 0.41-0.45 (gameplay frame; postcard matches). Near rock is lava-lit too: basalt columns 14 m out glow from their base with hot rims, the keel glows in its cracks, a molten channel runs round the slab. The far wall behind the baseline is deliberately the quietest part |
| NO_RESORT_CLUTTER | PASS | Kit dump: 0 of the 18 resort-dressing renderers (TropicalV3_017 planters, _020 sofas, _033 lanterns; 108,228 tris) are enabled on either map. Replaced by rooftop kit (tank, air handlers, vents, masts, windsock) and obsidian pylons |
| PROOFS | PASS | `proof/sheet_skyscraper.png`, `proof/sheet_volcano.png`; raw frames in `proof/after/` (the shipped set plus `7_rear` and `8_rivalintro`); the unchanged code recaptured in `proof/baseline/` matches the shipped frames to 0.2-1.6 / 255 |
| PLAY_SAFE | PASS | `GATE_RESULTS.txt`: `TennisGame`, `TennisBall`, `TennisPresentation`, `TennisRules`, `TennisReplay`, `TennisActor`, `TennisPhoneInput`, `TennisLook`, `TennisOpponent`, `TennisVenue` are byte-identical to the hashes taken before the work (`before_code/play_files.sha256`) |

## What was built

**Sky.** A solid cloud sea and cumulus banks instead of alpha sheets; a skyline of 34 towers in 6 facade families with a landmark; a baked twilight dome (thin hot horizon line, magenta to violet to indigo, banded sun, huge cloud ribbons); rooftop kit in place of the beach-club props.
**Volcano.** A five-terrace bowl with arc-length UVs (the wallpaper stretch is gone) and eight lavafalls; basalt columns standing in the lake; a molten channel and an orange edge light on the slab; a rock keel; a baked dome with smoke billows; the eruption plume moved to a place a camera can see; six obsidian pylons; trees, grassland and the unseen sea removed.

## Numbers (all from `tools/`, generated into `GATE_RESULTS.txt` and the sheet footers)

| | sky before -> after | volcano before -> after |
|---|---|---|
| Triangles owned by the venue | 12,164 -> 142,534 | 1,591,200 -> 103,652 |
| Arena kit triangles (resort props hidden) | 138,607 -> 30,379 | 138,607 -> 30,379 |
| Whole static scene | 150,771 -> 172,913 | 1,729,807 -> 134,031 |
| Build time, Editor (Mono) | 441 -> 389 ms (sky dome 246 ms, first match only) | 1,984 -> 1,302 ms |
| Ball vs background, lob band, median (gameplay) | 1.47:1 -> 1.97:1 | 7.70:1 -> 7.98:1 |
| Share of lob band under 2:1 (gameplay) | 91% -> 52% | 2.1% -> 2.6% |
| Active lights | 2 -> 2 | 9 -> 9 (unchanged, none added) |

The "before" triangle counts and build times were **measured** by running the original builder through the same dump tool (`tools/baseline_swap.sh`), not estimated.

## Reproduce

```
work/venue-presence/tools/capture.sh <out_dir> skyscraper volcano       # compile pass, then one capture per venue (Unity must be closed)
HERO_VENUE_DUMP=1 HERO_VENUE_DUMP_KIT=1 ...                             # also logs the kit and triangle dump
work/venue-presence/tools/run_gates.sh                                  # every automated check, writes GATE_RESULTS.txt
python3 work/venue-presence/tools/write_sheet_notes.py && python3 work/venue-presence/tools/make_sheets.py ArtDir/screenshots/venues work/venue-presence/proof/after work/venue-presence/proof
```
Capture env switches (editor only): `HERO_VENUE_OUT` (default is the shipped ArtDir folder, so always set it for proofs), `HERO_VENUE_DUMP`, `HERO_VENUE_DUMP_KIT`, `HERO_VENUE_HIDE`, `HERO_VENUE_ONLY`.

## Rollback

`before_code/` holds the originals (SHA-256 in `before_code/SHA256.txt`). To go back: copy `TennisVenueBuilder.cs.before` over `TennisVenueBuilder.cs` and `TennisVenueFx.cs.before` over `TennisVenueFx.cs`, delete `TennisVenueBuilder.Mesh.cs`, `.Skyscraper.cs`, `.Volcano.cs` and their `.meta`. The capture tool's original is `git show HEAD:Unity/Assets/Editor/TennisVenueCapture.cs`. The working versions are also in `after_code/`. Nothing was committed.

## Files this work touched

New: `TennisVenueBuilder.Mesh.cs`, `TennisVenueBuilder.Skyscraper.cs`, `TennisVenueBuilder.Volcano.cs` (+ `.meta`). Edited: `TennisVenueBuilder.cs` (now a `partial class`; helpers, kit list, the old sky and volcano removed), `TennisVenueFx.cs` (two new components, `Sway`, `FallFlow`), `Editor/TennisVenueCapture.cs` (env switches and the dump). Not touched: `TennisVenue.cs`, `TennisGame.cs`, anything in `ArtDir/`, any hero, clothes or racket file. (`git status` lists `TennisVenue.cs` and `TennisGame.cs` as modified: both carried another session's uncommitted edits before this work began, a doc comment and the recording events; their hashes are unchanged by this work.)

## Known gaps (stated, not hidden)

* **Not run on a phone.** Every timing is an Editor (Mono) timing. The Low quality tier (fewer lumps, wisps and steam vents) compiles but was not rendered.
* **The sky's ball contrast is 1.97:1 against the plan's own 2.0:1 target** (1.79:1 on the postcard); the sunlit cloud tops at the horizon stay brighter than the ball on purpose, they sell the height. The first draft of the sky (gold and coral bands) scored 1.44:1, no better than before, which is why the final palette is deeper.
* **Materials.** Every solid surface is URP Lit. The sky domes, the sun, the apron-edge glow card, flames and particles use the project's existing alpha and additive FX shaders, as the original venues did; no shader or asset was added.
* The volcano's court interior is a little warmer after the change (warmth -0.01 -> +0.04): bloom spills off the new emissive surfaces. Ball contrast on it did not drop (7.70 -> 7.98).
* The volcano's 9 active lights (sun, fill, two lava lights, slab glow, four braziers) are as they were; only the first two pixel lights per object run on device. Cutting them is a separate decision.
* The shipped shots in `ArtDir/screenshots/venues` are left as they were (they are the "before"). Resort is untouched: no small fix was needed for any gate.

## Things worth remembering next time

* From the gameplay camera the deck edge hides everything steeper than about 5.4 degrees below the eye, so a cloud sea or lava lake must be within roughly 60 m of the deck to be seen from play.
* The ball is a bright yellow-green (hue 67, S .65, V .7-.9). Any bright sky or cloud sits at about 1.3-1.5:1 against it; and an HDR emission with red above 2 and green near 1 tone-maps to **yellow**, which reads as a second ball (pylon caps and embers did). Keep emission green below about 0.4 x red.
* Particle systems made in code start playing before they are configured, so `prewarm` never happens; stop, clear and play once configured.
* The drone lands 1.4 m outside the deck's near corner: anything wider than the deck footprint there is seen edge-on from above.
* A statically batched mesh reports the combined mesh from every member: dedupe before counting triangles.
* Baking a sky dome per pixel is the slow part of the sky build: hoist noise that does not depend on the inner loop, cache per-column noise, bake at 1024 x 256 (it is magnified about 8x on screen anyway).
