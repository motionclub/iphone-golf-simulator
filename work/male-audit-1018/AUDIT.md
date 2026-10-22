# Male hero audit — current game vs male reference pack (2026-10-18 night)

**State captured:** today's integrated tree (`Unity/` after the 10-18 22:17 install = face/shader chat 11, garments round 9, caps re-hug).
APFS clone `~/integration-work/audit-male` (Unity3 + `rsync` of the real `Unity/Assets`), one Unity batch run through `heavy.sh`:
`tools/run.sh <tag>` → `unity/MaleAuditRun.cs` = HeroTurnaround (all four heroes, game shaders, `TURNAROUND_LOOK=target`) + MaleFaceReview
(views / dressed / body) + FemaleFaceReview (views). Raw renders: `unity_out/now/`. Nothing in `Unity/` was edited.

**References:** `ArtDir/style/alive/male-reference-pack-2026-10-17` — 01 tennis master, 03 golf master, 09 polo, 15 body, 17 face detail.
Clothing hues in the harness are its own picks (cream polo, cobalt golf polo, darker skin `B7744A` in the turnaround); colours are
customizable, so hue differences are **not** counted below. The face review uses Tan `E2A06E` like chat 11's sign-off.

## Proof sheets (`proof/`)
| file | what |
|---|---|
| `A_tennis_vs01.jpg` | sheet 01 front/side/back vs game rest pose |
| `E_golf_vs03.jpg` | sheet 03 front/side/back vs game rest pose |
| `C1_male_face_front_tq.jpg` | sheet 17 front + 3/4 vs game (bald, Tan) |
| `C_male_face_vs17.jpg` | + profile + lips close-up |
| `D_female_bar.jpg` | female game face next to male game face, same harness (the bar) |
| `B_closeups_male_vs_female.jpg` | turnaround close-ups: face, shirt, shoes, male vs female |
| `F_body_vs15.jpg` | uncovered body vs sheet 15 + locked plate |
| `G_neck_cap_detail.jpg` | neck band seam, cap fit at back/side |

## Verdict
The female reads well because everything on her face is **one consistent stylization** (big cartoon eyes with a dark lash frame,
painted lip volume, blush, soft form) — her shader paints the form the flat game lighting cannot (`_HeroLightingEnabled` = 0 and fill .12
in game, logged by both reviews). The male got **realistic proportions (small eyes, narrow skull) without the painted form**, so in the
same flat light his face is a smooth mask with features stuck on. The clothes are built to the sheets in construction, but at game
distance the **shoes and the boxy, fold-less polo** dominate the silhouette.

## FACE — where we are vs sheet 17 (priority order)
| # | Problem (seen in) | Ref | Likely cause / where | Fix direction |
|---|---|---|---|---|
| F1 | **Eyes look pasted on / staring**: bright white sclera shows on both sides of the iris, no lid thickness or lash line visible at game size (C1, D) | Upper lid + dark lash line frame the eye, iris fills most of the opening, little white | chat 11: iris 1.0, eye opening 33x12.5 mm, sclera .82-ish; lash/crease paint too weak in flat light | Copy the female method: dark upper-lash band + lid-thickness shading in `HeroFaceSkin`/`TennisCharacter` male branch, sclera albedo down + corner shading, iris ~1.10-1.15 or lid 1-2 mm lower (`MaleIris`, `MaleEyeTall` in `HeroFaceReferenceFit`) |
| F2 | **Brows float high** (gap ~2x eye height) and at 3/4 the **far brow sticks out past the temple silhouette** (C1 3/4) | Heavy brows sitting low and close to the eye, wrapped on the brow ridge | Brow strip vs the narrowed skull (`MaleSkull` -.02 / orbit terms); brow verts never lowered for the male (female has its own brow line at L82) | Lower male brows ~4-6 mm, pull the outer tips onto the forehead surface; gate: brow inside the head silhouette in 3/4 and profile |
| F3 | **Nose vanishes from the front**: no nostrils, no alar crease, no shadow under the tip (C1) | Broad tip, visible nostril wings + dark nostrils, shadow under the nose | Form exists in mesh (warp tip/alar) but no painted occlusion; flat light | Painted form pass (female approach): nostril darks, alar crease, sub-nasal shadow, slight tip highlight; maybe +2-3 mm alar width |
| F4 | **Lips = flat pink lozenge**, no bow, no shadow under the lower lip (C lips) | Defined cupid's bow, upper lip darker, lower lip highlight + shadow below | Lip paint present (chat 11) but no volume paint | Paint lip volume like the female (her lips were fixed by painting form, not bump) + under-lip shadow + mouth-corner darks |
| F5 | **Jaw kink** at the chin corner (front) and a **step line under the ear** (3/4); vertical crease on the side of the neck (C1, G) | Smooth rounded-square jaw, clean jaw→neck turn | sculpt s13 + 10-12 jaw sculpt leftovers ("corner under ear") | Smooth the jaw edge row + neck crease in Blender (60° split guard as chat 11) |
| F6 | **Stubble reads as grey dirt** — hazy, cool, no edge (C, D) | Fine warm brown-grey stubble with a clear cheek line and darker upper lip/chin | stubble colour/density in male shader branch | Warmer hue, finer grain, crisp upper boundary on the cheek, lower opacity on the jaw sides |
| F7 | **Rectangular darker band on the front of the neck** running into the chest, hard vertical edges (G body front/3/4) — shows at the open polo collar | Even neck tone | male face/neck zone mask in the skin shader has a box edge (chat 11 noted neck patch 12.3 dE) | Feather the zone (or remove the neck darkening); gate: no luminance step > 2 % across the neck |
| F8 | **Ears pale and flat** vs the face, no concha shading (C1) | Ears same warmth as the face, deep concha | ear zone not covered by the face tint/AO | Same tint as the cheek + concha/helix-rim occlusion paint |
| F9 | Overall no **form shading** (brow ridge, cheekbone, temple hollow, under-jaw) | strong soft form | game lighting is flat by design | Male "painted form" layer = the single biggest lever (it is what makes the female read) |

