# PLAN — Clothing V3: real fabric, real shine, no breaks, bowling outfits (2026-10-25)

Adnan (10-25): "create bowling clothes, as well as elevate our current lineup of clothes … no actual texture to the clothes …
pants and shirt don't overlap" — then: "current clothes actually do an ok job of not looking painted on, but there's no texture to
the shirts, limited shine and overall look, and also sometimes they break." Use the internet and Blender to the best of our ability.
Work dir: `work/clothing-v3/`. Stage only, no commits. Every Unity/Blender launch through `work/delegation-2026-10-17/heavy.sh`.

## 1. What is actually wrong (measured, not guessed)

| Symptom | Root cause found in the shipped data |
|---|---|
| "No texture" | `Kit_*_N.png` (2048²) is flat blue except seam/hem lines; `Kit_*_M.png` AO (R) is ~white over every panel. The only fabric detail is the tiling weave (`KitV2_FabricAtlas.png`, 512², 4 fabrics × 240 px). `TennisCloth` fades the weave to **zero** before Nyquist (`fade`, `frequency` 8–12), so at gameplay distance there is nothing left: flat colour × lighting. |
| "Limited shine" | Both heroes run the knit path (`_FemaleSurface` 1, set by `FemaleGarmentFinish` / `MaleFaceFinish`): specular exists **only for rubber/foam**; cloth gets Lambert + a Charlie velvet lobe (sheen .32). Smoothness .08. Polyester tennis piqué / rayon have a visible soft sheen; ours has none. |
| "Shirt and pants don't overlap" | Hem vs waistband top, measured per azimuth: male tennis polo **+3.2…4.1 cm** (shallow), female tank **−0.1…−0.4 cm (no overlap at all)**, golf female +0.5…1.2 cm, golf male tucked +1.8…3.2 cm. |
| "Sometimes they break" | Known from the 10-17/18 garment pipeline (`work/clothing-v2/pipeline/GATE_RESULTS.md`): the corrective solver skips covered skin > 3 cm from uncovered skin ("deep") although the cover still draws it in some frames. Opt-in fix `GP_COVER_REF` measured **−48 % tears male, −32 % golf female** on the 40 worst poses, then the work was paused (10-18). Shorts poke through the polo hem when kneeling (LAYERS 63k). |

## 2. Research (web, 10-25) — what we take from it
- Detail that survives ~300 px character height is **5–40 mm folds, hem/placket edges, rib bands, and a weave enlarged 4–8×**; true-scale weave can only shimmer (Polycount, 80.lv stylized cloth breakdowns, Unity detail-map docs).
- The main "this is cloth" signal in stylized games = **a baked fold normal map with a few big, simplified folds** (armpit drag, waist bunching, crotch/leg crease) + cavity/AO multiply kept in a neutral mask so palette swaps keep it (Marc Brunet / Sitompul breakdowns; Shining Nikki far/mid/close fabric tests).
- Shading: Filament / HDRP cloth = Charlie sheen + Ashikhmin/Neubelt visibility + wrapped diffuse (w≈.5) + subsurface tint; "common fabrics: base colour carries chroma, sheen ≈ luminance". Satin/rayon/leather use the standard or **anisotropic** model (a real specular lobe) — that is our missing shine.
- Mélange/heather: ±4–6 % luminance grain at 2–4 mm, applied after the tint, keeps every swatch alive.
- Pipeline: Blender-only route = cloth-sim a dense copy of the existing shell → sculpt/crease accents → **bake Selected→Active onto the shipped low-poly UVs** (cage 5–10 mm); bake overlapping flaps (hem) separately. Mobile budget: ≤1K–2K per garment, one shared tiling detail atlas, ASTC, no crunch.
- Bowling: retro camp-collar shirt (boxy, short sleeves, two-tone yoke/panels, chest pocket, chain-stitch back art, rayon/gabardine), modern dye-sub jersey; women's: fitted bowling shirt + capris / A-line or skort; rental-style two/three-tone leather shoes with the size on the heel.

Sources: 80.lv/articles/001agt-eureka-sculpting-stylized-cloth-pbr-texturing · 80.lv/articles/creating-stylized-pbr-characters-for-games ·
polycount.com/discussion/comment/2650882 · polycount.com/discussion/comment/2785244 · adobe.com/…/shining-nikki-creating-elegant-materials… ·
google.github.io/filament/Filament.md.html (Cloth model) · knarkowicz.wordpress.com/2018/01/04/cloth-shading · docs.unity3d.com/460/Documentation/Manual/HOWTO-UseDetailTexture.html ·
creativebloq.com/3d/how-to-make-a-t-shirt-in-blender · en.wikipedia.org/wiki/Bowling_shirt · therealmccoys.com/products/rayon-bowling-shirt-black ·
hermes.bowling.com/products/classic-unisex-rental.htm · wiisports.fandom.com/wiki/Bowling_(sport)

## 3. Workstreams (in execution order)

