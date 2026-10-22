"""smoke_model.py -- predict GolfLookSmoke's SMOKE_SOFT numbers (effective alpha, median / p99 |delta luminance|, edge step) for a Smoke_C.png
without running Unity.  v2 2026-10-04 (area T, v4 repair).

Run under Blender's python (numpy):  /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 smoke_model.py fit|eval ...

It re-creates the board GolfLookBoards uses: camera (0,9,0) -> (-10,24,130) in the hole frame (x right, y up, z down the hole), 60 deg vertical FOV, 900x1600;
the DRESS_SMOKE card: bottom centre (-10,4,130), 36 x 44 yd, vertical, UV (0,0)..(1,1); material GolfArcade/GolfSurf:
  alpha = clamp(tex.a * _Color.a * _AlphaGain)^_AlphaPower * smoothstep(0, _EdgeFade, min(u,1-u,v,1-v))
  colour = tex.rgb * _Color.rgb * lerp(1, light, _Lit) ; frame = lerp(sky, MixFog(colour), alpha), sRGB(linear blend)
The sky ("without" frame) is a real render from the runtime owner (v2/runtime/shots/<run>/smoke_card_without.jpg, converted to .rgb by PIL).
light and fog are fitted per run from the real "with" frame (per channel G = f ((1-Lit) + Lit (S + e)), A = fog additive), see `fit`.
"""
import sys, os, json
import numpy as np

W, H = 900, 1600
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, '..', 'tex', 'v4', 'model')


def s2l(x):
    x = np.asarray(x, np.float64)
    return np.where(x <= 0.04045, x / 12.92, ((np.maximum(x, 0) + 0.055) / 1.055) ** 2.4)


def l2s(x):
    x = np.clip(np.asarray(x, np.float64), 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def load_z(name, shape):
    import zlib
    return np.frombuffer(zlib.decompress(open(os.path.join(MODEL, name + '.z'), 'rb').read()), np.uint8).reshape(shape)


def load_rgb(name):
    """a board frame (PIL-decoded JPEG of the real Unity run, zlib-compressed raw RGB) -> uint8 (1600, 900, 3)"""
    return load_z(name, (H, W, 3))


def card_uv():
    """per-pixel (u, v, valid) of the smoke card in the 900x1600 board frame."""
    cam = np.array([0.0, 9.0, 0.0]); at = np.array([-10.0, 24.0, 130.0])
    f = (at - cam); f /= np.linalg.norm(f)
    up = np.array([0.0, 1.0, 0.0])
    r = np.cross(up, f); r /= np.linalg.norm(r)
    uu = np.cross(f, r)
    t30 = np.tan(np.radians(30.0)); asp = W / H
    px = (np.arange(W) + 0.5) / W * 2 - 1
    py = 1 - (np.arange(H) + 0.5) / H * 2
    X, Y = np.meshgrid(px, py)
    d = f[None, None, :] + (X * t30 * asp)[..., None] * r[None, None, :] + (Y * t30)[..., None] * uu[None, None, :]
    tt = 130.0 / d[..., 2]
    P = cam[None, None, :] + d * tt[..., None]
    u = (P[..., 0] - (-10 - 18.0)) / 36.0
    v = (P[..., 1] - 4.0) / 44.0
    valid = (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1) & (tt > 0)
    return u, v, valid


def bilin(tex, u, v):
    """tex (n,n,c) float, PNG row 0 = top = v 1."""
    n = tex.shape[0]
    x = u * n - 0.5; y = (1 - v) * n - 0.5
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    fx = (x - x0)[..., None]; fy = (y - y0)[..., None]
    x0c = np.clip(x0, 0, n - 1); x1c = np.clip(x0 + 1, 0, n - 1); y0c = np.clip(y0, 0, n - 1); y1c = np.clip(y0 + 1, 0, n - 1)
    return (tex[y0c, x0c] * (1 - fx) * (1 - fy) + tex[y0c, x1c] * fx * (1 - fy) + tex[y1c, x0c] * (1 - fx) * fy + tex[y1c, x1c] * fx * fy)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


_UV = {}


def uvmap():
    if not _UV:
        _UV['u'], _UV['v'], _UV['valid'] = card_uv()
    return _UV['u'], _UV['v'], _UV['valid']


def sample_card(rgba):
    """rgba uint8 (n,n,4) -> per-pixel tex rgb (sRGB 0..1), tex alpha (0..1), edge distance, valid."""
    u, v, valid = uvmap()
    t = bilin(rgba.astype(np.float64) / 255, np.clip(u, 0, 1), np.clip(v, 0, 1))
    edge = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v))
    return t[..., :3], t[..., 3], edge, valid


