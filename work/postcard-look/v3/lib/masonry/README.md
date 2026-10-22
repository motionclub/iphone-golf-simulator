# Phase 1 masonry

Only hole09_masonry.py and hole09_stone.py changed. Wall support skyline, top bearing chip cap, arch seating, lintel bearing and all validator thresholds remain unchanged. Cut corners now visibly trim the plan silhouette more, quarry folds remove a deeper side portion, exposed stone tops break more strongly, and a subset of the existing Rock_C windows permits natural moss. A deterministic corner-cut fallback prevents intact cuboids when stochastic cuts miss.

Before fixture: 269 pieces, 0 unbroken cuboids. After fixture: 286 pieces, 0 unbroken cuboids. Both PASS the <=20% piece threshold, including rotated intact boxes. This was a visual improvement; the previous piece metric already passed.

After unchanged ruin_check: 13/13 PASS. Floating stones 0; lintel supports 9/9 at each end; doorway 56/56 open through-rays; buried bases 87%; stone length CV 0.31/0.30; exposed tops 91% tilted; arch 145/181 covered angles, largest gap 0.45m; planar faces worst0.002mm; mismatching coplanar UV pairs0. Look/props shared smokes are coordinated with the library agent after this batch.

The neutral Blender views inspect geometry only. The parent will render the staged hole through Unity during the ordered phases. Saved after views: fixture.png, arch_front.png, doorway_front.png, top_oblique.png and fixture.blend in after/. The fixture uses no scoring design changes and writes solely in v3/lib/masonry.

Scratch harness repairs: initial render had no installed EEVEE_NEXT enum, and the next had no world after P.start purged it. The harness now uses installed BLENDER_EEVEE and explicitly creates a world. Neither failed run is render evidence.
