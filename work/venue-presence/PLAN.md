# PLAN — venue presence (sky first, then volcano)

Follows `AUDIT.md` (same folder). Everything below is built in `TennisVenueBuilder` (new code lives in `partial class TennisVenueBuilder` files next to it so the edits to the shared file stay small, because another session has uncommitted work in it). Materials stay URP Lit for solid surfaces; the existing FX shaders (`TennisFxAlpha`, `TennisFxAdditive`, which read vertex colour) are used only for sky dome, glows and particles.

Each item says what it **steals** and how it is **adapted to this soft look**. "Not photoreal, not grim": flat-shaded facets, soft gradients, saturated but friendly colour, no logos, no text.

## Hard rules for the build (from the brief and the audit)

* **Court, deck and play are not touched.** `TennisVenue.cs` is not edited at all (deck extents, `OverDeck`, colours, `FarClip`, `Drone` path and end pose stay byte-identical). `TennisGame.cs`, `TennisBall.cs`, `TennisPresentation.cs`, `TennisRules.cs`, `TennisReplay.cs` and the actors are not edited (hashes recorded in `before_code/play_files.sha256`, re-checked at the end). Kept kit (court, lines, posts, net, run-off apron, umpire chair) is not moved; only the resort dressing is hidden.
* **No new real-time lights.** The URP asset allows 2 additional lights per object and the characters already use them; lava and dusk "light" is emission, glow cards and baked gradients. The existing slab glow point light and four brazier lights stay as they are.
* **No new gameplay maps, no hero/clothes/racket edits, no ArtDir hero blends, no vgpu install, no logos or lettering.**
* **Budget (disclosed, measured with `HERO_VENUE_DUMP=1`):** sky venue-owned from 12,164 to **at most 160k triangles**; volcano venue-owned from ~1.59M to **at most 260k**. Hiding the 18 resort props removes 108,228 triangles from each map. Net change per map is reported in the final answer.
* **Ball readability is tracked, not traded away.** Target on the sky: median ball-to-background contrast in the lob band rises from 1.47:1 to 2.0:1 or better. Volcano: keep at least 90% of the lob band at 2:1 or better (today 97.9%) while adding glow.

---

## A. SKYSCRAPER

**S1. A real cloud sea under the deck, and cloud banks at deck level.** *Steals: Mario Kart "course above the clouds", where solid pillowy cloud is the floor and rim of the world.* The audit's 5.4 degree rule says a flat sea 370 m down cannot be seen from play, so the cloud surface moves up to y = -58 m and is built as an opaque lit heightfield with cellular "pillow" billows (15-40 m high, creases between them), 22k vertices in polar rings (10 m cells near, 250 m far). Colour comes from a baked height ramp: warm cream on tops, lavender in the shade, indigo in the valleys, lit by the venue's sun so lit sides face the sun. On top of it, clusters of icosphere lumps (merged into a few meshes) form cloud banks that rise to deck height and above at 300-1800 m, so the horizon band in `skyscraper_1_gameplay` is solid 3D cloud with a lit side and a shadow side, not stickers. Collars of lumps wrap each tower base where it enters the sea. The four alpha sheets, 150 cumulus sprites, 20 horizon sprites and the 380 city boxes are deleted (the city is below the new sea and no longer visible). Wisps become a few low 3D lumps that never pass between the camera and the court.
*Adaptation:* smooth marshmallow shading, no texture noise, a three-colour ramp.