### A. Fabric library, built in Blender (replaces the 512² atlas)
Real yarn geometry (Geometry Nodes curves → mesh), tileable, baked orthographically (height → normal, AO, fibre/colour variation) at 1024² per fabric
into a **2048² atlas v3** (3×3 cells + gutters): tennis piqué (enlarged ~2.5× for read), jersey, 1×1/2×2 rib, twill (shorts/trousers), gabardine/rayon
plain weave (bowling), pleat suiting, leather grain, shoe mesh, sock knit. Each cell also gets a **macro level** (heather grain 2–4 mm) stored so
the shader can keep it after the threads fade. Tool: `work/clothing-v3/fabric/` (`yarn.py`, `bake_fabric.py`, `atlas.py`).

### B. Fold + AO maps per garment, baked in Blender
For every shipped garment: dense copy of the exact installed mesh (same UVs) → gravity drape against the body in the bind pose (pinned
shoulders/waistband/collar, short sim so the silhouette is unchanged) + procedural crease accents (armpit drag, waist bunch, elbow/sleeve
compression, crotch "whiskers", knee-back) → **bake Selected→Active normals onto the shipped low mesh** + fold AO + cavity. Composited into
the existing `_N` / `_M` (seams/stitches kept). Geometry and UVs untouched ⇒ fit, cover, correctives and hide lists stay valid.
Tool: `work/clothing-v3/folds/`.

### C. Shader: fabric that never goes flat + real shine (`TennisCloth` + lobby `MatchHeroSurfaces.swift`)
1. Weave: fade threads before aliasing, but fall back to the cell's **mip average + macro heather**, never to nothing.
2. Fabric-aware shine: add a soft fibre specular lobe per fabric (piqué/polyester: GGX r≈.5, strength low; rayon/satin: anisotropic along
   the grain; leather: sharper; cotton twill: almost none) + keep the Charlie sheen, sheen tint ≈ sqrt(albedo).
3. Fold AO/cavity from the M map, heather grain after the tint (palette-neutral).
4. Same math in the SceneKit lobby shader; re-sync heroes (`work/hero-sync/sync_heroes.sh`).

### D. Breakage (tears / poke-through)
Resume the paused pipeline with the proven fix: `GP_COVER_REF` runs for male tennis polo (T5_MT), female tennis (K12_FT base), golf female (T5_GF);
LAYERS: hem stand-off so shorts no longer pierce the polo hem when kneeling. Install passing runs with `handoff/install_garments.sh`.
Overlap: female tank hem lowered ~3–4 cm over the skirt waistband (rebuild via `tank2.py`, same pipeline).

### E. Bowling outfits (male + female), same garment system
- Male: retro camp-collar bowling shirt (boxy, short sleeves, two-tone yoke + front panels as the trim channel, chest pocket as geometry,
  untucked hem ~6 cm below the waistband) + relaxed flat-front trousers; rental-style two-tone bowling shoes (heel size number); socks.
- Female: fitted camp-collar bowling shirt + capri trousers (or skort), two-tone bowling shoes.
- Builders: `polo2.py` new designs (`bowling_male`, `bowling_female` with a camp collar), `pants2.py` (`bowling_male_trousers`, `female_capri`),
  `shoe4.py` (`bowling_*`). Fit → cover → correctives through `work/clothing-v2/pipeline`, fabric = rayon/gabardine cell.
- Game: BowlingKitHero_Male/Female prefabs (copies of the match heroes with the bowling kit installed), worn by `BowlingHero.Spawn`;
  every colour customizable (shirt / yoke / trousers / shoe panels).

## 4. Gates (binary; proof in `work/clothing-v3/proof/`)
| Gate | PASS when |
|---|---|
| TEXTURE_FAR | gameplay-distance Unity capture: shirt-region luminance std-dev (high-pass) ≥ 2× today's, on white, navy and red swatches |
| TEXTURE_NEAR | locker/close-up capture shows the knit/weave structure on every garment (author read + side-by-side) |
| NO_SHIMMER | slow 8-frame pan: mean per-pixel temporal delta on cloth ≤ today's + 10 % |
| SHINE | brightest 2 % of shirt pixels under the key ≥ 1.25× the shirt mean (today measured first), no plastic look (Adnan) |
| PALETTE | 6 swatches (white, near-black, red, blue, green, yellow) keep hue; detail visible on all |
| SHAPE | garment vertex positions/UVs unchanged for A–C (max error 0 mm) |
| TEARS | per hero tear px over the 153-pose suite ≤ 0.6× today's install; LAYERS not worse |
| OVERLAP | every top's hem ≥ 3 cm below its bottom's waistband top at all 8 azimuths (tucked golf exempt) |
| BOWLING | both bowling kits installed + worn in the bowling scene, tear suite on the bowling clips, colours customizable |
| PERF | ≤ 0.3 ms/hero at 1080p (today .056–.081) |
| LOBBY | Adnan (10-25): "make sure lobby clothes look just as high quality as they do in game". Same fabric atlas v3, fold maps and shine math in `MatchHeroSurfaces.swift`; lobby vs game MAD ≤ today + 1 AND the garment high-pass detail energy in the lobby render ≥ 0.85× the Unity render of the same shot (all 4 heroes + bowling) |

## 5. Order
A + B (Blender) → C (shader) → proof round 1 (Unity clone captures, both heroes, tennis + golf) → D runs (queued through heavy.sh while C iterates) →
E (bowling) on the finished system → install + lobby sync → GATE_RESULTS.md.
