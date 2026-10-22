"""basalt_view.py <dir> <out.png> [<dir2> ...]: per dir: 1 tile lit with the key light fitted for the wall (BASALT_WALL_LIGHT x live Tint) + the glow (emission) as the Game view adds it, and 3x3 of the same.
Blender python. Preview only (no fog, no lava lights)."""
import sys, os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
import lab
g = lab.gl
def shade(d):
    C = g.read_png(os.path.join(d, 'Basalt_C.png'))[..., :3].astype(np.float32) / 255
    N = g.read_png(os.path.join(d, 'Basalt_N.png'))[..., :3].astype(np.float32) / 255 * 2 - 1
    E = g.read_png(os.path.join(d, 'Basalt_E.png'))[..., :3].astype(np.float32) / 255
    sp = g.basalt_spec()
    tint = lab.s2l(np.array(sp['tint'], np.float32))
    L = np.array([-0.45, 0.30, 0.84], np.float32); L /= np.linalg.norm(L)
    ndl = np.clip((N * L).sum(-1) / 0.84 * 0.6 + 0.4, 0.1, 1.4)[..., None]       # crude directional shading on top of the fitted flat light
    lin = lab.s2l(C) * tint * g.BASALT_WALL_LIGHT.astype(np.float32) * ndl + lab.s2l(E) * np.array([1.0, .80, .50], np.float32)
    return lab.l2s(np.clip(lin, 0, 1))
if __name__ == '__main__':
    out = sys.argv[2]; cols = []
    for d in [sys.argv[1]] + sys.argv[3:]:
        im = shade(d)
        cols.append(lab.vstack([lab.label(lab.fit(im, 640), os.path.basename(d.rstrip('/')) + ' 1 tile (8 m)'), lab.label(lab.fit(lab.tile(im, 3), 640), '3x3')]))
    lab.write(out, lab.hstack(cols)); print('wrote', out)