def effective_alpha(ta, edge, valid, ca=1.0, gain=1.0, power=1.0, fade=0.18):
    a = np.power(np.clip(ta * ca * gain, 0, 1), power)
    a = a * (smoothstep(0, fade, edge) if fade > 1e-4 else 1.0)
    return np.where(valid, a, 0.0)


def lumq(rgb8):
    return 0.2126 * rgb8[..., 0] + 0.7152 * rgb8[..., 1] + 0.0722 * rgb8[..., 2]


def render(rgba, sky8, tint, gain, selflight, lit, G=None, A=None, fade=0.18, light=None):
    """predicted 8-bit frame.  G (3,) multiplies tex*tint (fitted light), A (3,) additive; light=(f,fS,A) rebuilds G from lit/selflight."""
    trgb, ta, edge, valid = sample_card(rgba)
    al = effective_alpha(ta, edge, valid, tint[3] if len(tint) > 3 else 1.0, gain, 1.0, fade)
    if light is not None:
        f, fS, A = light
        G = f * (1 - lit + lit * selflight) + fS * lit
    C = s2l(trgb) * s2l(np.array(tint[:3]))[None, None, :] * np.asarray(G)[None, None, :] + np.asarray(A)[None, None, :]
    sky = s2l(sky8 / 255.0)
    out = sky * (1 - al[..., None]) + C * al[..., None]
    return np.round(l2s(out) * 255).astype(np.uint8), al


