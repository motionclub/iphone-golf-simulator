"""Compare the game midline profile (|x|<4 mm, max z per y) with the sheet-17 profile, aligned at the nasion (min z over y -8..+8)."""
import sys, json, numpy as np
sys.argv += [] 
import nose_off as NO, off
ref = np.load(NO.HERE + '/nose/ref_profile.npy')
def game_profile(over, ys):
    G = NO.head(over); half, front = off.slices(G, NO.h.tri, ys, xlim=4)
    return front
def compare(over, label=''):
    ys = np.arange(10, -66, -2.0)
    g = game_profile(over, ys); r = np.interp(ys, ref[::-1, 0], ref[::-1, 1])
    nas = (ys <= 8) & (ys >= -8); off_ = np.nanmin(g[nas]) - np.min(r[nas]); r = r + off_
    d = g - r
    print(label, 'tip game y=%.0f z=%.1f | ref y=%.0f z=%.1f' % (ys[np.nanargmax(g)], np.nanmax(g), ys[np.argmax(r)], np.max(r)))
    print('   y  ' + ' '.join(f'{y:5.0f}' for y in ys[::2]))
    print(' game ' + ' '.join(f'{v:5.1f}' for v in g[::2]))
    print('  ref ' + ' '.join(f'{v:5.1f}' for v in r[::2]))
    print(' diff ' + ' '.join(f'{v:5.1f}' for v in d[::2]))
    return ys, g, r
if __name__ == '__main__':
    for a in sys.argv[1:]:
        compare(json.load(open(a)) if a != '-' else {}, a)
