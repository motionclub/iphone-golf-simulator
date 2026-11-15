# The hero as I would build it — code-built model, 2026-11-11

Both heroes here are new models generated entirely by one script, `hero_gen.py`, and rendered in Blender. They are not based on the current game characters. Nothing in `Unity/` changed, and these are not yet rigged or in the game.

| Sheet | Shows |
|---|---|
| `sheets/01_male_turnaround.jpg` | Front, three-quarter, side, back |
| `sheets/02_female_turnaround.jpg` | Same views |
| `sheets/03_faces.jpg` | Both faces: front, three-quarter, side |
| `sheets/04_details.jpg` | Polo and shoes, both heroes |
| `sheets/05_colourways.jpg` | Four colourways each, one with a cap |
| `sheets/06_game_mesh.jpg` | Full detail beside the game-budget mesh with its wireframe |

## The design

- **Soft-toy athlete, about six heads tall.** This follows the art bible's north star (Switch Sports clarity, soft plastic, stocky-friendly proportions) more closely than the current semi-realistic heroes do.
- **One generator, two presets.** Man and woman share every rule and differ only in numbers (shoulder width, waist, limb thickness, eye size, hair). They read as one family.
- **Plain, generic faces.** Round eyes with a catchlight, a soft brow arc, a small nose bump, a closed smile, blush on the cheeks. Brows, lids and mouth are separate small meshes, so expressions can be driven by a few bones.
- **Limbs with shape.** Shoulder, upper arm, elbow, a forearm that tapers to the wrist; thigh, knee, calf, ankle. No tubes.
- **Hands with four fingers and a thumb,** slightly oversized.
- **Garments are their own meshes** with cloth thickness: a polo with a collar, placket, buttons, sleeve bands and a crest; shorts with a side stripe; a pleated skirt on a waistband with fitted shorts under it.
- **A real low sneaker.** Built on a last with a rounded toe lower than the heel, a waist, the tip leaning toward the big toe, a flat cupsole with an outsole line, a heel tab, laces and a collar the sock sits inside. There is no foot mesh; the leg ends inside the sock.
- **Every colour zone is a material:** primary, secondary, accent, skin, hair. A colourway is three colour values and no textures.

## Fit for the game

| Measure | Man | Woman | Current heroes |
|---|---|---|---|
| Triangles, game mesh | 23,240 | 24,500 | 227,907 and 205,999 |
| Triangles, render mesh | 426,232 | 387,272 | — |
| Height | 1.71 m | 1.65 m | 1.73 m |
| Textures needed | none | none | 2048² skin and cloth maps |
| Separate parts | body, face, hair, top, collar, placket, bottom, socks, shoes, wristband, cap | same, with skirt | body plus kit meshes |

The game mesh is the same model reduced part by part to a fixed budget (body 9,000, each shoe 2,400, top 3,200 and so on); sheet 06 shows it next to the full-detail version.

## What it still needs before it can be played

- **A skeleton and skin weights.** The joint positions are parameters in the script, so a matching rig can be generated from the same numbers. Not done.
- **Animation retargeting.** Proportions differ from the current heroes, so existing clips need retargeting.
- **Clean topology.** The game mesh is an automatic reduction. It holds the silhouette but is not edge-looped for deformation at elbows, knees and shoulders.
- **The game's own shading.** These renders use Blender's lighting, not the game's.

## Weak points in this version

- The hair is a smooth helmet shape; it needs clumps or a parting to read as hair.
- The cap sits on top of the hair instead of replacing it, so the brim floats slightly.
- The shoes are clean but plain: laces barely read and there are no panel lines.
- Shoulders are a little puffy where the sleeve meets the yoke.
- No golf or bowling outfits yet.

## Run it

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python hero_gen.py -- sex=male out=out/final views=front,q,side,back,face,shoes,top save=1
```

Options: `sex=male|female`, `kit=primary,secondary,accent` (hex), `cap=1`, `kits=name:p,s,a[:cap]|...` for a colourway loop, `game=1 wire=1` for the budget mesh, `bare=1` for the body alone, `skin=<hex>`. Body numbers live in the `P` preset at the top of the script. Each run takes about a minute. `out/final` also holds `male.blend`, `female.blend` and the two `_game.blend` files.
