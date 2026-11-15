# Hero references rendered in code — 2026-11-11

These seven sheets are real renders of the game's own heroes with every code-side improvement switched on. They replace the image-generation route: no outside service, our faces, bald under a cap. Everything ran in a throwaway copy of the project; nothing in `Unity/` changed.

| Sheet | Shows |
|---|---|
| `sheets/01_male_turnaround.jpg` | Male tennis hero: front, three-quarter, side, back |
| `sheets/02_female_turnaround.jpg` | Female tennis hero, same views |
| `sheets/03_faces.jpg` | Both faces: front, three-quarter, side |
| `sheets/04_details.jpg` | Shoes from three sides, tops front and back, shorts and skirt |
| `sheets/05_colourways.jpg` | Four colourways each, cap following the kit |
| `sheets/06_golf_bowling.jpg` | Golf and bowling kits for both |
| `sheets/07_in_game.jpg` | On court up close, as played, and in the menu |

## What is switched on

| Change | From |
|---|---|
| Calmer menu grade, hero lighting on with half fill | Look pass (earlier today) |
| Her arms shaped (shoulder, upper arm, tapering forearm) | Depth pass |
| Foot hidden under the shoe; toe narrowed and lowered; his shoe attached rigidly; toe bend capped | Depth pass |
| **Flat sole** in place of the rocker, and a **waist** under the arch | New |
| **Crest patch** on the left chest, drawn by the shirt shader from the garment's rest shape so it stays put through animation | New |
| **Accent colour as its own pick** (collar, cuffs, shoe panels, waistband, crest ring) | New, using a trim colour the materials already had |
| **Cap follows the kit** (base and brim) | New wiring of an existing unused hook |
| **Matte finish** as an option (black and gold colourway) | New |

All of it is behind environment switches (`HERO_DEPTH`, `HERO_CREST`, `VISUAL_HERO_LIGHTING`, `HERO_LOOK`) and saved in `tools/`: `all_changes.patch` (7 files), `HeroArmForm.cs`, `HeroCrest.cs`.

## What code alone could not reach

- **A true low sneaker.** The shoes now have a flat sole, a lower toe and a waist, but they are still the old chunky mesh reshaped. The collar and overall bulk need a remodel.
- **Her top as a collared polo.** She still wears the tank; code improved its finish only. Its ragged armholes and hem in motion are unchanged.
- **Expressions.** The faces have blink shapes only, so there is no smile or celebration to render.
- **Proportions.** Left as they are (about seven heads tall). The earlier 113 % head variant is not applied here.

## Not checked

- Motion with the flat sole (only the earlier shoe shape was filmed in a rally).
- Anything on a phone.
- The lobby (Swift) copies of the heroes.

## Reproduce

Clone `Unity/`, apply `tools/all_changes.patch`, copy the two `.cs` files into `Assets/Scripts/Tennis/`, then run the jobs in `jobs1.txt` and `jobs2.txt` with `run_stream.sh`. Colourways use `TURNAROUND_KIT=shirt,lower,shoes,trim,capBase,capTrim[,matte]`.