Not a problem: skull/ear size and head proportion now track sheet 07/17 (chat 11 numbers hold in these renders).

## CLOTHES — where we are vs sheets 01 / 03 / 09
| # | Problem (seen in) | Ref | Likely cause | Fix direction |
|---|---|---|---|---|
| C1 | **Shoes are moon boots** — tennis + golf read ~20 % of body height, bulbous toe, thick midsole (A, E, B) — the worst read at game distance | slim low sneaker, ~17 % | shoe4 `enclose`: 0.365/0.375 m long + 10 mm room around a 0.30 m cartoon foot (gate 3 FAIL: 13-29 % silhouette) | Stop enclosing the full cartoon foot: **collapse the hidden foot inside the shoe** (garment-only corrective that shrinks toe/instep verts to the shoe's inner last, like the cover already hides them) and rebuild shoe4 at ~0.30 m with a lower toe; compare female shoes (B) which read right |
| C2 | **Socks are thick tall tubes** (A) | snug crew sock | collar sized to the 13 cm ankle | slim sock ~15 % + shorter cuff after C1 |
| C3 | **Tennis polo is a stiff box**: no drape, no side/armpit folds, sleeves flare out straight, shoulders square, collar lies flat with thin tipping (A, B) | soft knit with side folds, sleeves following the arm, rolled collar with clear navy tip | K7_MT fit + correctives tuned for tears, no fold detail/AO in the maps | Fold normal + AO bake (side seams, armpit, sleeve hem roll), sleeve taper toward the arm, taller collar roll + wider tip band; keep the tear numbers ≤ today |
| C4 | **Golf polo flat and cropped at the belt** (E) | bloused over the belt, collar stand visible | tuck geometry pinned at the belt | 1-2 cm blouse above the belt + fold AO; bigger collar stand |
| C5 | **Cap sits high**: gap between cap band and scalp at the back, strap opening floats (G) | cap hugs the skull | cap re-hug (10-18) vs the narrower skull — lobby/game not verified together | re-check `--keep-fit` hug against today's head; gate: band-to-scalp gap ≤ 3 mm all round |
| C6 | Tennis shorts, golf trousers, belt | — | — | closest to the sheets; leave alone |

## Body (sheet 15)
Matches the locked plate as Adnan decided 10-17 (sheet 15 is bulkier) — no change. Only F7 (neck band) is a body-area defect.

## Suggested order
1. **Face painted-form pass** (F1, F3, F4, F6, F8, F9) — shader only, no mesh-count risk, biggest visible win; mirror to `MatchHeroSurfaces.swift` + lobby sync.
2. **Brow + jaw geometry** (F2, F5) and the neck band (F7).
3. **Shoes + socks** (C1, C2) via the hidden-foot collapse, so the shoe can shrink.
4. **Polo look** (C3, C4): folds/AO/collar, without reopening the tear work Adnan paused.
5. Cap fit (C5).

Each step: re-run `tools/run.sh <tag>` and rebuild the A/C1/E sheets for the same before/after comparison.