**S2. A tower family instead of one cloned curtain wall.** *Steals: the rooftop-game height read: a few unique towers, setbacks, a mast, one odd silhouette, window variation.* About 30 towers at 90-1800 m, built from one mesh builder, with **six facade materials** (blue glass with spandrels; cream stone with punched windows; terracotta brick; mint ribbon windows; charcoal glass with gold fins; lavender and white with coral bands), each with its own lit-window emission mask, per-tower UV offsets so no two windows patterns match, and window size fixed in metres. **Nine silhouettes:** ziggurat, crowned parapet, observatory dome, slant-cut roof, needle, helipad ring, roof garden, twin towers with a skybridge, round drum with ring balcony. Placement is deterministic and tested against the drone path (no tower whose roof is above the camera within 12 m of any sampled path point). Shafts run below the sea so no base is visible. The deck's own tower gets coral and gold bands and a lit crown so it reads from the drone and side views.
**The landmark: a "Saucer Tower"** (needle shaft, flat lit saucer with a glowing window ring, spire with the existing blinking beacon) 300 m out, slightly left of the +z axis so it sits in the gameplay and postcard frames and in the rival-intro shot; the twin skybridge towers sit on the -z side for the player intro. *Adaptation:* toy-like proportions, chunky setbacks.

**S3. A sky that belongs to the map.** *Steals: Splatoon stage skies, a bold gradient plus a few huge shapes.* Replaces the peach gradient with a baked 2048 x 256 dome texture: toon-stepped bands from gold at the horizon through coral and orchid to violet and an indigo zenith (twilight over the clouds), a banded giant sun with rings, a few huge flat cloud ribbons with gold under-rims, cirrus streaks and faint stars near the zenith. The mid-sky is deliberately deeper than the old peach so a lobbed felt-yellow ball keeps contrast (tracked metric). Fog colour is matched to the horizon band; fog start moves in so towers at 300-1800 m step back in tone.

**S4. Rooftop, not terrace.** *Steals: Mario Tennis / Wii Sports Resort: the court stays clean, spectacle is outside it.* Hide the 8 lanterns, 6 sofas and 4 planters (TropicalV3_033/020/017) on this map and replace them with rooftop kit placed only in the stone margin, never on the apron or lines: a wooden water tank (the classic roof landmark), an air-handler cluster, vent stacks, a stair bulkhead, a windsock that sways, four corner floodlight masts with warm lamp heads (emission, no lights), and the existing antenna mast kept and trimmed. Umpire chair, net, posts and lines stay.

## B. VOLCANO

**V1. Fix the wallpaper and turn the wall into a terraced bowl.** *Steals: Bowser's Castle, where the lava lake is a lit stage and the walls are architecture.* The wall texture is stretched 3:1 because `v = r/90`; the new terrain uses arc-length UVs along the profile so rock is isotropic on steep faces. The profile becomes four stepped terraces (cliff risers 15-20 m, ledges, a toothed obsidian crest), with strata, a relief map, and glowing cracks that follow the surface. The 30 thin stripes and the yellow sulfur blobs are removed; 5-7 **lavafalls** (glowing animated ribbons, 4-10 m wide, spilling over the terrace lips and into the lake) replace them. The central +-15 degree of the wall behind the far baseline stays dark and low-detail (the lob band); the bright features sit to the sides and above it.
**V2. Near and mid layers: basalt islands in the lake.** *Steals: Mario Kart "near / mid / far" and Bowser's Castle lava pillars.* Clusters of hexagonal basalt columns stand in the lake 10-55 m from the deck sides and far end, tops from -6 m to +8 m, so there is something between the court and the wall and the camera gets parallax. They are glowing at the base (emission ramp) and lit on their inward faces by the existing slab-glow point light. None sits within 10 m of the deck edge.
**V3. The slab is lit by the lava.** *Steals: Bowser's Castle, lava is a light; it colours the deck edge and the near rock, it is not a flat orange texture far away.* The exposed deck margin becomes a molten channel (animated lava with dark crust and glowing cracks, bloomed by HDR emission) around the whole court; an additive orange gradient on the outer 2-3 m of the apron (clear of all lines) carries that light inward; the slab sides get a glowing melt-line; an obsidian **rock keel** (the existing unused `Underside`, rebuilt low-poly with glowing cracks) hangs below it. The four brazier corners stay.
**V4. A sky with shapes.** *Steals: Splatoon.* Baked dome: banded molten horizon, magenta smoke ceiling lit orange from below, near-black violet zenith, giant toon smoke billows with glowing undersides; the eruption plume is moved to a vent that can actually be seen from the drone and side views; embers kept. The lake gets a crust-plate texture (dark plates with glowing gaps, scrolling) instead of all-orange noise.
**V5. Lose the beach club.** Hide the same 18 resort props. Replace the lanterns with 8 obsidian pylons (glowing slit, emissive tip) in the margin; no plants, no sofas.
**V6. Stop paying for what no camera sees, spend it where it shows.** Remove the 420 trees (1,327,160 triangles), the grassland and the sea quad (never in any shipped view; the drone starts inside the crater and stays below the rim line). The 240 sphere-primitive boulders (184k) become about 150 low-poly ledge rocks (96 triangles each). Net result is a map that is roughly 6x cheaper while looking denser.

