# Character depth audit — arms, shoes, female clothes (2026-11-11)

All three complaints trace to specific causes in the build, and two of them now have working fixes. The fixes ran in a throwaway copy of the project; nothing in `Unity/` changed. The code is saved in `tools/` (`clone_changes.patch`, `HeroArmForm.cs`).

Evidence comes from close-up films of both heroes in an autoplayed tennis rally (four cameras that follow the player) and from studio turnarounds.

## 1. The woman's arms

![arms](evidence/01_female_arms.jpg)

**What is wrong**
- **Her arms are straight tubes.** They are about 8 cm across from shoulder to wrist with no deltoid, elbow or forearm shape. An earlier note in `work/female-arms-form2` describes exactly this and built a fix on 10-01, but it was never installed, and the mesh has since been rebuilt.
- **She plays the man's arm carriage.** Her clips were re-exported per sex but keep his elbow-out posture. On his thick arms it reads as athletic; on thin tubes with narrow shoulders it reads as an insect.
- **Her shoulder joint has less support than his.** The runtime volume-preserving bones cover only elbow and wrist on her (28 support bones against his 91), because her mesh takes a different weighting path (`HeroArmSkinning.cs:34-43`).
- **Neither rig has twist bones,** so forearm roll piles up at the wrist.

**What I ruled out:** the clearance solver's elbow swivel. Cutting it from 55° to 15° changed nothing visible in the rally, because walking and running use pre-baked correction tracks.

**What I fixed in the copy**
- A shape pass on her arms in the rest pose: a deltoid and biceps swell, a slight narrowing above the elbow, and a forearm that is full near the elbow and tapers to the wrist. Up to 18 mm of movement, fading out at the shoulder seam and the hand so neither moves.

**What is left**
- Elbow carriage in her locomotion clips: bring the upper arms in by roughly 10–15° in Blender. About a day for the walk and run set.
- Shoulder support on her mesh, and a forearm twist share. About a day, with a re-check of the tank-top armhole.

## 2. Shoes on both

![shoes in motion](evidence/02_shoes.jpg)
![studio](evidence/03_studio.jpg)

**Why the feet read as inverted**
- **The toe box is as tall and as wide as the heel.** The man's shoe is 39.5 cm long and 19.7 cm wide (width/length 0.49, against about 0.38 for the target sneaker), with no waist and a blunt 14 cm tip. From the front, the toe end looks like a heel.
- **The shoe was built as a box around a cartoon foot.** The hide lists leave the forefoot visible inside the shoe, so the shoe had to be wide enough to enclose it. The male notes record this as a failed silhouette gate (13–29 % against a 5 % target).
- **The man's heel is skinned 45 % to the shin.** When the ankle bends, the back of the shoe goes with the leg and the front with the foot, so the shoe shears.
- **The toe bend has no limit,** so the game can fold the front third of the shoe upward when a toe dips below the court.
- **Left and right are not swapped.** Transforms, winding and bones all check out.

**What I fixed in the copy**
- The whole foot is now hidden under a worn shoe, which removes the reason for the box.
- A sneaker-shaped reshape: the toe narrows in plan with its tip toward the big toe, and the upper drops toward the tip over a sole that keeps its thickness and trim.
- The man's shoe is re-skinned rigidly: heel and sole on the foot, collar following the sock.
- Toe bend is capped at 15°.

**Where that leaves it:** less hoof, cleaner silhouette, no poke-through or tearing in the rally film. It is still a chunky shoe on a rocker sole. A proper low sneaker needs a remodel on a real last, which is now possible because the foot no longer has to fit inside. About a day per sex in Blender.

## 3. The woman's clothes against the man's

![cloth](evidence/04_cloth_male_vs_female.jpg)

