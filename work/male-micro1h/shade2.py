"""Analysis-by-synthesis (numpy only): orthographic splat of the sculpted head into any plate panel (front / profile / 3/4), light fitted on the dome
in CAMERA space, predicted Lambert shading vs plate luminance."""
import sys, math
sys.path.insert(0, '.')
import numpy as np
from PIL import Image
import h1lib as H, loft as L, sculpt as S, proxy as PX
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
K = H.K; TOP = H.TOP
plate = Image.open(R + 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('L')
D = np.load('data/proxy_L3.npz', allow_pickle=True); V0 = D['V']; F0 = D['F']
VIEWS = {
    'front': dict(box=(5, 62, 433, 352), az=0.0, kind='front'),
    'left': dict(box=(433, 62, 834, 352), az=90.0, kind='side'),
    'q3L': dict(box=(5, 390, 433, 668), az=41.0, kind='q3', pm=176.5),
    'q3R': dict(box=(433, 390, 834, 668), az=36.0, kind='q3', pm=589.5),
}
FACE = {'front': (145, 120, 305, 300), 'q3L': (130, 440, 315, 620), 'q3R': (520, 440, 740, 620), 'left': (470, 100, 640, 300)}
DOME = {'front': (16, 66, 170, 275), 'q3L': (14, 66, 160, 262), 'q3R': (14, 66, 140, 252), 'left': (16, 70, 130, 270)}      # panel rows/cols (r0,r1,c0,c1) of dome-only pixels


def stage1(P, prm=None, nf=None):
    loft = L.Loft(nf=nf) if nf is not None else L.Loft()
    P0, _, _ = L.remap(P, loft)
    P1, _ = S.apply(P0, np.zeros_like(P0), prm or S.PRM, ('nose', 'orbit', 'brow', 'cheek', 'eye', 'mouth', 'ear'), F=None)
    keep = P[:, 2] < 1.462; P1[keep] = P[keep]
    return P1


def project(P, name):
    v = VIEWS[name]; a = math.radians(v['az'])
    x0, y0, x1, y1 = v['box']
    if v['kind'] == 'front':
        col = 227.6 + P[:, 0] / K; row = 76 + (TOP - P[:, 2]) / K
    elif v['kind'] == 'side':
        col = (x0 + x1) / 2 + (P[:, 1] - float(H.ycol((x0 + x1) / 2))) / (-K) * -1.0
        # y(col) = 0.065 - (712 - col) K  -> col = 712 + (y - 0.065)/K ; the profile faces image-left
        col = 712 + (P[:, 1] - 0.065) / K
        row = 76 + (TOP - P[:, 2]) / K
    else:
        u = P[:, 0] * math.cos(a) + (P[:, 1] + 0.1254) * math.sin(a)
        col = v['pm'] + u / K; row = 397 + (TOP - P[:, 2]) / K
    depth = P[:, 0] * math.sin(a) - P[:, 1] * math.cos(a)           # larger = nearer the camera (camera at (sin a, -cos a))
    camdir = np.array([math.sin(a), -math.cos(a), 0.0])
    return col - x0, row - y0, depth, camdir


def splat(P, N, name):
    v = VIEWS[name]; x0, y0, x1, y1 = v['box']; w = x1 - x0; h = y1 - y0
    col, row, depth, camdir = project(P, name)
    ci = np.round(col).astype(int); ri = np.round(row).astype(int)
    ok = (ci >= 0) & (ci < w) & (ri >= 0) & (ri < h) & ((N @ camdir) > -0.1)
    idx = -np.ones((h, w), int); vi = np.where(ok)[0]
    order = np.argsort(depth[vi])        # nearest last
    flat = ri[vi] * w + ci[vi]
    ix = idx.ravel(); ix[flat[order]] = vi[order]
    Nimg = np.zeros((h, w, 3)); m = idx >= 0; Nimg[m] = N[idx[m]]
    for _ in range(2):
        pad = np.pad(m, 1); cnt = sum(pad[1 + dy:1 + dy + h, 1 + dx:1 + dx + w].astype(int) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
        hole = (~m) & (cnt >= 3)
        if not hole.any(): break
        acc = np.zeros_like(Nimg); padN = np.pad(Nimg, ((1, 1), (1, 1), (0, 0))); padm = np.pad(m, 1)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if (dy, dx) == (0, 0): continue
                acc += padN[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] * padm[1 + dy:1 + dy + h, 1 + dx:1 + dx + w][..., None]
        Nimg[hole] = (acc / (np.linalg.norm(acc, axis=2, keepdims=True) + 1e-12))[hole]; m = m | hole
    return Nimg, m, idx


def cam_basis(name):
    a = math.radians(VIEWS[name]['az'])
    return np.array([math.cos(a), math.sin(a), 0.0]), np.array([0, 0, 1.0]), np.array([math.sin(a), -math.cos(a), 0.0])   # right, up, toward camera


def light_vec(name, az_l, el_l):
    r, u, c = cam_basis(name); a_ = math.radians(az_l); e_ = math.radians(el_l)
    return r * math.sin(a_) * math.cos(e_) + c * math.cos(a_) * math.cos(e_) + u * math.sin(e_)


def fit_light(Nimg, mask, lum, name):
    r0, r1, c0, c1 = DOME[name]
    m = mask[r0:r1, c0:c1]; Ns = Nimg[r0:r1, c0:c1][m]; Ls = lum[r0:r1, c0:c1][m]
    best = None
    for az in np.arange(-80, 81, 4):
        for el in np.arange(-20, 81, 4):
            l = light_vec(name, az, el)
            s = np.clip(Ns @ l, 0, None)
            A = np.stack([np.ones_like(s), s], axis=1)
            sol = np.linalg.lstsq(A, Ls, rcond=None)[0]
            rms = np.sqrt(np.mean((A @ sol - Ls) ** 2))
            if best is None or rms < best[3]: best = (l, sol[0], sol[1], rms, az, el)
    return best


def compare(P1, name, light=None, tag='', up=3, save=True):
    N1 = PX.vertex_normals(P1, F0)
    Nimg, m, _ = splat(P1, N1, name)
    box = VIEWS[name]['box']
    lum = np.asarray(plate.crop(box)).astype(float)
    if light is None:
        b = fit_light(Nimg, m, lum, name); light = b
        print(name, 'light (camera az,el) = (%d,%d)  a %.0f b %.0f  dome rms %.1f' % (b[4], b[5], b[1], b[2], b[3]))
    l, a, b_ = light[0], light[1], light[2]
    pred = a + b_ * np.clip(Nimg @ l, 0, None)
    res = lum - pred
    fx0, fy0, fx1, fy1 = FACE[name]
    sl = (slice(fy0 - box[1], fy1 - box[1]), slice(fx0 - box[0], fx1 - box[0]))
    def g(arr, mask=None):
        im = np.clip(arr, 0, 255).astype(np.uint8)
        im = np.where(mask, im, 40).astype(np.uint8) if mask is not None else im
        return Image.fromarray(im).convert('RGB')
    rr = np.clip(res / 60.0, -1, 1)
    rgb = np.zeros(res.shape + (3,)); rgb[..., 0] = np.where(rr > 0, 255, 255 * (1 + rr)); rgb[..., 1] = 255 * (1 - np.abs(rr)); rgb[..., 2] = np.where(rr < 0, 255, 255 * (1 - rr))
    rgb[~m] = 40
    imgs = [g(lum)] + [g(pred, m)] + [Image.fromarray(rgb.astype(np.uint8))]
    crops = [im.crop((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop)) for im in imgs]
    W, Hh = crops[0].size; sheet = Image.new('RGB', (W * 3 + 20, Hh))
    for i, c in enumerate(crops): sheet.paste(c, (i * (W + 10), 0))
    sheet = sheet.resize((sheet.width * up, sheet.height * up), Image.LANCZOS)
    if save: sheet.save('r/sh2_%s_%s.png' % (tag, name))
    return light, res, m, sheet


if __name__ == '__main__':
    P1 = stage1(V0)
    for n in ('front', 'q3L', 'q3R', 'left'):
        compare(P1, n, tag='base')
