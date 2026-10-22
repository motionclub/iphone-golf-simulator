# Dream worlds implementation — 2026-10-15

The attached plan was explicitly authorized by “implement this plan fully.” Its planning-only footer is superseded by that request. Character meshes, clothing and character lighting profiles were not part of this implementation.

## Runtime architecture

- `DreamConditions` version 5 defines fixed UTC−5 time, seeded weather pacing and shared analytic fog visibility. The Swift daily forecast has a 16,000-draw golden parity fixture.
- `DreamEnvironment` owns final sky, direct/ambient environment light, fog, reflection and bounded exposure. Weather supplies state; existing venue builders supply the daytime baseline. Save/resume stores the anchor, elapsed time, seed, location, weather, hazard identifiers and version. Multiplayer uses the host anchor; replays use the original shot time.
- Automatic weather is enabled in normal rounds. Retired native settings, actions and bridge/network overrides cannot disable it. Incompatible pre-v5 network configurations are rejected. Test forcing is compiled into Editor/development paths.
- Golf weather is fixed per hole. Rain, snow and ash have distinct measured bounce/drag responses. Gust epochs are based on swings, so penalties do not secretly give competitors different wind.
- Tennis conditions commit at game boundaries. The shared solver and host simulation use identical symmetric drag/bounce changes. Crater ember effects occur only after an existing point result and beyond the deck.
- `DreamCourseLayout` supplies one authored optional decision feature per hole, two seeded lateral sockets and deterministic phases. Fog/storm replaces lava timing gates with basalt openings. Tees, cup approaches and the original conservative corridor remain protected. No floating decoration is landable.
- The custom shot simulator handles currents, moving rock collisions (including after an earlier rebound), ice and timed vent burns. Burns produce one existing penalty/drop outcome, a distinct event and safe recovery. Previews, replays and host paths use this simulation.
- `DreamVisibility` applies the same observer-relative policy to world fog, cached map terrain and every precise overlay. Moving a camera does not move the observer. Current-ball markers stay above the map veil; distant pin information becomes a coarse bearing.
- `DreamWorldArt` adds bounded modular landforms, local mineral accents, small luminous grove plants/pollen, tennis practical lights and biome-specific silhouettes. The existing hole 12 garden remains local to its original hole. Existing foliage, terrain collision and character assets are retained.

## Reproduction

Use Unity 6000.3.24f1. Editor entry points: `DreamWorldCapture.Run` (all 19 locations × five modes), `DreamRouteAudit.Run` (terrain/route audit), and `GolfCourseStandardCapture.Run` (matched baseline camera set). Capture controls are documented in their editor source. Normal builds expose no weather/time controls.

Final proof and gate status are recorded in `GATE_RESULTS.md`. Intermediate `rejected-art`, `night-fix`, `routes-initial` and calibration captures are investigation evidence, not final acceptance images. Use `proof/final-v3`, `proof/after`, the final XML files and `proof/balance.csv`.

## Interpretation limits

The paired route benchmark samples 48 matched execution errors per skill band and hole. Remaining strokes are an explicit distance/putting estimate, not human scoring data. Conservative shots are selected using the nominal outcome plus four expert error corners, constrained to the original corridor and avoiding the optional feature. A local heading/power search reduces fragile nominal-only selection; this still is not a complete shot planner. Calibration uses known entry shots and does not prove that players discover or enjoy them. Par-3 targets are offset from the cup to reward a close birdie position. Final expert samples on holes 12, 15, 18 and 21 produced zero shortcut hole-outs in 48 shots each, with mean remaining distances of 2.04, 2.00, 6.56 and 5.87 yards. The ice runway provides a smaller gain; all routes still require human balance checks. No hardware performance or thermal result is inferred from Editor counters. The native simulator build verifies the Swift shell, not a newly exported Unity iOS player.

## Catalogue

| Hole | Name | Optional feature |
|---|---|---|
| 7 | Cliffside | RockGate |
| 8 | Needle | RockGate |
| 9 | Split | WindLift |
| 12 | Island Carry | RockGate |
| 15 | The Steps | WindLift |
| 13 | The Spiral | RockGate |
| 14 | The Witch's Lair | RockGate |
| 17 | Frostbite Fjord | IceRunway |
| 18 | Mesa Canyon | WindLift |
| 19 | Temple Falls | RockGate |
| 20 | Windmill Links | WindLift |
| 10 | Crater | LavaVent |
| 16 | Volcano Rim | BasaltGate |
| 21 | Obsidian Slab | LavaVent |
| 22 | Ember Causeway | LavaVent |
| 23 | Caldera Crown | BasaltGate |

Tennis: Tropical Resort, Sky Tower and Magma Crater share the clock/weather system, with generous court visibility and mirrored physics.
