# Putt meter on the minimap, 2026-10-19

Adnan: the putt meter should be on the minimap, zoomed in on the green, like the full shot's power marks on the map. The world-space ruler on the green (chat C's PuttDistanceMarks) is retired to work/hold-swing-putt/retired/.

GATE: MAP_ZOOMS_ON_PUTT PASS: with the putter lined up, the shot map frames the putt: the ball near the bottom, the hole up the map, out to the first meter mark past the hole (proof/maps_sheet.jpg, 27 ft and 12 ft putts).
GATE: MARKS_IN_FEET PASS: the 25/50/75/100 % marks sit on the aim line in the meter's colours and are labelled in feet on the right (5/19/42/75 ft dry). They are the same feet as the meter's stops.
GATE: LIVE_DOT PASS: as the putter comes back, a live dot slides up the line with its feet on the left (7 ft at 30 %, 23 ft at 55 %, 54 ft at 85 %). The map steps out a mark at a time, so the dot never leaves it.
GATE: FULL_SHOT_UNCHANGED PASS: the tee shot's map still frames the whole hole with its 25/50/75/100 % marks (proof/full_shot_unchanged.jpg).
GATE: SWIFT_COMPILES PASS (file only): GolfController.swift compiles clean. The full app build fails only on the checked-in GolfArcade.xcodeproj being stale (AwayPolicy missing, not this change).
GATE: PHONE_DEVICE FAIL (NOT RUN): the phone sheet map card (Unity, TV mode) and the SwiftUI controller map get the same marks but were not captured. Not tried on a real phone.

Film: tools/film.sh <label> (mirrors Unity/Assets into ~/unity-clones/hold-swing-putt, batch mode, muted, through heavy.sh).
