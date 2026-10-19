"""python3 tools/nose_off.py <out.jpg> <label=params.json|-> ... : offline nose views (front, 3/4 -40, profile 90, below) of the current
male head (source_male_1017 + s14 sculpt delta, warp = s14 + overrides). Rows per state, ref row first."""
import sys, json, types; sys.modules.setdefault('bpy', types.ModuleType('bpy'))
MF = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-face-body'
sys.path.insert(0, MF + '/tools'); sys.path.insert(0, __file__.rsplit('/', 1)[0])
import os; HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else None; ARGS = [os.path.abspath(a.split('=')[1]) if a.split('=')[1] != '-' else '-' for a in sys.argv[2:]]; os.chdir(MF)
import numpy as np, off, render_off as RO
from PIL import Image, ImageDraw
import nose_model, nose2
h = off.Head(); base = json.load(open('eval/s14.json'))['warp']; delta = np.load('eval/s14_delta.npy')
def head(over):
    if over.get('model') == 2:
        P = dict(off.DEFAULT); P.update(base)
        co = h.base + delta; f = h.to_face(co); x, y, z, live = nose_model.warp_face(f[:, 0], f[:, 1], f[:, 2], P)
        X, Y, Z = x * 1000, y * 1000, z * 1000
        G10 = h.U(np.stack([x, y, z], 1)) * 1000; Nn = RO.vnormals(G10, h.tri, 1); nz = Nn[:, 2][np.searchsorted(np.arange(len(G10)), h.idx)] if False else Nn[h.idx, 2]
        X2, Z2 = nose2.nose_op(X, Y, Z, over.get('Q', {}), nz)
        out = np.stack([X2 / 1000, y, Z2 / 1000], 1); out[~live] = f[~live]; G = h.U(out) * 1000
        it = over.get('Q', {}).get('relax', 0)
        if it:
            lam = over['Q'].get('relax_w', .5); e = h.edges; nb = len(G)
            zw = nose2.zone_w(G[:, 0], G[:, 1], G[:, 2])
            for _ in range(it):
                acc = np.zeros_like(G); cnt = np.zeros(nb)
                np.add.at(acc, e[:, 0], G[e[:, 1]]); np.add.at(acc, e[:, 1], G[e[:, 0]]); np.add.at(cnt, e[:, 0], 1); np.add.at(cnt, e[:, 1], 1)
                avg = acc / np.maximum(cnt, 1)[:, None]; G = G + (lam * zw)[:, None] * (avg - G)
        pp = over.get('Q', {}).get('phil_relax', 0)
        if pp:
            e = h.edges; nb = len(G); ax = np.abs(G[:, 0]); y = G[:, 1]; z = G[:, 2]
            y0, y1 = over['Q'].get('phil_y', (-61., -58.))
            pw = (1 - nose2.ss(12, 18, ax)) * nose2.ss(y0, y1, y) * (1 - nose2.ss(-51, -48, y)) * nose2.ss(20, 30, z)
            for _ in range(pp):
                acc = np.zeros_like(G); cnt = np.zeros(nb)
                np.add.at(acc, e[:, 0], G[e[:, 1]]); np.add.at(acc, e[:, 1], G[e[:, 0]]); np.add.at(cnt, e[:, 0], 1); np.add.at(cnt, e[:, 1], 1)
                avg = acc / np.maximum(cnt, 1)[:, None]; G = G + (.5 * pw)[:, None] * (avg - G)
        lp = over.get('Q', {}).get('low_relax', 0)
        if lp:
            e = h.edges; nb = len(G); ax = np.abs(G[:, 0]); y = G[:, 1]; z = G[:, 2]
            lw = (1 - nose2.ss(42, 55, ax)) * nose2.ss(-128, -118, y) * (1 - nose2.ss(-62, -56, y)) * nose2.ss(-20, 0, z) * over['Q'].get('low_w', 1.)
            for _ in range(lp):
                acc = np.zeros_like(G); cnt = np.zeros(nb)
                np.add.at(acc, e[:, 0], G[e[:, 1]]); np.add.at(acc, e[:, 1], G[e[:, 0]]); np.add.at(cnt, e[:, 0], 1); np.add.at(cnt, e[:, 1], 1)
                avg = acc / np.maximum(cnt, 1)[:, None]; G = G + (.5 * lw)[:, None] * (avg - G)
        jp = over.get('Q', {}).get('jaw_relax', 0)
        if jp:
            e = h.edges; nb = len(G); ax = np.abs(G[:, 0]); y = G[:, 1]; z = G[:, 2]
            jw = (1 - nose2.ss(55, 70, ax)) * nose2.ss(-150, -140, y) * (1 - nose2.ss(-112, -104, y)) * nose2.ss(-60, -40, z)
            for _ in range(jp):
                acc = np.zeros_like(G); cnt = np.zeros(nb)
                np.add.at(acc, e[:, 0], G[e[:, 1]]); np.add.at(acc, e[:, 1], G[e[:, 0]]); np.add.at(cnt, e[:, 0], 1); np.add.at(cnt, e[:, 1], 1)
                avg = acc / np.maximum(cnt, 1)[:, None]; G = G + (.5 * jw)[:, None] * (avg - G)
        if over.get('Q', {}).get('lips'):
            G = G.copy(); G[:, 2] = nose2.lips_op(G[:, 0], G[:, 1], G[:, 2], over['Q']['lips'] if isinstance(over['Q']['lips'], dict) else None)
        sp = over.get('Q', {}).get('side_relax', 0)
        if sp:
            e = h.edges; nb = len(G); ax = np.abs(G[:, 0]); y = G[:, 1]
            sw = nose2.ss(4, 7, ax) * (1 - nose2.ss(17, 23, ax)) * nose2.ss(-48, -42, y) * (1 - nose2.ss(-10, -4, y)) * nose2.zone_w(G[:, 0], G[:, 1], G[:, 2])
            for _ in range(sp):
                acc = np.zeros_like(G); cnt = np.zeros(nb)
                np.add.at(acc, e[:, 0], G[e[:, 1]]); np.add.at(acc, e[:, 1], G[e[:, 0]]); np.add.at(cnt, e[:, 0], 1); np.add.at(cnt, e[:, 1], 1)
                avg = acc / np.maximum(cnt, 1)[:, None]; G = G + (.5 * sw)[:, None] * (avg - G)
        return G
    P = dict(off.DEFAULT); P.update(base); P.update(over)
    co = h.base + delta
    f = h.to_face(co); x, y, z, live = nose_model.warp_face(f[:, 0], f[:, 1], f[:, 2], P)
    out = np.stack([x, y, z], 1); out[~live] = f[~live]
    return h.U(out) * 1000
