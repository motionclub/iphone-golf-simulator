"""evidence sheets for the v2 texture pass -> work/postcard-look/v2/tex/sheet_*.png (Blender python)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import lab
gl = lab.gl
ROOT = lab.ROOT
BEF = os.path.join(ROOT, 'work/postcard-look/v2/tex/before')
AFT = os.path.join(ROOT, 'Unity/Assets/Resources/Course/Look')
OUT = os.path.join(ROOT, 'work/postcard-look/v2/tex')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lit_predict as lp
REF = os.path.join(OUT, 'refs')
def ref(name):
    """reference crops written by the system-python step (ref_*.png in scratch/); returns float image or None."""
    p = os.path.join(REF, name)
    return lab.f01(lab.load(p)) if os.path.exists(p) else None

lights = lp.parse_lights()
Ls = {h: np.array(lp.hole_light_linear(lights[h])) for h in (8, 9, 10)}
cs = lp.parse_tints()
rec = json.load(open(os.path.join(OUT, 'recommended_tints.json')))
def tint_for(h, nm, recommended):
    if recommended and str(h) in rec and nm in rec[str(h)]:
        return np.array(rec[str(h)][nm])
    return np.array(cs.get((h, nm), lp.TABLE_TINT))
def lit(C, h, nm, recommended):
    t = lab.s2l(tint_for(h, nm, recommended))
    return lab.l2s(np.clip(lab.s2l(lab.f01(C)) * Ls[h] * t, 0, 1))
STILL = lp.STILL_TARGET
HN = {8: 'NEEDLE', 9: 'SPLIT', 10: 'CRATER'}

# ---------------------------------------------------------------- grass
rows = []
S = 220
for nm in ('Fairway', 'Green', 'Rough', 'Scrub'):
    b = lab.load(os.path.join(BEF, nm + '_C.png')); a = lab.load(os.path.join(AFT, nm + '_C.png'))
    cells = [lab.label(lab.fit(lab.tile(lab.f01(b), 3), S), nm.upper() + ' BEFORE 3X3', 1), lab.label(lab.fit(lab.tile(lab.f01(a), 3), S), nm.upper() + ' AFTER 3X3', 1)]
    for h in (8, 9, 10):
        if nm == 'Scrub' and h != 9:
            continue
        cells.append(lab.label(lab.fit(lab.tile(lit(b, h, nm, False), 2), S), '%s LIT BEFORE (OLD TINT)' % HN[h], 1))
        cells.append(lab.label(lab.fit(lab.tile(lit(a, h, nm, True), 2), S), '%s LIT AFTER' % HN[h], 1))
        tgt = np.ones((S, 60, 3)) * (np.array(STILL[h][nm]) / 255.0)
        cells.append(lab.label(tgt, 'STILL', 1))
    rows.append(lab.hstack(cells))
w = max(r.shape[1] for r in rows)
rows = [np.pad(r, ((0, 0), (0, w - r.shape[1]), (0, 0)), constant_values=0.1) for r in rows]
lab.write(os.path.join(OUT, 'sheet_grass.png'), lab.vstack(rows))
print('wrote sheet_grass.png')

# ---------------------------------------------------------------- lava
bC, bE = lab.load(os.path.join(BEF, 'Lava_C.png')), lab.load(os.path.join(BEF, 'Lava_E.png'))
aC, aE = lab.load(os.path.join(AFT, 'Lava_C.png')), lab.load(os.path.join(AFT, 'Lava_E.png'))
gb = lab.lava_game(bC, bE, (1.3, 0.85, 0.55)); ga = lab.lava_game(aC, aE, (1.1, 1.1, 1.1))
gb_old = lab.lava_game(bC, bE, (2.6, 2.4, 2.2))
persp_a, _ = lab.persp(lab.tile(ga, 2), 48, size=(1000, 360), cam_h=8.0, pitch_deg=-8.0)
persp_b, _ = lab.persp(lab.tile(gb, 2), 48, size=(1000, 360), cam_h=8.0, pitch_deg=-8.0)
r = ref('ref_lava_crop.png')
top = lab.hstack([lab.label(lab.fit(gb_old, 500), 'BEFORE: OLD RUNTIME EMISSION X2.6/2.4/2.2', 1), lab.label(lab.fit(gb, 500), 'BEFORE: EMISSION X1.3/.85/.55', 1), lab.label(lab.fit(ga, 500), 'AFTER: EMISSION X1.1', 1)])
mid = lab.hstack([lab.label(lab.fit(lab.tile(gb, 3), 500), 'BEFORE 3X3', 1), lab.label(lab.fit(lab.tile(ga, 3), 500), 'AFTER 3X3 TILED (NO GRID, NO REPEAT POLYGON)', 1),
                  lab.label(lab.fit(lab.f01(aE), 500), 'AFTER EMISSION MAP (PEAK <= 255,180,60)', 1)])
pers = lab.hstack([lab.label(persp_b, 'BEFORE PERSPECTIVE (CAM 8 M UP, -8 DEG)', 1), lab.label(persp_a, 'AFTER PERSPECTIVE', 1)])
parts = [top, mid, pers]
if r is not None:
    parts.append(lab.label(lab.fit(r, 1000, 460), 'TARGET crater.jpg lava pool (crop)', 1))
lab.write(os.path.join(OUT, 'sheet_lava.png'), lab.vstack(parts))
print('wrote sheet_lava.png')

# ---------------------------------------------------------------- basalt
bC, bN, bE = [lab.load(os.path.join(BEF, 'Basalt_%s.png' % k)) for k in 'CNE']
aC, aN, aE = [lab.load(os.path.join(AFT, 'Basalt_%s.png' % k)) for k in 'CNE']
lb = gl.lit_preview(bC, bN, bE); la = gl.lit_preview(aC, aN, aE)
r = ref('ref_basalt_crop.png')
top = lab.hstack([lab.label(lab.fit(lb, 560), 'BEFORE LIT 1X', 1), lab.label(lab.fit(la, 560), 'AFTER LIT 1X', 1), lab.label(lab.fit(lab.f01(aN), 560), 'AFTER NORMAL', 1), lab.label(lab.fit(lab.f01(aE), 560), 'AFTER EMISSION', 1)])
mid = lab.hstack([lab.label(lab.fit(lab.tile(lb, 3), 560), 'BEFORE LIT 3X3', 1), lab.label(lab.fit(lab.tile(la, 3), 560), 'AFTER LIT 3X3', 1)] + ([lab.label(lab.fit(r, 560, 560), 'TARGET crater.jpg walls', 1)] if r is not None else []))
lab.write(os.path.join(OUT, 'sheet_basalt.png'), lab.vstack([top, mid]))
print('wrote sheet_basalt.png')

# ---------------------------------------------------------------- smoke
bS = lab.load(os.path.join(BEF, 'Smoke_C.png')); aS = lab.load(os.path.join(AFT, 'Smoke_C.png'))
def over(S, bg):
    a = S[..., 3:4].astype(np.float64) / 255
    return lab.f01(S[..., :3]) * a + np.array(bg) * (1 - a)
red = np.array([180, 60, 30]) / 255; grey = np.array([90, 80, 85]) / 255
rs = ref('ref_smoke_crop.png')
row1 = lab.hstack([lab.label(over(bS, red), 'BEFORE OVER RED', 1), lab.label(over(aS, red), 'AFTER OVER RED', 1), lab.label(over(bS, grey), 'BEFORE OVER GREY', 1), lab.label(over(aS, grey), 'AFTER OVER GREY', 1)])
parts = [row1]
if rs is not None:
    parts.append(lab.label(lab.fit(rs, row1.shape[1], 380), 'TARGET crater.jpg smoke plumes (crop)', 1))
lab.write(os.path.join(OUT, 'sheet_smoke.png'), lab.vstack(parts))
print('wrote sheet_smoke.png')

# ---------------------------------------------------------------- secondary: Cliff / Rock
cells = []
for nm in ('Cliff', 'CliffDark', 'Rock'):
    for tag, d in (('BEFORE', BEF), ('AFTER', AFT)):
        c = lab.load(os.path.join(d, nm + '_C.png')); n = lab.load(os.path.join(d, nm + '_N.png'))
        cells.append(lab.label(lab.fit(lab.tile(gl.lit_preview(c, n), 3), 380), '%s %s LIT 3X3' % (nm.upper(), tag), 1))
lab.write(os.path.join(OUT, 'sheet_secondary.png'), lab.vstack([lab.hstack(cells[:2] + cells[2:4]), lab.hstack(cells[4:6])]))
print('wrote sheet_secondary.png')
