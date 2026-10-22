"""Standard hand-local view specs + sheet composer.  usage (python): from views import specs, sheet"""
import numpy as np, sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3')
from hlib import *
def vec(a): return ','.join('%.5f' % x for x in a)
def local_dir(d_local, side):
    """direction given in local (a', n, w) -> global direction"""
    d = np.array(d_local, float); g = d[0]*A + d[1]*N + d[2]*D
    if side < 0: g = g.copy(); g[0] = -g[0]
    return g
def local_pt(p_local, side):
    return to_global(np.array([p_local], float), side)[0]
def specs(side, scale=0.30, center=(0.0, 0.0, 0.07), views=None):
    """views: name -> (dir_local, up_local). Camera sits along dir_local from the hand centre."""
    V = views or {
        'dorsal':  ((0, -1, 0), (0, 0, -1)),      # looking at the back of the hand, fingers pointing down on screen
        'palmar':  ((0, 1, 0), (0, 0, -1)),
        'radial':  ((1, 0, 0), (0, 0, -1)),       # from the thumb side
        'ulnar':   ((-1, 0, 0), (0, 0, -1)),
        'dist':    ((0, 0, 1), (0, -1, 0)),
        'q_dorsal_radial': ((0.8, -0.6, 0.0), (0, 0, -1)),
        'q_palmar_radial': ((0.8, 0.6, 0.0), (0, 0, -1)),
        'q_palmar_ulnar': ((-0.7, 0.7, 0.0), (0, 0, -1)),
    }
    c = local_pt(center, side)
    out = []
    for nme, (dl, ul) in V.items():
        d = local_dir(dl, side); u = local_dir(ul, side)
        out.append(f'{nme}:{vec(c)}:{vec(d)}:{scale}:55:-40:{vec(u)}')
    return out
