"""Write README.md (asset table from proof/metrics) + sheets/_overview.jpg. System python3:  python3 readme.py"""
import json
from pathlib import Path
from PIL import Image, ImageDraw
import sys
sys.path.insert(0, str(Path(__file__).parent))
from sheets import panel, font
from gates import lods

ROOT = Path(__file__).resolve().parents[1]
ms = [json.loads(p.read_text()) for p in sorted((ROOT / 'proof/metrics').glob('*.json'))]
order = ['A', 'B', 'C']
ms.sort(key=lambda m: (m['kind'].startswith('shore'), not m['kind'].startswith('course landmark'), order.index(m['course']), m['name']))
g = json.loads((ROOT / 'proof/gates.json').read_text())
allpass = all(x['pass_'] for v in g.values() for x in v.values())

# ---- overview contact sheet
T = 320
cols = 7
rows = (len(ms) + cols - 1) // cols
S = Image.new('RGB', (T * cols, (T + 24) * rows), '#1d1f24')
d = ImageDraw.Draw(S)
for k, m in enumerate(ms):
    x, y = (k % cols) * T, (k // cols) * (T + 24)
    S.paste(panel(ROOT / 'renders' / m['name'] / 'match.png', T - 4, T - 4, m['course']), (x + 2, y + 24))
    t0, t0s, t1, t2 = lods(m)
    d.text((x + 4, y + 4), f"{m['name']}  {t0 + t0s:,} tris", fill='white', font=font(15))
S.save(ROOT / 'sheets' / '_overview.jpg', quality=86)

# ---- README
L = ['# Majestic landmark kit (PLAN 4.1 "L")', '',
     'Blender-built, Unity-ready FBX landmarks, hole set pieces and shore kit for the golf courses of '
     '`work/majestic-all-maps/PLAN.md`, matched to the hole targets in `work/majestic-all-maps/refs/holes/` '
     '(crops in `targets/`, positions from `design/HOLE_BRIEFS.md`). **Not installed into Unity**: the golf track places them.', '',
     f"Gates: [GATE_RESULTS.md](GATE_RESULTS.md) — **GATE: LANDMARK_KIT {'PASS' if allpass else 'FAIL'}** "
     f"({len(ms)} assets: SHAPE_MATCH, TRIS, LOD, PIVOT_SCALE, CLEAN, TILE, MATERIALS). Overview: `sheets/_overview.jpg`; "
     'one 1920x1080 sheet per asset in `sheets/<Name>.jpg` (target crop | matching-angle render | facts + gates, then a 4-view turntable, LOD1 and LOD2).', '',
     '## Rebuild (headless, through the heavy-job gate)', '',
     '```bash', 'cd work/majestic-landmarks',
     'bash ../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python scripts/build.py -- [Name ...]',
     'python3 scripts/gates.py && python3 scripts/readme.py   # GATE_RESULTS.md, README table, overview', '```', '',
     'The whole kit builds, renders, exports and re-imports in about 2 minutes (one Blender process, ~3 s per asset). '
     '`scripts/crop_targets.py` re-cuts the target crops listed in `scripts/targets.json`; `scripts/sheets.py` and `scripts/review.py` make the sheets.', '',
     '| file | does |', '|---|---|',
     '| `scripts/kit.py` | builder library: closed-shell primitives (box, lathe, sweep, prism, heightfield slab, noise blob), bevels, per-face or per-vertex colour, glow, LOD quality, finishing (triangulate, weighted normals on hard parts) |',
     '| `scripts/assets_landmarks.py` | Lighthouse, StepTemple, TwinFallsIsle, CalderaVolcano, CalderaWall_A/B |',
     '| `scripts/assets_setpieces.py` | the hole set pieces |', '| `scripts/assets_shore.py` | shore kit |',
     '| `scripts/build.py` | per asset: LOD0 + LOD1 build, impostor atlas, renders, FBX export, re-import, metrics (`proof/metrics/<Name>.json`) |',
     '| `scripts/gates.py` | binary gates -> `GATE_RESULTS.md`, `proof/gates.json` |', '',
     '## Conventions (read before placing)', '',
     '- **Units / axes:** metres, FBX scale 1 (`apply_scale_options=FBX_SCALE_ALL`, `-Z forward, Y up`, `bake_space_transform`), so every object imports '
     'with identity rotation and scale. Blender +Z up -> Unity +Y. Each asset\'s **front faces Blender -Y**, which lands on Unity +Z '
     '(the racket mapping Unity (x, y, z) = Blender (-x, z, -y)); turn the root to face the tee.',
     '- **Hierarchy:** root empty `<Name>` at the pivot -> `<Name>_LOD0`, `<Name>_LOD1`, `<Name>_LOD2` (impostor) and separate parts `<Name>_<Part>_LOD0/1`. '
     'Unity\'s `_LODn` suffix import builds the LODGroup. FX listed as *shared* (`Lighthouse_Beam`, `CalderaVolcano_Plume`, chimney `Smoke`) have no suffix and '
     'stay visible at every distance.',
     '- **One material per asset** (`<Name>_Mat`), made for chat 9\'s `GolfArcade/MajesticDressing` shader: vertex colour = albedo (sRGB in the FBX), '
     'UV0 = (sway, phase) = 0, UV1 = 0, **UV2.x = glow** (lava, lit windows, lantern glass, crater). FX cards use `<Name>_FX` (needs a transparent, '
     'double-sided, UV0.y-scrolling shader: falls, lava fall, plume, smoke, beam, foam; alpha is in vertex colour A). The impostor uses `<Name>_Impostor` '
     '(alpha-clip, double-sided) with `fbx/<Name>_Impostor.png` (front + side views in one atlas).',
     '- **LODs:** LOD1 is rebuilt from the same recipe at lower segment counts with chamfers instead of round bevels and small details dropped '
     '(25–60 % of LOD0). LOD2 is a cross of two cards (4 tris). Flat shore pieces have no LOD2 by design.',
     '- **Pivots:** base centre on the ground (z 0) unless the table says *waterline* (z 0 = sea level, land +Y, sea -Y), *anchor* (rope bridge) or *centre*. '
     'Animated parts sit at their own pivot: `Windmill_Sails` at the hub (spin about local Y = Unity Z), `Waterwheel_Wheel` at the hub (local X), '
     '`Lighthouse_Beam` at the lantern (local Z = Unity Y).',
     '- **Tiling:** ShoreBand / BlackSandShore / CliffSkirt / FoamStrip repeat every 20 m along X; ShoreBand_Arc: 10 tiles of 36 deg close a ring of '
     'radius 31.8 m (centre at local (0, 31.8, 0)); CalderaWall_A/B: 24 segments of 15 deg close a ring of radius 200 m (centre at local (0, -200, 0)); '
     'TILE gate = cut-end vertices identical (0 mm).', '',
     '## Assets', '',
     '| asset | course | holes | LOD0 / LOD1 / LOD2 tris | materials | size x·y·z (m) | pivot | intended position (brief) |', '|---|---|---|---|---|---|---|---|']
for m in ms:
    t0, t0s, t1, t2 = lods(m)
    lo, hi = m['bbox_fbx']
    dims = '·'.join(f'{hi[i] - lo[i]:.1f}' for i in range(3))
    mats = sorted({mm for v in m['reimport'].values() for mm in v['mats']})
    mats = ', '.join(x.replace(m['name'] + '_', '') for x in mats)
    tri = f"{t0 + t0s:,}" + (f" (incl. {t0s} shared FX)" if t0s else '') + f" / {t1:,} / {t2 if t2 else '—'}"
    anim = ('; separate: ' + ', '.join(f'{a} ({b})' for a, b in m['animated'])) if m.get('animated') else ''
    L.append(f"| **{m['name']}** | {m['course']} | {', '.join(map(str, m['holes']))} | {tri} | {mats} | {dims} | {m.get('pivot', 'base')} | "
             f"{m['where']}{anim} |")
L += ['', '## Honest notes and open items', '',
      '- SHAPE_MATCH is my read of each sheet against its feature checklist; Adnan\'s eye is final. Weakest matches: **TwinFallsIsle** (rounder, more '
      'regular outline than the craggy target), **MesaArch** (target is more massive), **WitchCottage** (target is more crooked), **StoneGate** '
      '(the h19 tee target shows a single tall totem pillar edge-on; the brief asks for a gate, so this is a two-pillar gate). '
      '**ToriiGate** and **Waterwheel** have no target view (brief only).',
      '- Previews are Blender EEVEE with a flat course light; the in-game look depends on `MajesticDressing` + the course grade. Waterfalls, lava fall, '
      'plume and foam are plain cards until the Unity FX shader scrolls them.',
      '- The expected-size ranges were written before building; after the first build I widened six of them where my guess had left out a part: '
      'Windmill sails (z to 26 m), WitchCottage chimney (16 m), IceFishingHut stovepipe (4 m), MesaArch/ObsidianArch boulder feet (x), '
      'CalderaWall skirt 3 m under the lava (pivot at lava level, z to 52 m), FoamRing/FoamStrip/ShoreBand_Arc/CliffSkirt bounds. The ranges in the recipes are the current ones.',
      '- Scale: landmarks are built at plausible real sizes (lighthouse 20 m, volcano 288 m wide x 145 m, isle ~100 m x 71 m, caldera ring radius 200 m). '
      'The golf track should scale them uniformly to its course layout; the far ones (volcano, isle, walls) were sized for ~300–800 m viewing distance.',
      '- Not done here (golf track): placement per `MajesticHoleKit`, LODGroup screen sizes, colliders, FX shaders, Unity import check.', '']
(ROOT / 'README.md').write_text('\n'.join(L))
print('README.md +', ROOT / 'sheets' / '_overview.jpg')
