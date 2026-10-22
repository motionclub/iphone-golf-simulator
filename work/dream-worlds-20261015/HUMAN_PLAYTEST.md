# Remaining human acceptance — dream worlds

Hardware testing remains waived. Do not infer device frame rate from these captures. The following are experience checks; simulated players cannot supply them.

## Route balance

Use identical seeds and conditions for conservative and optional routes. Have novice, intermediate and expert players attempt both routes at least ten times per hole. Record actual strokes to finish, failed entries, penalties, deaths, recovery quality, whether the warning was understood, and whether they would voluntarily choose the shortcut again. Alternate route order to reduce learning bias.

Priority cases:

- Holes 12, 15, 18 and 21: final current targets are offset from the cup. The final expert samples show zero shortcut hole-outs in 48 attempts per hole and roughly 2–7 yards remaining. Confirm that these birdie opportunities reward the harder entry and do not replace ordinary shot selection.
- Hole 17: the ice runway has a modest simulated reward. Check whether its longer run is worth the narrower entry.
- Holes 8 and 23: check miss recovery and whether penalty frequency makes the optional route too punishing.
- Magma vents 10, 21 and 22: verify players understand cooling → warning → eruption, can wait safely, and see exactly one penalty after a burn. Severe fog/storm should replace the lethal gate.

The CSV uses distance-based remaining-stroke estimates and a fixed error model. It is not a human acceptance result. The plan proposes roughly one saved stroke on longer holes and a better birdie position on par-3s. Frequent automatic hole-outs would exceed that par-3 intent and should be tuned down if confirmed in play.

## Visibility and presentation

Review each five-mode contact sheet and the full-resolution captures. Play fog from tee, ridge and overhead cameras: current ball and local ground stay readable; distant pin, landing zone, terrain and route information stay obscured. Check phone, TV and spectator layouts. On each tennis venue, play from both ends in fog/storm/night and confirm line and ball readability.

## Session checks

Resume an offline round after a clock change: retain shot/hazard state, then reconcile time at the next safe hole/game boundary. Rejoin a v5 host and verify identical weather, hazard phase and resolved shot outcome. A pre-v5 client must be refused. Switch golf → tennis → menu and verify no stale sky, fog mask, wetness or extra compositor survives.

## Future performance acceptance

When hardware testing is scheduled independently, collect separate main/render/GPU timings during a 15-minute thermal run, including night-storm and fog. Report p95/p99 and hitches at 60 fps or the accepted 30 fps fallback. Until then PERFORMANCE is UNVERIFIED; this task does not request a phone connection.
