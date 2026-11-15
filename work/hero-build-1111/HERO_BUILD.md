# Hero build and presence — installed 2026-11-11

The men are more muscular and fill their shirts, the woman's arms have real shape and a working forearm twist, and both heroes read better in every scene. The changes are installed in `Unity/` (8 files modified, 3 added, nothing committed). They were verified in a copy of the project that is byte-identical for these files; the game project itself has not been opened in Unity since the install, and nothing has run on a phone.

![men](evidence/01_men_build.jpg)
![her arms](evidence/02_her_arms.jpg)
![presence](evidence/03_presence.jpg)

## What changed

### The men's build
- One smooth shape field in the rest pose gives them larger shoulders, biceps and forearms, pecs, a wider upper back and traps, a waist that draws in, a fuller neck and bigger calves.
- The same field is applied to every garment over the body, so the polo, golf shirt, bowling shirt, shorts and trousers follow the build. Nothing pokes through in the studio or rally renders.
- It applies to the tennis, golf and bowling kits, and to the distance versions of the garments.

### Her arms
- **Shape:** a shoulder cap, a fuller upper arm, and a forearm that tapers to the wrist, in place of the straight tubes.
- **Forearm twist:** three helper bones per forearm share the hand's roll along the limb, so the wrist no longer wrings. The men get this too.
- **Shading:** the flat patches on her shoulder caps and arms are smoothed.

### Presence in game
- **Hero lighting is on.** The existing system that caps coloured venue light and adds a fill and rim was switched off; it is now the default, with the fill halved so limbs keep their shading.
- **Cloth keeps its shape in strong light.** Saturated shirts no longer clip to one flat colour. Picks stay fully customisable.
- **Firmer ground shadow** under both players in tennis.
- **Menu:** the plaza's golden-hour grade no longer turns skin yellow, and the hero's head turns toward the viewer.
- **Shoes** (from the earlier pass): foot hidden under the shoe, narrower and lower toe, flat sole, rigid attachment, toe bend capped.

## Switches

Everything is on by default. Each can be turned off with an environment variable in the Editor.

| Variable | Turns off |
|---|---|
| `HERO_BUILD=0` | Men's build, her arm shape, forearm twist |
| `HERO_TWIST=0` | Forearm twist only |
| `HERO_ARM_NORMALS=0` | Her shoulder and arm shading fix |
| `HERO_DEPTH=0` | Shoe reshape, foot hiding, toe clamp |
| `HERO_PRESENCE=0` | Hero lighting default, cloth settings, firmer shadow, menu head turn |
| `HERO_LOOK=0` | Calmer menu grade |
| `MENU_GAZE=0` | Menu head turn only |

`HERO_MUSCLE` scales the men's build (default 1.2) and `HERO_ARM_GAIN` her arms (default 2).

## Still open

- **Her elbows still flare** in the run and recover clips. That is in the animation, not the mesh.
- **A hard edge remains** on the back of her shoulder where arm meets shoulder blade.
- **Her tank top** still has ragged armholes and hem; that needs the garment rebuild.
- **Shoes** are improved, not remodelled.
- **The phone locker** (the Swift copy of the heroes) still shows the old build until the heroes are re-exported and synced.
- **Hand-clearance tracks** were baked for the old, slimmer bodies. Arms may now brush the chest or tank in poses that used to clear; I did not see it in the rally films.
- **Automated tests** (PlayMode suites, the visual goldens) were not run.
- **Bone count** rose by six per hero for the twist helpers.

## Files

- Installed: `tools/installed_changes.patch` (the eight modified files), plus `HeroBuild.cs`, `HeroForearmTwist.cs`, `MenuHeroGaze.cs`.
- `install.sh` — what was run. `ROLLBACK.sh` — restores the eight files from `install_backup/` and moves the three new ones out of the project.
- `evidence/` — the three boards. `shots/` — every render, by job. `review/` — working sheets.
- The verification copy is still at `~/unity-clones/hero-build` for quick follow-up renders.