VIEWS = [(0, 0), (-40, 0), (-90, 0), (0, 25)]
def views(G, res=360, half=42):
    keep = G[h.tri][:, :, 1].min(1) > -175
    ims = []
    for yaw, el in VIEWS:
        g = G
        if el:  # tilt: rotate about x so the camera looks up from below
            a = np.radians(el); R = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]]); g = (G - [0, -40, 0]) @ R.T + [0, -40, 0]
        im = RO.render(g, h.tri, yaw, keep=keep, res=res, half=half, centre=(0, -36, 30))[0]
        ims.append(Image.fromarray(im))
    return ims
if __name__ == '__main__':
    rows = []
    R17 = Image.open(HERE + '/../../ArtDir/style/alive/male-reference-pack-2026-10-17/sheets/17-face-detail-neutral.png').convert('RGB')
    S07 = Image.open(HERE + '/../../ArtDir/style/alive/male-reference-pack-2026-10-17/sheets/07-head-skin-neutral.png').convert('RGB')
    mmpx = .692; hp = 42 / mmpx
    def rc(img, cx, cy, h=hp): return img.crop((int(cx - h), int(cy - h), int(cx + h), int(cy + h))).resize((360, 360), Image.LANCZOS)
    ref = [rc(R17, 355, 316 + 36 / mmpx), rc(S07, 905, 352, 60), rc(R17, 1555 - 20 / mmpx, 316 + 36 / mmpx), Image.new('RGB', (360, 360), 'white')]
    row = Image.new('RGB', (1440, 360), 'white'); [row.paste(im, (360 * i, 0)) for i, im in enumerate(ref)]
    ImageDraw.Draw(row).text((6, 6), 'REF 17 / 07(3/4, approx scale) / 17 profile', fill=(0, 0, 0)); rows.append(row)
    for spec, pj in zip(sys.argv[2:], ARGS):
        label = spec.split('=')[0]
        over = json.load(open(pj)) if pj != '-' else {}
        ims = views(head(over)); row = Image.new('RGB', (360 * len(ims), 360), 'white')
        for i, im in enumerate(ims): row.paste(im, (360 * i, 0))
        ImageDraw.Draw(row).text((6, 6), label, fill=(0, 0, 0)); rows.append(row)
    out = Image.new('RGB', (rows[0].width, 360 * len(rows))); [out.paste(r, (0, 360 * i)) for i, r in enumerate(rows)]
    out.save(OUT, quality=90)