## C. What I will not touch

Resort map and its props (`resort_*` captures unchanged; no small fix proposed), `TennisVenue.cs`, deck size, `OverDeck`, drone end pose, gameplay and replay cameras, ball and contact code, `TennisGame.cs`, hero body / clothes / racket, ArtDir hero blends, the locker's court-colour override (still works: the court material is not changed), any new map.

## D. Gates and how each is proven

| gate | proof |
|---|---|
| AUDIT_WRITTEN | `work/venue-presence/AUDIT.md` |
| PLAN_WRITTEN | this file; every item above names its steal |
| COURT_UNCHANGED | `TennisVenue.cs` SHA equal to `before_code/`; kept-kit lines of the kit dump (court, lines, posts, net, apron, chair) identical before/after; `Drone(1)` logged equal; `play_files.sha256` re-verified |
| SKY_HEIGHT | `proof/sheet_skyscraper.png` edge + below + drone frames show the cloud sea under the edge; tower log shows 6 materials and 9 silhouettes among visible towers |
| VOLCANO_LIGHT | `proof/sheet_volcano.png` edge frame; pixel metric: warmth (R-B) on the slab margin and near-rock faces vs mid-deck, with the old frame as control |
| NO_RESORT_CLUTTER | dump shows 0 enabled renderers of TropicalV3_017/020/033 on both maps; frames show no sofas, plants, or garden lamps |
| PROOFS | before/after sheets for both maps, in `proof/` |
| PLAY_SAFE | `git diff` and `play_files.sha256` show no ball, contact, rules or camera files changed by this work |

Capture: existing `TennisVenueCapture` via `work/venue-presence/tools/capture.sh`, output `work/venue-presence/proof/after/`, views identical to the shipped set (gameplay, postcard, drone frames, side, below, edge). Old shots are the shipped `ArtDir/screenshots/venues/` files (verified equal to a fresh recapture, `proof/baseline/`).

---

# AS BUILT (written after the build; the plan above is left as written)

Every item above was built. Where the build differs from the plan, or a number moved after measuring, it is listed here. Code: `TennisVenueBuilder.cs` (shared helpers, kit list), `TennisVenueBuilder.Mesh.cs` (mesh accumulator, noise, ramps, textured sky dome), `TennisVenueBuilder.Skyscraper.cs`, `TennisVenueBuilder.Volcano.cs`, plus `Sway` / `FallFlow` in `TennisVenueFx.cs`. `TennisVenue.cs` is untouched.

