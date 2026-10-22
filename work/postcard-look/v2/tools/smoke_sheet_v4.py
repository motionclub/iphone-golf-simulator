"""smoke_sheet_v4.py <out.png>: Smoke_C before (v3) / after (v4): over red (180,60,30), over grey (90,80,85), the PREDICTED Game-view crop (live LK_SMOKE spec, smoke_model.py), alpha."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, lab, smoke_model as sm
gl = lab.gl
f, fS, _ = sm.light_fit(); sky = sm.load_rgb('t4e_smoke_card_without.rgb').astype(float)
sp = gl.smoke_spec(); G = sm.G_for(sp['lit'], sp['selflight'], f, fS)
after = np.fromfile(os.path.join(lab.ROOT, 'Unity/Assets/Resources/Course/Look/Smoke_C.png'), np.uint8) if False else None
from_png = None
import struct, zlib
def readpng(p):
    d = open(p, 'rb').read(); pos = 8; idat = b''; w = h = ct = 0
    while pos < len(d):
        ln, = struct.unpack('>I', d[pos:pos+4]); tag = d[pos+4:pos+8]; body = d[pos+8:pos+8+ln]; pos += 12 + ln
        if tag == b'IHDR': w, h, _, ct = struct.unpack('>IIBB', body[:10])
        elif tag == b'IDAT': idat += body
    c = {2: 3, 6: 4}[ct]; raw = np.frombuffer(zlib.decompress(idat), np.uint8).reshape(h, 1 + w * c)
    out = np.zeros((h, w * c), np.int32); prev = np.zeros(w * c, np.int32)
    for r in range(h):
        ft = raw[r, 0]; x = raw[r, 1:].astype(np.int32)
        if ft == 0: cur = x
        elif ft == 2: cur = (x + prev) & 255
        else:
            cur = np.zeros(w * c, np.int32)
            for i in range(w * c):
                a_ = cur[i - c] if i >= c else 0; b_ = prev[i]; c_ = prev[i - c] if i >= c else 0
                if ft == 1: pr = a_
                elif ft == 3: pr = (a_ + b_) >> 1
                else:
                    pp = a_ + b_ - c_; pa, pb, pc = abs(pp - a_), abs(pp - b_), abs(pp - c_)
                    pr = a_ if (pa <= pb and pa <= pc) else (b_ if pb <= pc else c_)
                cur[i] = (x[i] + pr) & 255
        out[r] = cur; prev = cur
    return out.astype(np.uint8).reshape(h, w, c)
new = readpng(os.path.join(lab.ROOT, 'Unity/Assets/Resources/Course/Look/Smoke_C.png'))
rows = []
for name, S in (('V3 (BEFORE)', sm.load_before()), ('V4 (INSTALLED)', new)):
    a = S[..., 3].astype(float) / 255; c = S[..., :3].astype(float) / 255
    red = np.array([180, 60, 30]) / 255; gry = np.array([90, 80, 85]) / 255
    t = [lab.label(c * a[..., None] + red * (1 - a[..., None]), name + ' OVER RED'), lab.label(c * a[..., None] + gry * (1 - a[..., None]), 'OVER GREY')]
    fr, al = sm.render(S, sky, sp['tint'], sp['gain'], sp['selflight'], sp['lit'], G=G, A=np.zeros(3), fade=sp['fade']); st = sm.stats(fr, sky)
    crop = fr[420:1020, 100:800].astype(float) / 255
    ys = (np.arange(512) * crop.shape[0] / 512).astype(int); xs = (np.arange(512) * crop.shape[1] / 512).astype(int)
    t.append(lab.label(crop[ys][:, xs], 'PREDICTED GAME med %.1f p99 %.0f' % (st['med'], st['p99'])))
    t.append(lab.label(np.repeat((a / 0.5).clip(0, 1)[..., None], 3, -1), 'ALPHA (X2) MAX %.2f' % a.max()))
    rows.append(lab.hstack(t))
lab.write(sys.argv[1], lab.vstack(rows))
