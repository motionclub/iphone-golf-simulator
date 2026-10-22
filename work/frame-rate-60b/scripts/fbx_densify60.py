"""FRAME_RATE_60B: give a baked 30 fps FBX a key every 1/60 s, in place, when its source scene is gone.

Every animation curve keeps all of its keys (same times, same values: the approved poses at the shared frames);
the missing 1/60 s keys between them come from a monotone cubic (Fritsch-Carlson, as golf_swing.Curve: through
every key, never overshooting between two) and the whole curve is written as linear keys at 60 Hz, which is how
Unity plays a resampled take. Constant (stepped) curves stay stepped. GlobalSettings TimeMode -> 60 fps.
Geometry, IDs and connections are written back as read (emote-fluid's binary FBX round trip).

    Blender -b --factory-startup --python fbx_densify60.py -- <in.fbx> <out.fbx> [...pairs]
"""
import sys, os, array, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fbx_curves as FB
import numpy as np

TICK60 = 769769300          # KTime ticks in 1/60 s (46186158000 per second)


def pchip_slopes(t, v):
    n = len(t); m = np.zeros(n)
    if n < 2: return m
    h = np.diff(t); d = np.diff(v) / h
    if n == 2: return np.array([d[0], d[0]])
    for i in range(1, n - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    def end(h0, h1, d0, d1):
        e = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
        if e * d0 <= 0: return 0.0
        if d0 * d1 <= 0 and abs(e) > 3 * abs(d0): return 3 * d0
        return e
    m[0] = end(h[0], h[1], d[0], d[1]); m[-1] = end(h[-1], h[-2], d[-1], d[-2])
    return m


def hermite(t, v, m, x):
    k = np.clip(np.searchsorted(t, x, side='right') - 1, 0, len(t) - 2)
    h = t[k + 1] - t[k]; s = (x - t[k]) / h
    return ((2 * s**3 - 3 * s**2 + 1) * v[k] + (s**3 - 2 * s**2 + s) * h * m[k] + (-2 * s**3 + 3 * s**2) * v[k + 1] + (s**3 - s**2) * h * m[k + 1])


def densify(src, dst):
    root, version, models, channels = FB.read(src)
    gs = next(e for e in root.elems if e.id == b'GlobalSettings')
    props = next(e for e in gs.elems if e.id == b'Properties70')
    for p in props.elems:
        if p.props and p.props[0] == b'TimeMode': p.props[4] = 3
        if p.props and p.props[0] == b'CustomFrameRate': p.props[4] = 60.0
    # every AnimationCurve in the file, not only the ones on models (blend-shape DeformPercent curves too)
    objects = next(e for e in root.elems if e.id == b'Objects')
    curves = [e for e in objects.elems if e.id == b'AnimationCurve']
    added = stepped = 0
    for c in curves:
        times = np.array(FB.data(c, b'KeyTime'), np.int64); vals = np.array(FB.data(c, b'KeyValueFloat'), np.float64)
        if len(times) < 2: continue
        grid = np.rint(times / TICK60).astype(np.int64)
        assert np.all(np.abs(times - grid * TICK60) <= 4), (src, "keys off the 60 Hz grid")
        full = np.arange(grid[0], grid[-1] + 1)
        if len(full) == len(grid): continue
        flags = list(FB.data(c, b'KeyAttrFlags'))
        constant = all(f & 0x2 for f in flags)
        x = full.astype(np.float64)
        if constant:
            idx = np.searchsorted(grid, full, side='right') - 1; new = vals[idx]; stepped += 1
        else:
            t = grid.astype(np.float64); new = hermite(t, vals, pchip_slopes(t, vals), x)
            new[np.searchsorted(full, grid)] = vals          # the original keys exactly
        added += len(full) - len(grid)
        FB.assign(c, b'KeyTime', array.array('l', (full * TICK60).tolist()))
        FB.assign(c, b'KeyValueFloat', array.array('f', new.astype(np.float32).tolist()))
        flag = (0x2 | (1 << 8)) if constant else (1 << 2 | 1 << 8 | 1 << 13 | 1 << 14)
        FB.assign(c, b'KeyAttrFlags', array.array('i', [flag]))
        FB.assign(c, b'KeyAttrDataFloat', array.array('f', [0.0, 0.0, 9.419963346924634e-30, 0.0]))
        FB.assign(c, b'KeyAttrRefCount', array.array('i', [len(full)]))
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    FB.write(dst, root, version)
    print(f"DENSIFY60 {os.path.basename(src)}: {len(curves)} curves, {added} keys added ({stepped} stepped curves held), TimeMode 60; sha {hashlib.sha256(open(dst,'rb').read()).hexdigest()[:12]}")


args = sys.argv[sys.argv.index("--") + 1:]
for s, d in zip(args[::2], args[1::2]): densify(s, d)
