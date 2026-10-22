"""Phone-view previews of grass albedos: for a set of materials/holes, a perspective view (camera 2.2 m up, pitch -19 deg, 60 deg vfov = the game's tee frame) of the
tiled albedo lit with lit_predict's 'game' model (per-hole light + tint + additive term), BEFORE (v5/before) vs NOW (a dir). Not Game-view proof (no bump, no shadows, no fog).
usage: grass_preview.py <now_dir> <out.png> [Mat:hole ...]     e.g. Fairway:8 Fairway:9 Green:8 Rough:8 Scrub:9"""
import sys, os, importlib.util, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', '..', 'tools')
sys.path.insert(0, TOOLS)
import lab
import lit_predict as lp
gl = lab.gl
BEFORE = os.path.join(HERE, '..', 'before')
TILE = dict(Fairway=10.0, Green=6.0, Rough=12.0, Scrub=12.0)
def lit(alb, hole, mat):
    L = np.array(lp.hole_light_linear(lp.parse_lights()[hole]))
    tints = lp.parse_tints()
    t = tints.get((hole, mat), (.94, .94, .94))
    t = np.array(t[:3]) if len(t) >= 3 else np.array([t] * 3)
    lin = lab.s2l(alb) * lab.s2l(t.astype(np.float32)) * L * np.array(lp.GAME_MUL) + np.array(lp.GAME_ADD[hole])
    return lab.l2s(np.clip(lin, 0, 1))
def view(d, mat, hole, size=(450, 800)):
    a = gl.read_png(os.path.join(d, mat + '_C.png'))[..., :3].astype(np.float32) / 255
    a = lit(a, hole, mat)
    img, hit = lab.persp(a, TILE[mat], size=size, cam_h=2.2, pitch_deg=-19.0, fov_v=60.0, ss=2)
    return img
if __name__ == '__main__':
    now, out = sys.argv[1], sys.argv[2]
    items = [x.split(':') for x in sys.argv[3:]]
    rows = []
    for m, h in items:
        h = int(h)
        b = view(BEFORE, m, h); n = view(now, m, h)
        sd = lambda im: float(lab.gl.lum(im[int(im.shape[0] * .4):]).std() * 255)
        print(f'{m} hole{h}: lower-60% luminance sd (model view, 450x800) before {sd(b):.1f}/255  now {sd(n):.1f}/255  ratio {sd(n)/sd(b):.2f}')
        rows.append(lab.hstack([lab.label(b, f'{m} hole{h} BEFORE'), lab.label(n, f'{m} hole{h} NOW')]))
    lab.write(out, lab.hstack(rows, pad=12))
    print('wrote', out)