## Sky
| item | as built |
|---|---|
| S1 cloud sea | A solid, lit heightfield 58 m under the deck (43,776 tris) with 229 cumulus lumps standing on it (37,760 tris) and collars where towers enter it. The four alpha sheets, 150 cumulus sprites, 20 horizon sprites and 380 city boxes are gone. Wisps are 18 low 3D puffs drifting between the deck and the sea (about 11.5k tris after I cut their subdivision to hit the budget). |
| S2 towers | 34 towers (plan said about 30), 6 facade families, 9 top silhouettes (ziggurat, crown, dome, slant-cut, needle, helipad, roof garden, flat plant room, round drum), a skybridge pair on the player-intro side and the **Saucer Tower** landmark. The landmark sits at x -135, z 312 (not -95): the first draft stood in the middle of the gameplay frame. Windows: fixed size in metres, per-tower UV offsets, one lit-window emission mask per family. |
| S3 sky | Baked 2048 x 256 dome (cached for the life of the app), sun with three rings as a crisp sprite, eight huge cloud ribbons with lit undersides, cirrus, a few stars. **The palette is deeper than planned**: the first draft (gold, coral, orchid) left the lob band at 1.44:1 ball contrast, the same as before. The final bands are a thin hot gold line at the horizon, then coral, magenta, plum, violet, indigo, and the cloud ramp is a notch darker and mauver. |
| S4 rooftop kit | Hidden: 8 lanterns, 6 sofas, 4 planters. Added in the stone margin only: water tank, two air handlers, three vent stacks, skylight, stair bulkhead, floodlight masts at the **far** end only (the near pair would stand inside the drone's landing view), a swaying windsock at x 11.5, z -3.5. Concrete is a cool mid-grey (pale boxes against the horizon are as bright as the ball). |

## Volcano
| item | as built |
|---|---|
| V1 bowl | Five stepped terraces (plan said four), lips that lean out over each riser, arc-length UVs (the 3:1 stretch is gone), a toothed crest with horns, eight lavafalls (plan said 5 to 7). The lob corridor (24 degrees either side of straight behind the far baseline) uses a submesh with a glow at 16% of the rest. |
| V2 basalt | 20 hexagonal-column clusters standing in the lake (a few were dropped by the camera and drone clearance tests in earlier drafts). Nearest column is about 14 m from the deck edge. Emission is a heat ramp, hottest at the lake. |
| V3 slab light | Molten channel round the margin (warped-Worley crust plates, scrolling), orange gradient on the apron's outer 2.2 m clear of every line, melt line on the slab sides, rock keel (the old unused `Underside`, rebuilt and **flush** with the slab: with a wider lip the drone's landing camera, 1.4 m outside the edge, saw its wall edge-on as black slivers). |
| V4 sky | Baked dome with a banded horizon and smoke billows lit from below. The plume stands on the crater rim 52 degrees off the lob corridor; steam vents are kept out of 54 to 126 degrees (a first draft put two smoke columns behind the baseline). Embers start orange, not yellow (a yellow spark is ball-coloured). Particle prewarm now works (the systems used to start before they were configured). |
| V5 resort props | Hidden (same 18 as the sky). Replaced by **six** obsidian pylons (plan said eight): the two nearest the camera corner were cut because they stood in the postcard and edge views. Cap glow is red-orange: tone-mapped yellow read as a second ball. |
| V6 budget | Trees, grassland, rocky ground and sea quad removed (no shipped camera sees them). 240 sphere boulders replaced by 150 ledge rocks of 80 triangles. |

## Changes outside the two builders
* `TennisVenueCapture.cs` (editor only): output folder via `HERO_VENUE_OUT` (so proof runs never overwrite `ArtDir/screenshots/venues`), `HERO_VENUE_DUMP` (kit and triangle report), `HERO_VENUE_HIDE` / `HERO_VENUE_ONLY` (debug), two extra review views (`7_rear`, `8_rivalintro`). The shipped six-view set is unchanged.
* `TennisVenueFx.cs`: two new components (`Sway`, `FallFlow`); the existing ones are unchanged.

## Known gaps (not claimed as done)
* No on-device (iPhone) run. All timings are Editor timings.
* The Low quality tier code paths (fewer lumps, wisps, steam vents) compile and are simple, but were not rendered.
* The sky's ball contrast ended at **1.97:1** median on the gameplay frame against the plan's 2.0:1 (1.79:1 on the postcard). The brightest remaining things in the band are the sunlit cloud tops at the horizon, which I kept on purpose: they are what sells the height.
* Resort untouched (no small fix was needed for any gate).
