# Map intro UI — three exploratory directions

Requested: redesign the map-entry name bubbles and related intro overlays. These are generated visual mockups for review, not Unity screenshots or an implementation.

## Directions

1. **Club Bubble** — warm white welcome bubble, flat navy type, lime location tab, small speech tail. Closest to the current friendly party-sports tone.
2. **Court Ticket** — compact notched club pass, stronger type, slight tilt and one accent tab. Gives each map arrival a collectible feel.
3. **Open Air** — large white type directly over the scenery, small location chip and a localized contrast scrim. Gives the map the most room.

Each board shows a tropical map reveal and a matching family for a golf landmark, player introduction and rooftop/volcano map names. The bottom strip is a design presentation area, outside the game viewport.

## Suggested motion for a prototype

| Element | Club Bubble | Court Ticket | Open Air |
| --- | --- | --- | --- |
| Arrival | 240 ms soft pop, 104% peak scale | 280 ms slide with a small rotation settle | 240 ms fade and 12 px rise |
| Location label | Follow title by 70 ms | Appear with the ticket | Follow title by 60 ms |
| Landmark bubble | 180 ms pop from its anchor | 180 ms slide from the pin | 160 ms fade with a short stem reveal |
| Exit | 180 ms fade and small drop | 200 ms slide down | 180 ms fade |

These timings are proposals; the static boards do not demonstrate animation. Keep existing intro sequencing and skip behavior when prototyping. Keep map geometry, camera, lighting, character assets and gameplay unchanged. Keep overlays within the actual landscape safe area; the boards target a 16:9 reference viewport and do not verify every device aspect.

## Sources and generation

- Current system: `Unity/Assets/Scripts/UI/IntroGraphics.cs`, `Unity/Assets/Scripts/Tennis/TennisPresentation.cs`, `Unity/Assets/Scripts/Game/HoleIntro.cs`.
- Reference captures: `GolfArcade/Unity/MenuArt/map-resort.jpg`, `map-skyscraper.jpg`, `map-volcano.jpg`.
- Existing intro proof: `proof/intro-flyover/sheets/E_tennis_full_pick_spike.jpg`.
- Generated with built-in imagegen. Exact prompts: [PROMPTS.md](PROMPTS.md).
- Visual mockup proof and gates: [GATE_RESULTS.md](GATE_RESULTS.md).
