# Custom map UI — complete review set

Latest user requirements: preserve each map's bespoke sculpted identity, remove sport-category labels, use usernames without YOU or role tabs, extend the direction to map arrivals, HUDs, phone controllers and surrounding flows. Power meter refinement: small exact percentage and four notches at 25%, 50%, 75% and 100%.

Open [the review gallery](gallery.html) to filter and enlarge the 15 boards.

## Ten map systems

- [TROPICAL RESORT](proof/01-tropical-resort.png) — arrival, live-play HUD, portrait phone controller, nameplate and event/state examples.
- [SKY TOWER](proof/02-sky-tower.png) — arrival, live-play HUD, portrait phone controller, nameplate and event/state examples.
- [MAGMA CRATER](proof/03-magma-crater.png) — arrival, live-play HUD, portrait phone controller, nameplate and event/state examples.
- [CLIFFSIDE](proof/04-cliffside.png) — arrival, live-play HUD, portrait phone controller, nameplate and event/state examples.
- [WILD ISLES](proof/05-wild-isles.png) — arrival, live-play HUD, portrait phone controller, nameplate and event/state examples.
- [MAGMA OPEN](proof/06-magma-open.png) — arrival, live-play HUD, portrait phone controller, nameplate and event/state examples.
- [CLUB LANES](proof/07-club-lanes.png) — arrival, live-play HUD, portrait phone controller, nameplate and event/state examples.
- [NEON NIGHTS](proof/08-neon-nights.png) — arrival, live-play HUD, portrait phone controller, nameplate and event/state examples.
- [TIKI SHORES](proof/09-tiki-shores.png) — arrival, live-play HUD, portrait phone controller, nameplate and event/state examples.
- [MAGMA LANES](proof/10-magma-lanes.png) — arrival, live-play HUD, portrait phone controller, nameplate and event/state examples.

## Shared screens and power detail

- [Map selection and loading](proof/11-map-selection-loading.png)
- [Player introductions and events](proof/12-player-intros-events.png)
- [Setup, ready and pause](proof/13-setup-ready-pause.png)
- [Results and round-end states](proof/14-results-round-end.png)
- [Precise power meter](proof/15-precise-power-meter.png)

The active HUD uses thinner material accents than the large arrival sculptures. Character labels show only usernames. Map names stand alone; sport labels and session/category ribbons were removed. Controller functions were checked against current SwiftUI source: serve aim/baseline movement/Toss and motion/radar during rallies; club/aim/arm-to-swing controls for courses; stance position and hold/release ball control for lanes. This is a conceptual visual treatment, not a claim that interactions were implemented or tested. Existing sample numeric values are illustrative.

The power-meter board and three course mockups use a compact live percentage, four quarter-scale notches and an endpoint aligned to the shown power. A separate adjustable component preview demonstrates a shared value driving fill, marker and number; its source is in the chat's durable visualization directory. The earlier unchanged-meter instruction was superseded by the user's explicit request to redesign it. The initial large-percentage/dense-ruler concept was superseded by the small-percentage/four-notch revision.

## Scope and evidence

Generated with built-in imagegen. These are static conceptual composites, not Unity runtime captures. Backdrops and generated figures provide context and are not proof of pixel fidelity to runtime assets. No game code, scene, character, camera, light, animation or production UI asset was changed. No commit. Actual implementation, localization, contrast over motion, device safe areas and tap-target validation remain future work.

Source context: `Unity/Assets/Scripts/UI/IntroGraphics.cs`, `Tennis/TennisHud.cs`, `UI/Hud.cs`, `Bowling/BowlingHud.cs`; `GolfArcade/Unity/TennisPlayViews.swift`, `GolfController.swift`, `BowlingController.swift`. The current controller removed Dive on 2026-11-13, so no Dive action was added. A category-based copy rule from older archive plans is superseded by this chat.

Exact original prompts: [PROMPTS.md](PROMPTS.md). Corrective/revision prompts: [REVISIONS.md](REVISIONS.md). Review gates: [GATE_RESULTS.md](GATE_RESULTS.md).