- **His polo was rebuilt on 10-30; her tank was last rebuilt on 10-26 and only got the finish.** His has a collar, placket, cuffs and hem thickness, with fold shadows baked for it. Hers is a stretched tube with piping.
- **Her edges are ragged.** The armholes and hem show a frayed, jagged outline in every game frame.
- **Her finish is blotchy.** The gloss puts patchy reflections on a shape with no folds to justify them. I calmed it in the copy (less reflection, deeper fold shadow); that helps but does not add construction.
- **Her skirt shades badly from the front** (smeared dark streaks across the pleats), and her undershorts show below it with a noisy texture.
- **Her shoes carry about a sixth of the texture data of his** (250 KB mask against 1.6 MB).
- **Fix:** run her tank and skirt through the same rebuild his polo had: clean hems and armholes with thickness, a waistband, baked folds, matching finish. One to two days, mostly pipeline time. This I did not attempt in this pass.

## How this compares with top games

| Practice | Where it comes from | Our heroes |
|---|---|---|
| Silhouette first; detail that does not change the outline is baked down | Blizzard on Overwatch | Shoes fail on silhouette; tank edges are ragged |
| Twist joints attached to the main joint, weighted about 100 / 66 / 33 from wrist to elbow | Unreal's mannequin and MetaHuman rigs; common rigging practice | No twist joints; a blend at the wrist only |
| Body hidden under clothing so garments need not wrap it | Standard in modular character systems | Done for torso and legs; not for the forefoot until this pass |
| Characters designed to look natural in motion with few steps | Nintendo dropped robot designs for Switch Sports for this reason | Tube arms and box shoes look worst exactly when moving |
| LOD steps at about 50 % and 25 % | Epic's Fortnite LOD guidance | Present |
| 20–80k triangles for a console character | Third-party guides (no official Fortnite figure found) | 206–228k at full detail |

Sources:
- [Epic: Fortnite-ready asset best practices](https://dev.epicgames.com/documentation/fortnite/fortniteready-assets-best-practices-in-fortnite)
- [Epic: LOD best practices in Fortnite](https://dev.epicgames.com/documentation/fortnite/level-of-detail-lod-best-practices-in-fortnite?lang=ja)
- [Unreal forum: forearm twist in Modular Rig](https://forums.unrealengine.com/t/modular-rig-forearm-twist/1997065)
- [Polycount: twist bone weighting](https://polycount.com/discussion/comment/2681188)
- [PC Gamer: how Torbjörn set Overwatch's art style](https://pcgamer.com/how-torbjrn-became-the-art-inspiration-for-all-of-overwatch)
- [Kotaku: Overwatch art GDC talk](https://kotaku.com/without-torbjorn-overwatch-wouldnt-be-overwatch-1792919785)
- [Blizzard: working on Overwatch as a concept artist](https://overwatch.blizzard.com/en-gb/news/23537427)
- [Nintendo Life: Switch Sports character concepts](https://www.nintendolife.com/news/2022/05/nintendo-reveals-character-concepts-for-switch-sports-included-robot-designs)
- [Nintendo: Ask the Developer, Switch Sports](https://www.nintendo.com/sg/interview/as8s/03.html)
- [Simplygon: character optimisation](https://simplygon.com/posts/0179d2c5-a440-49d7-850a-0a9a94152d1b)

## What I would do next, in order

1. **Install this pass with the look baseline from the previous round** (menu grade, hero lighting). Needs the lobby copies re-synced and a phone check. Half a day.
2. **Rebuild her tank and skirt** to his polo's standard.
3. **Remodel both shoes** on a real last.
4. **Her elbow carriage** in walk and run, plus shoulder support and forearm twist.
5. **Weight:** cut both heroes to about 60k triangles.

## Not checked
- Golf and bowling kits (same shoes and arms, but different garments).
- The lobby (Swift) copies of the heroes, which need the same changes exported.
- Anything on a phone.
- The arm pass against the baked hand-clearance tracks: her arms are up to 18 mm fuller, so a forearm may now brush the tank where it used to clear.

## Files
- `evidence/` — the four boards.
- `shots/film_female`, `shots/film_male` — before films; `shots/film_female4`, `shots/film_male4` — after; `shots/turn_after` — studio after.
- `tools/HeroMotionFilm.cs` — the four-camera rally film; `tools/HeroArmForm.cs` and `tools/clone_changes.patch` — the fixes, all behind `HERO_DEPTH=1`.
