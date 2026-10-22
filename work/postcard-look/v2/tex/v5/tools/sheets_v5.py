"""sheets_v5.py <Look dir> <out dir>: texture evidence sheets, v5 BEFORE (v5/before) vs NOW: sheet_grass_v5.png (albedo 3x3 + phone view), sheet_lava_v5.png, sheet_basalt_v5.png, sheet_scrub_v5.png. Blender python."""
import sys, os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools')); sys.path.insert(0, HERE)
import lab, grass_preview as gp, basalt_view as bv
g = lab.gl
BEFORE = os.path.join(HERE, '..', 'before')
now, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
def rd(d, n): return g.read_png(os.path.join(d, n + '_C.png'))[..., :3].astype(np.float32) / 255
# grass: per material: BEFORE 3x3 | NOW 3x3 | BEFORE phone view | NOW phone view
rows = []
for m, h in (('Fairway', 8), ('Green', 8), ('Rough', 8), ('Scrub', 9)):
    b3 = lab.fit(lab.tile(rd(BEFORE, m), 3), 400); n3 = lab.fit(lab.tile(rd(now, m), 3), 400)
    bv_ = gp.view(BEFORE, m, h, (225, 400)); nv = gp.view(now, m, h, (225, 400))
    rows.append(lab.hstack([lab.label(b3, f'{m} BEFORE 3x3'), lab.label(n3, f'{m} NOW 3x3'), lab.label(bv_, 'phone BEFORE'), lab.label(nv, 'phone NOW')]))
lab.write(os.path.join(out, 'sheet_grass_v5.png'), lab.vstack(rows))
# lava
sp = g.lava_spec()
def shade(d):
    C, E, N = [g.read_png(os.path.join(d, 'Lava_%s.png' % k)) for k in 'CEN']
    return g.lava_shader_model(C, E, N, sp)[1] / 255.0
A = shade(BEFORE); B = shade(now)
def lrow(img, tag):
    p, hit = lab.persp(lab.tile(img, 2), 24 * 2, size=(900, 280), cam_h=8.0, pitch_deg=-8.0)
    return lab.vstack([lab.hstack([lab.label(lab.fit(img, 450), tag + ' 1 tile (24 m)'), lab.label(lab.fit(lab.tile(img, 3), 450), '3x3')]), lab.label(p, tag + ' phone grazing')])
ref = g.read_png(os.path.join(HERE, '..', 'refs', 'crater_lava_crop.png'))[..., :3].astype(np.float32) / 255
lab.write(os.path.join(out, 'sheet_lava_v5.png'), lab.hstack([lrow(A, 'BEFORE (v4)'), lrow(B, 'NOW (v5)'), lab.label(lab.fit(ref, 450, 600), 'crater.jpg pool')]))
# basalt
lab.write(os.path.join(out, 'sheet_basalt_v5.png'), lab.hstack([lab.vstack([lab.label(lab.fit(bv.shade(d), 560), t + ' 1 tile (8 m, lit + glow)'), lab.label(lab.fit(lab.tile(bv.shade(d), 3), 560), '3x3')]) for d, t in ((BEFORE, 'BEFORE (v4)'), (now, 'NOW (v5)'))]))
print('wrote sheets in', out)
