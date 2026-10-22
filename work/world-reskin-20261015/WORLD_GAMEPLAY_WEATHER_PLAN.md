# Dream worlds, meaningful weather and risk/reward courses

Date: 2026-10-15. Status: PLAN ONLY. No implementation authorized by this request.

## Intent and scope

Carry the accepted dreamlike mood across **all 16 golf holes and all 3 tennis venues**. Make the world feel alive through landforms, atmosphere, materials, light, sound and consequential weather. Additional buildings are optional; each landmark must earn its place through composition, navigation or gameplay. Keep the joyful sports identity, beautiful foliage and readable play surfaces.

Golf receives authored shortcuts and randomized obstacle configurations. Tennis receives the visual world, clock and automatic venue-appropriate weather; tennis-specific gameplay effects require symmetric tuning and should not inherit golf penalties. Target 60 fps; stable 30 fps is an accepted fallback. Device tests were waived previously, so hardware performance remains unverified until measured. Do not request a phone connection as part of this planning task.

This supersedes the earlier one-map art pilot scope for future work. It does not authorize implementation now. Character/clothing changes are outside this plan.

## Research and design conclusions

1. **Mario Golf: Super Rush:** Nintendo documents biome-specific obstacles alongside blizzards that strengthen wind and reduce travel, and rain that affects travel and run. Weather should change club selection, aim and landing strategy as well as presentation. [Nintendo update notes](https://en-americas-support.nintendo.com/app/answers/detail/a_id/55654/)
2. **Fall Guys:** Epic's official course guidance starts with simple playable layouts, uses height and curved routes, and uses colors/patterns/icons to communicate danger. The game's designers also describe movable geometry changing available routes. Prototype hazards and shortcuts before expensive art; communicate their behavior through shape, motion and sound. [Epic design guidance](https://dev.epicgames.com/documentation/en-us/fortnite/working-with-fall-guys-islands-in-fortnite-creative), [Fall Guys designer interview](https://www.fallguys.com/news/moving-parts-the-brains-behind-the-blocks?lang=en-US)
3. **Left 4 Dead:** Valve's presentation describes selection among designer-placed possibilities and alternating peaks/rest periods. Borrow constrained variety and pacing; do not secretly punish successful golfers or give competing players different conditions. [Valve, The AI Systems of Left 4 Dead](https://steamcdn-a.akamaihd.net/apps/valve/2009/ai_systems_of_l4d_mike_booth.pdf)
4. **Horizon Zero Dawn:** Guerrilla describes an environment system integrating vegetation, sound, effects, wildlife and gameplay. Apply that coordinated approach to each biome rather than making the sky carry the whole transformation. This is an artistic lesson, not a proposal to copy Decima's renderer. [Guerrilla presentation](https://www.guerrilla-games.com/read/gpu-based-procedural-placement-in-horizon-zero-dawn)
5. **Mobile URP:** Unity recommends measuring rendering costs and managing shadow distance/resolution, cameras and rendering features. Budget dramatic effects around the actual camera and preserve gameplay visibility across quality tiers. [Unity URP performance guidance](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/configure-for-better-performance.html)

All numeric tuning below is a proposed starting point for this game, not a claim about those games or a verified performance result.

## What the repository already provides

| Area | Observed implementation | Planned treatment |
|---|---|---|
| Catalogue | `Course/Hole.cs`: Cliffside 7/8/9/12/15; Wild Isles 13/14/17/18/19/20; Magma 10/16/21/22/23. Tennis: Resort, Skyscraper, Volcano. | Track completion for every hole/venue, not just one example per course. |
| Weather selection | `Course/RoundEvents.cs`: seeded Clear/Gusty/Rain/Storm/Fog, biome snow/ash substitutions, changes between strokes. | Retain deterministic foundation; replace with per-hole condition schedules and composition limits. |
| Weather mechanics | Wet weather already multiplies fairway drag by 1.6, green drag by 1.3 and bounce by 0.7. | Verify these effects end-to-end; tune and communicate them rather than duplicate them. |
| Player switches | `SportsSession.swift` defaults `golfWeather` off; menus, map setup, lobby, bridge and network expose weather off flags. Weather and movers share one switch. | Remove all player controls and legacy overrides; separate internal weather/hazard systems. |
| Moving obstacles | `CourseMovers.cs` computes balloon/cart/gull/twister positions from time; launch phase is shared with shot simulation. | Extend this deterministic model for timed hazards. |
| Ball collision | `CourseShot.cs`, `Obstacles.cs` and ground rules handle custom golf simulation. | New hazards must work inside simulation, prediction, replay and networking; Unity trigger VFX alone are insufficient. |
| Fog | `WeatherView.cs` already drives depth/height fog; linear haze ends at 650 course yards in fog. Height fog uses a low base, exponential vertical falloff and a maximum opacity cap. | Diagnose actual depth/height/composition behavior across elevations; don't assume fog is entirely absent or that changing one color fixes it. |
| Minimap | Cached terrain rendering plus separate pin, landing, route, target and flight overlays in `Hud.cs`; phone and TV have different views. Fog copy explicitly says to trust the map. | Shared visibility mask must cover terrain AND overlays on every view. Update copy and aiming aids. |
| Lighting | Golf/tennis look scripts, atmosphere, weather and the fantasy pilot can all modify presentation. | One final environment compositor owns sky, light, fog, exposure and reflections. |

## 1. Art direction across the full catalogue

Use consistent surface quality and atmospheric depth while giving each biome its own identity. Avoid blanket purple tinting, detail-free trees, excessive bloom and black night scenes.

| World | Proposed transformation | Signature gameplay opportunities |
|---|---|---|
| Cliffside, 5 holes | Turquoise coves, sculpted white cliffs, flowering groves, suspended sea stacks, soft sea-cloud banks; amber edges at sunset, luminous blue water at night. | Floating rock openings, predictable coastal gust lanes, demanding island carries. |
| Wild Isles, 6 holes | Preserve its pine, crater, ice, mesa, jungle and tulip variety. Add layered giant silhouettes, aurora over ice, warm canyon light, luminous jungle plants and drifting pollen. | Ice runways, canyon wind lifts, root/rock apertures and timed natural barriers. |
| Magma Open, 5 holes | Basalt shelves, convincing molten channels, glowing fissures, ember-filled air and restrained heat shimmer; deep violet skies against orange lava. | Telegraphing lava vents, basalt gates, narrow cooled-crust shortcuts. |
| Tropical Resort tennis | Dreamlike coastal garden, layered palms and blossoms, lagoon reflections, warm court lighting after dusk. | Consistent match conditions; weather affects the surrounding world and carefully tuned ball behavior. |
| Sky Tower tennis | Courts above cloud layers, floating distant landforms, strong skyline depth and controlled luminous accents. | Exposed-wind identity, mirrored across court ends and locked during each rally. |
| Magma Crater tennis | Rich basalt and lava depth, rising ash, eruption silhouettes and clean illuminated court lines. | Spectacle outside the play envelope; out-of-bounds incineration respects the existing point result. |

Each hole needs a foreground/midground/background composition, material roughness hierarchy, contact shadows, coherent sky/reflection lighting, weather-responsive foliage and a matching sound bed. Keep the ball, legal landing surface, flag and hazards visually separable. Reuse modular art intelligently without repeating the same landmark on every hole.

## 2. Random obstacles with rules players can learn

Author safe placement sockets and legal motion envelopes for each hole. At hole load, a seeded selector chooses a validated combination of hazard type, location and timing. Never scatter arbitrary obstacles over a fairway.

Initial composition: one major decision hazard plus up to two supporting hazards on suitable holes; easier holes may use fewer. Keep tees, immediate swing space, cup approaches and at least one conservative route usable. Heavy fog, extreme wind and a lethal timing gate must not combine on a compulsory route. Reserve the most demanding combinations for optional shortcuts.

| Hazard | Player interaction | Warning and consequence |
|---|---|---|
| Floating rock gate | Time a low shot through an opening or loft around it. | Clear repeating motion; hard collision deflects the ball. |
| Lava vent / eruption arc | Cross during its cooling interval or take a longer route. | Ground glow, bubbling and rumble before a clearly bounded active plume. Contact destroys the ball. |
| Wind lift | Shape a shot through a visible current for extra carry. | Particles/foliage show direction; leaving the current badly can overshoot the safe landing area. |
| Ice runway | Land at a precise angle to gain substantial roll. | Recognizable icy material and runoff edges; excessive speed sends the ball into a hazard. |
| Moving basalt barrier | Choose a timing window or a higher trajectory. | Predictable silhouette and cycle; no spontaneous collision volume. |

Start lava timing with approximately 2–3 seconds of warning, 1–2 seconds active, then a visible cooling interval; tune for actual swing lead time and ball flight. The upcoming window must be legible before committing. No hazard spawns or retargets in response to a ball already in flight.

Incineration is a complete gameplay event: authoritative impact time/location, short breakup/ember effect, one clearly explained penalty, safe drop at a validated recovery point, next stroke ready promptly. Proposed rule: the shot counts plus one penalty stroke; never charge twice if water/out-of-bounds logic also runs. Do not burn a stationary ball while its player is waiting their turn. Validate respawn positions against the entire hazard cycle.

Floating **solid obstructions** come first. Landable floating platforms are a later extension: they require support IDs, elevated/moving ground, ball-at-rest behavior, camera handling, aiming and drop rules. The existing ground sampler cannot be assumed to support multiple surfaces at the same X/Z. Do not ship a visual island the ball falls through.

## 3. Shortcuts with a measurable reward

Author at least one optional demanding route per golf hole where geometry permits; redesign a hole deliberately if needed rather than forcing a fake shortcut. Preserve an understandable conservative route.

Examples:

- Cliffside: thread a suspended rock opening to reach a shelf that skips a layup. A miss hits rock or water.
- Magma: cross a vent lane during its quiet interval and reach the green in one fewer approach. A miss burns the ball and costs the penalty/drop.
- Fjord: use a narrow ice strip to carry a long roll onto a protected approach. Wrong angle or speed slides into danger.
- Jungle/mesa: a low aperture or controlled wind-assisted carry bypasses a dogleg, with a smaller landing margin.

On longer holes, aim initially for a successful shortcut to save about one stroke. On par-3s, reward a substantially better birdie position rather than inventing a meaningless distance saving. Measure expected strokes including miss penalties across novice/intermediate/expert shot distributions. The expert route should reward mastery while the conservative route remains rational. Geometry, camera, aim assist and predicted landing zones must agree about the route. Update route previews and CPU planning where present.

## 4. Automatic, consequential weather

Draw a fresh seeded weather profile for every new golf hole. Random can legitimately select clear weather. Initial weights: clear 25%, gusty 25%, rain/snow/ash 25%, fog 15%, severe storm 10%; adjust per biome and pacing. Avoid repeated severe events across a short round. Persist the draw for retries, reconnects and resume; a genuinely new round gets a new seed.

Give each hole a stable weather identity. Allow an authored intensity curve within it, with gameplay changes announced and applied between strokes. Lock the shot's physical weather state at launch; don't secretly change wind or friction after the player commits. In multiplayer, use equal condition epochs for the equivalent turn cycle; cosmetic clouds and rain can continue moving independently. This replaces the present possibility of weather changing just because a different player took a stroke.

| Condition | Gameplay | Presentation |
|---|---|---|
| Clear | Baseline surfaces and wind profile. | Rich sunlight/moonlight, cloud shadows where affordable, living foliage. |
| Gusty | Wind visibly changes the viable shot shape; calm intervals are readable. | Bent grass/trees, airborne petals, directional audio. |
| Rain | Reduced bounce/run and slower wet greens; any carry change must be separately tuned and reflected in prediction. | Slanted rainfall, splashes, darkened wet materials, restrained puddle reflections. |
| Storm | Stronger bounded wind and soaked ground; lower visibility. | Layered cloud cover, driven rain, distant lightning with delayed thunder; no random lightning ball kills. |
| Fog | Restricted sight and target information; conservative play becomes valuable. | Opaque banks with depth and height variation, muted distance, clear immediate play space. |
| Snow / ash | Biome-specific surface response and visibility, with appropriate wind. | Drifting snow or embers/ash, local accumulation, coherent sky and sound. |

Keep wetness visuals and physical surface state synchronized. Snow/ash need distinct tuning rather than treating every particle system as rain. Restrict changes to existing legal play surfaces until explicit tests cover new ones.

Remove weather switches from gameplay settings, course setup, multiplayer host controls, Swift actions, persisted preferences and Unity launch messages. Retire/ignore legacy `noWeather`/`weatherOff` inputs under the new versioned rules; don't hide a switch while leaving it functional. Old clients with incompatible rules must not silently join. Keep deterministic review/test controls compiled into development/test tooling only. Onboarding may use an authored gentle preset with no player toggle; normal rounds always use automatic selection. Refresh help text, condition labels and menu previews.

For tennis, sample conditions automatically at match start and vary only at agreed game boundaries. Court lights and local visibility must keep a rally playable. Introduce mild wind/surface effects symmetrically and test both ends; do not copy lethal golf hazards onto the court. Dramatic surrounding fog, rain and eruptions can be much stronger than the visibility reduction directly across the playing area.

## 5. Fog that actually hides the world and minimap

First reproduce clear/fog captures on low, elevated and flyover cameras. Inspect depth textures, shader ordering, transparent objects, pilot sky compatibility, fog base height and camera exposure. Existing height fog thins with altitude and is based on a few ground samples; these are investigation targets, not a proven single root cause.

Build around one world-space density/visibility description:

- Optical extinction increases with distance through fog, using depth and terrain-aware height plus broad drifting banks. Avoid a uniform gray layer. Retain local color and contrast near the golfer.
- Proposed dense-fog target: comfortable immediate view within roughly 10–15 course yards, strongly reduced contrast around 40–60 yards, distant targets obscured around 80–120 yards depending on density. Calibrate with real captures across elevations.
- Mobile implementation should first extend the existing analytic depth/height approach. Add a few bounded local bank volumes only where silhouettes need them; avoid a blanket expensive volumetric raymarch.
- Derive a low-resolution top-down visibility mask from the same density and the active player's allowed observation position. An overhead minimap camera must not see over the fog. Decorative bank motion may interpolate more often than the mask.
- Composite the mask over cached minimap terrain and apply the same visibility policy to pin, landing dot, target marks, route lines, reach arcs, trace and hazard icons. Apply it to phone, TV, simplified HUD and spectator views. Invalidate overlay caches when visibility changes even if the route version stays the same.
- Keep current ball, heading and local safe ground readable. Hide the precise distant pin/landing marker and predictive path beyond visibility; retain an approximate compass bearing and posted hole yardage for orientation. No through-fog glowing flag that restores exact targeting.
- Fogged areas remain obscured when the camera flies over them; moving a camera is not a reconnaissance exploit. Any remembered course outline is subdued and contains no live hazard/landing information.
- Use both density and player context, not simply a circular blur; lower graphics settings must not reveal more of the map or playfield.

## 6. Eastern-clock day/night across every map

Planning assumption: **literal EST = UTC−5 all year**. This means the stated times differ by one hour from New York's wall clock during daylight saving. If the intent is New York local time year-round, the future implementation should instead use `America/New_York`. The plan currently follows the explicit EST wording. [Official U.S. time distinguishes standard/daylight clocks](https://www.time.gov/)

| EST | Art direction |
|---|---|
| 05:00–07:00 | Dawn: cool mist, warming horizon, gradual sun rise. |
| 07:00–16:30 | Day: readable natural light and vivid biome identity. |
| 16:30–18:00 | Late afternoon: warmer side light. |
| **18:00–19:30** | **Sunset begins at 18:00**: amber/rose sky, elongated shadows. |
| 19:30–21:00 | Blue hour: indigo sky, moon/stars emerging, practical lights increasing. |
| **21:00–05:00** | **Full night from 21:00**: moonlit surfaces, warm light pools, luminous biome accents. |

This is an art-directed daily schedule, not seasonal astronomical sunset. Blend continuously; no abrupt switch at a time boundary. Use one authoritative UTC anchor converted to EST; multiplayer shares host/session time and advances it with a monotonic clock. Reconcile clock corrections at safe boundaries. Offline play uses device UTC; acknowledge it cannot be tamper-proof without a trusted service. Replays store the original environment time and progression instead of sampling today's clock.

Sun/moon, ambient fill, sky, reflections, fog scattering, practical lights and exposure must agree. Weather modulates that baseline instead of competing scripts overwriting it. Use a bounded exposure range so auto-exposure doesn't turn night into daytime or make lightning crush the scene afterward. Illuminate sporting surfaces deliberately; preserve darker surrounding depth. Court floodlights, glowing lava and bioluminescent foliage should provide motivated accents. No player-facing time/weather controls.

## 7. Architecture and performance constraints

Proposed data flow: versioned round seed + hole/venue ID + condition epoch + authoritative clock → environment state → simulation rules, visibility and presentation. Split hazard, weather and decorative randomness into independent streams so adding foliage cannot alter gameplay draws. Save/replay the chosen profiles, hazard IDs, phases and state version. Rejoin restores the same outcome.

Keep deterministic hazard positions and collision in the custom shot model; use swept collision/substeps for high-speed balls and thin/moving hazards. VFX consumes the resolved event. Add a distinct burn outcome to shot scoring and recovery. Maintain an explicit conversion between golf's course yards and tennis/metre-based scene data.

Centralize render ownership to avoid `WeatherView`, `GolfAtmosphere`, `HoleAtmosphere`, `TennisLook` and the pilot restoring stale lighting over each other. Fully restore shared state on hole/sport/menu transitions. Generalize the approved pilot through biome profiles, not a global switch that pastes its large structure set everywhere.

Performance budget: 16.67 ms/frame for 60 fps, 33.33 ms/frame for 30 fps. Measure main/render thread and GPU separately; these are frame budgets, not promised results. Retain automatic frame pacing/quality fallback. Reduce distant mesh/shadow cost, resolution, particle density and decorative layers before degrading readable foliage or hiding gameplay hazards. Never change collision, hazard timing, visibility reach or weather mechanics by quality tier.

Prefer instancing, shared materials, authored LODs with silhouette checks, simple shadow proxies, one principal shadow-casting light, precomputed/blended environment lighting and capped shadowless accents. Pool particles and hazard effects; avoid per-frame allocations. Keep terrain minimap cached and update a small fog mask rather than re-rendering the full course each frame. Audit overlapping transparencies and full-screen passes. The current golf pilot already measured roughly 4.7 million submitted triangles including passes in one view; treat it as something to optimize, not a template to multiply unchanged across all maps.

## 8. Delivery sequence after authorization

1. **Baseline and specification:** catalogue all holes/venues, capture fixed views, record visual and runtime baselines, finalize condition/penalty schemas and authored route envelopes. Preserve current art proof.
2. **Shared conditions and clock:** remove public switches, migrate preferences/protocol, integrate clock and one environment compositor. Test seeds, joins, retries, transitions and clock boundaries before heavy VFX.
3. **Fog and meaningful weather:** fix physical/visual synchronization and minimap/overlay visibility together. Prove dense fog, rain and night on existing geometry.
4. **Playable hazard slice:** use one Magma hole for a real timed eruption and shortcut; use the existing Cliffside pilot for floating obstacles. Prototype geometry first. Validate collision, scoring, timing, safe routes and expected reward before polishing assets.
5. **Tennis slice:** one court through daytime, sunset, storm and night, with symmetric condition changes and preserved court readability. Validate game rules and lighting handoff.
6. **Full art/gameplay rollout:** finish Cliffside's five holes, Wild Isles' six, Magma's five and all three courts. Give each its own composition and obstacle/shortcut design. Add landable floating geometry only after its support model passes.
7. **Balance and performance:** sweep allowed combinations, tune difficulty/pacing, optimize worst-case night-storm/fog views, refresh native map art/help and package proof. Do not call the rollout complete while unconverted holes remain.

No calendar commitment before the initial condition/geometry audit; moving landable platforms and universal multilayer lighting are larger tasks than additional dressing.

## 9. Binary acceptance gates and proof

- **GATE: COVERAGE PASS** only with a completed 16-hole/3-venue checklist, actual game captures and no unintended old-pilot-only activation.
- **GATE: VISUAL PASS** only with matching before/after camera pairs covering tee/gameplay, approach/green and wide view; each biome also shows clear day, sunset, night, fog and severe weather. Include live minimap/HUD captures. No generated concept image presented as game proof.
- **GATE: WEATHER PASS** only when measured repeat shots show intended wind/roll/bounce effects, HUD and prediction agree, no public weather switch works, and retries retain conditions.
- **GATE: FOG PASS** only when distance test targets lose visibility as specified, near play remains readable, all map/overlay paths respect occlusion, and changing quality/camera does not reveal hidden information.
- **GATE: HAZARDS PASS** only when warning → active → recovery behavior matches visuals, no tunneling/duplicate penalties occurs, recovery is safe, and deterministic replay/rejoin agrees.
- **GATE: FAIRNESS PASS** only after at least 1,000 seeded configurations per hole pass placement/safe-route invariants, plus sampled shot simulations and human playtests confirm conservative routes and useful expert shortcuts. Automated placement tests alone do not prove fun or playability.
- **GATE: CLOCK PASS** tests 17:59→18:00, 20:59→21:00, midnight, dawn, app resume, device time-zone changes, clock corrections and multiplayer agreement. Literal EST must remain UTC−5 through daylight-saving dates.
- **GATE: TENNIS PASS** only when both court ends retain ball/line visibility, identical condition rules apply, rally state does not change mid-point, and existing scoring remains correct.
- **GATE: PERFORMANCE PASS** requires sustained on-device data: proposed target p95 frame time ≤16.67 ms at 60, or ≤33.33 ms at the accepted 30 fallback, with hitches/p99 reported separately during a 15-minute thermal run. Until device testing is available, mark this **UNVERIFIED**, with editor counters and build checks reported separately; do not claim phone fps from screenshots.
- **GATE: REGRESSION PASS** covers single-player, multiplayer, reconnect, phone/TV views, changing sports, tutorial, scoring, drops, saves and supported quality levels. Attach `GATE_RESULTS.md`, raw measurements and proof paths at implementation time.

Planning deliverable only. No new art, physics, weather, settings, time-of-day or networking changes have been made by this plan.
