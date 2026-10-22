"""lava_v3_sheet.py <installed_dir> <new_dir> <out.png>: GolfLava shader-model preview (live GolfLook.cs constants) of the installed vs the new Lava maps:
1x, 3x3, phone-grazing perspective, and the crater.jpg crop. Blender python (numpy)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import lab
gl = lab.gl
inst, new, out = sys.argv[1:4]
sp = gl.lava_spec()
def load(d):
    return [gl.read_png(os.path.join(d, 'Lava_%s.png' % k)) for k in 'CEN']
def shade(C, E, N):
    h, rgb = gl.lava_shader_model(C, E, N, sp)
    return rgb / 255.0
A = shade(*load(inst)); B = shade(*load(new))
ref = gl.read_png(os.path.join(gl.ROOT, 'work/postcard-look/v2/tex/refs/ref_lava_crop.png')).astype(np.float64) / 255
def row(img, tag):
    one = lab.fit(img, 512)
    t3 = lab.fit(lab.tile(img, 3), 512)
    p, hit = lab.persp(lab.tile(img, 2), 24 * 2, size=(1040, 330), cam_h=8.0, pitch_deg=-8.0)
    return lab.vstack([lab.hstack([lab.label(one, tag + ' 1X'), lab.label(t3, tag + ' 3X3')]), lab.label(p, tag + ' PHONE GRAZING')])
sheet = lab.hstack([row(A, 'INSTALLED (10:14)'), row(B, 'NEW v3')])
r_small = lab.fit(ref, 1040, 380) if ref.shape[1] >= 1040 else ref
sheet = lab.vstack([sheet, lab.label(r_small, 'TARGET CRATER.JPG POOL')])
lab.write(out, sheet); print('wrote', out, sheet.shape)