def stats(frame, sky8):
    d = np.abs(lumq(frame.astype(np.float64)) - lumq(sky8.astype(np.float64)))
    sel = d[d >= 1.5]
    n = sel.size
    if n == 0:
        return dict(N=0, med=0, p99=0, grad=0)
    s = np.sort(sel)
    gx = np.maximum(np.abs(d[1:-1, 2:] - d[1:-1, :-2]), np.abs(d[2:, 1:-1] - d[:-2, 1:-1])) / 2
    mk = np.zeros_like(d, bool)
    inner = (d[1:-1, 1:-1] >= 1.5) | (d[1:-1, 2:] >= 1.5) | (d[1:-1, :-2] >= 1.5) | (d[2:, 1:-1] >= 1.5) | (d[:-2, 1:-1] >= 1.5) | True
    # Unity: skip pixel i when delta[i], delta[i-1], delta[i+1], delta[i-W] are all < 1.5
    c = d[1:-1, 1:-1]; l = d[1:-1, :-2]; r = d[1:-1, 2:]; up = d[:-2, 1:-1]
    skip = (c < 1.5) & (l < 1.5) & (r < 1.5) & (up < 1.5)
    g = gx[~skip]
    gs = np.sort(g)
    return dict(N=int(n), med=float(s[n // 2]), p99=float(s[int(n * 0.99)]), grad=float(gs[int(len(gs) * 0.99)]) if len(gs) else 0.0)


# ---------------------------------------------------------------------------------------------- run table (settings the runtime had in each real run)
RUNS = {
    't2': dict(tint=(0.62, 0.56, 0.56, 1.0), gain=1.0, selflight=0.05, lit=0.6, want=dict(N=18036, med=4.9, p99=14.7, grad=1.03)),
    't4d': dict(tint=(1.0, 0.95, 0.92, 1.0), gain=1.35, selflight=0.35, lit=0.8, want=dict(N=32349, med=8.1, p99=77.1, grad=4.00)),
    't4e': dict(tint=(1.0, 0.95, 0.92, 1.0), gain=1.30, selflight=0.30, lit=0.8, want=dict(N=31369, med=7.4, p99=72.2, grad=3.93)),
}


def load_before():
    return load_z('smoke_before_rgba.raw', (512, 512, 4))


def fit_run(name, rgba):
    r = RUNS[name]
    sky8 = load_rgb(name + '_smoke_card_without.rgb').astype(np.float64)
    with8 = load_rgb(name + '_smoke_card.rgb').astype(np.float64)
    trgb, ta, edge, valid = sample_card(rgba)
    al = effective_alpha(ta, edge, valid, r['tint'][3], r['gain'], 1.0, 0.18)
    T = s2l(np.array(r['tint'][:3]))
    sky = s2l(sky8 / 255); wl = s2l(with8 / 255)
    m = al > 0.04
    G = np.zeros(3); A = np.zeros(3)
    for c in range(3):
        x1 = (al * s2l(trgb[..., c]) * T[c])[m]; x2 = al[m]
        y = (wl[..., c] - sky[..., c] * (1 - al))[m]
        M = np.array([[ (x1 * x1).sum(), (x1 * x2).sum()], [(x1 * x2).sum(), (x2 * x2).sum()]])
        b = np.array([(x1 * y).sum(), (x2 * y).sum()])
        G[c], A[c] = np.linalg.solve(M, b)
    return G, A


def main(argv):
    rgba = load_before()
    res = {}
    for name in RUNS:
        G, A = fit_run(name, rgba)
        r = RUNS[name]
        fr, al = render(rgba, load_rgb(name + '_smoke_card_without.rgb').astype(np.float64), r['tint'], r['gain'], r['selflight'], r['lit'], G=G, A=A)
        st = stats(fr, load_rgb(name + '_smoke_card_without.rgb').astype(np.float64))
        res[name] = dict(G=G.tolist(), A=A.tolist(), model=st, want=r['want'])
        print(name, 'G', np.round(G, 3), 'A', np.round(A, 3), 'model', {k: round(v, 2) for k, v in st.items()}, 'unity', r['want'])
    json.dump(res, open(os.path.join(MODEL, 'fit.json'), 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])


def light_fit():
    """per-channel (f, fS): G = f (1 - lit + lit e) + fS lit   (3 real runs); returns arrays f, fS, residuals."""
    rgba = load_before()
    rows = []; Gs = []
    for name, r in RUNS.items():
        G, A = fit_run(name, rgba)
        rows.append([1 - r['lit'] + r['lit'] * r['selflight'], r['lit']]); Gs.append(G)
    M = np.array(rows); Gs = np.array(Gs)
    sol, *_ = np.linalg.lstsq(M, Gs, rcond=None)
    res = Gs - M @ sol
    return sol[0], sol[1], res


def G_for(lit, selflight, f=None, fS=None):
    if f is None:
        f, fS, _ = light_fit()
    return f * (1 - lit + lit * selflight) + fS * lit


def read_png_np(path):
    """8-bit non-interlaced PNG (colour type 2 or 6) -> uint8 (H,W,C); small numpy decoder (the Look PNGs are small)."""
    import struct, zlib
    d = open(path, 'rb').read(); pos = 8; idat = b''; w = h = ct = 0
    while pos < len(d):
        ln, = struct.unpack('>I', d[pos:pos + 4]); tag = d[pos + 4:pos + 8]; body = d[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if tag == b'IHDR':
            w, h, _, ct = struct.unpack('>IIBB', body[:10])
        elif tag == b'IDAT':
            idat += body
    c = {2: 3, 6: 4}[ct]
    raw = np.frombuffer(zlib.decompress(idat), np.uint8).reshape(h, 1 + w * c)
    out = np.zeros((h, w * c), np.int32); prev = np.zeros(w * c, np.int32)
    for r in range(h):
        ft = raw[r, 0]; x = raw[r, 1:].astype(np.int32)
        if ft == 0:
            cur = x
        elif ft == 2:
            cur = (x + prev) & 255
        else:
            cur = np.zeros(w * c, np.int32)
            for i in range(w * c):
                a_ = cur[i - c] if i >= c else 0; b_ = prev[i]; c_ = prev[i - c] if i >= c else 0
                if ft == 1:
                    pr = a_
                elif ft == 3:
                    pr = (a_ + b_) >> 1
                else:
                    pp = a_ + b_ - c_; pa, pb, pc = abs(pp - a_), abs(pp - b_), abs(pp - c_)
                    pr = a_ if (pa <= pb and pa <= pc) else (b_ if pb <= pc else c_)
                cur[i] = (x[i] + pr) & 255
        out[r] = cur; prev = cur
    return out.astype(np.uint8).reshape(h, w, c)
