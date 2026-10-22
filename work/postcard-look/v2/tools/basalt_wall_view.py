"""basalt_wall_view.py <out.png> [new|before|both]: the basalt as the Game view will show it: sRGB(clip(lin(albedo) x LK_BASALT Tint x wall key light + lin(E) x (1,.8,.5))),
1x tile and 3x3 tiles side by side.  'before' = the v3 PNGs (v2/tex/v4/model/*_before.rgb.z), 'both' = before above after."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, lab
gl = lab.gl


def make(mode):
    if mode == 'before':
        import smoke_model as sm
        C = sm.load_z('Basalt_C_before.rgb', (1024, 1024, 3)); E = sm.load_z('Basalt_E_before.rgb', (1024, 1024, 3))
    else:
        d = lab.gen('Basalt'); C, E = d['Basalt_C.png'], d['Basalt_E.png']
    sp = gl.basalt_spec()
    lin = gl.s2l(C / 255.0) * gl.s2l(np.array(sp['tint']))[None, None, :] * gl.BASALT_WALL_LIGHT[None, None, :] + gl.s2l(E / 255.0) * np.array([1.0, 0.8, 0.5])[None, None, :]
    img = gl.l2s(np.clip(lin, 0, 1))
    one = lab.fit(img, 700)
    t3 = lab.fit(np.tile(img, (3, 3, 1)), 700)
    return np.concatenate([lab.label(one, 'BASALT 1 TILE (8 M) ' + mode.upper()), lab.label(t3, '3X3 TILES ' + mode.upper())], 1)


mode = sys.argv[2] if len(sys.argv) > 2 else 'new'
lab.write(sys.argv[1], np.concatenate([make('before'), make('new')], 0) if mode == 'both' else make(mode))
