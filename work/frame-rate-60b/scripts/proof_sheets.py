"""FRAME_RATE_60B proof sheets (PIL only).
  steps.jpg   per-frame acceleration of tracked movers, before vs after: 30 Hz motion shows as a comb (every other bar ~0)
  res1080.jpg the five 1920x1080 frames with their measured median fps
    python3 proof_sheets.py <work dir>"""
import sys, os, json, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont
W = sys.argv[1]
def font(s):
    for f in ("/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"):
        try: return ImageFont.truetype(f, s)
        except Exception: pass
    return ImageFont.load_default()
F, FS, FB = font(22), font(16), font(30)
def load(path):
    out = {}
    for line in open(path):
        k, v = line.rstrip("\n").split("\t"); out[k] = np.array([[float(x) for x in p.split(",")] for p in v.split(";") if p])
    return out
def window(P, n=90):
    v = np.linalg.norm(np.diff(P, axis=0), axis=1)
    a = np.linalg.norm(P[2:] - 2 * P[1:-1] + P[:-2], axis=1)
    # the busiest stretch: most travel in n frames, no cut (travel jump > 6x median)
    med = np.median(v[v > 1e-6]) if (v > 1e-6).any() else 1
    ok = np.maximum(v[1:], v[:-1]) < 6 * med
    a = np.where(ok, a, np.nan)
    best, at = -1, 0
    for s in range(0, max(1, len(a) - n)):
        t = np.nansum(v[s:s + n])
        if t > best: best, at = t, s
    return a[at:at + n]
def panel(d, x, y, w, h, a, title, colour):
    d.rectangle([x, y, x + w, y + h], outline=(70, 70, 70)); d.text((x + 8, y + 6), title, font=FS, fill=(230, 230, 230))
    if a is None or not np.isfinite(a).any(): d.text((x + 8, y + h / 2), "no motion in this capture", font=FS, fill=(160, 160, 160)); return
    top = np.nanpercentile(a, 98) or 1; bw = w / len(a)
    for i, val in enumerate(a):
        if not np.isfinite(val): continue
        bh = min(1, val / top) * (h - 36)
        d.rectangle([x + i * bw + 1, y + h - bh - 2, x + (i + 1) * bw - 1, y + h - 2], fill=colour)
rows = [("golf_intro", "hand_r", "Golf intro / idle: right hand"), ("golf_hole12_intro", "head", "Golf tee (hole 12): head"), ("tennis_intro", "hand_r", "Tennis intro: hand (ReadyIdle, chat 4 candidate)"),
        ("tennis_intro", "racket", "Tennis intro: racket"), ("tennis_rally", "racket", "Tennis rally: racket"), ("plaza", "hand_r", "Plaza walk: hand")]
ns = {}; exec(open(os.path.join(W, "scripts/no_step.py")).read().replace("\nmain()\n", "\n"), ns)
img = Image.new("RGB", (1800, 120 + len(rows) * 190 + 210), (24, 24, 26)); d = ImageDraw.Draw(img)
d.text((24, 18), "NO_STEP: per-frame acceleration at a fixed 60 fps clock (90 busiest frames). A comb (every other bar ~0) = moves in straight lines between 1/30 s keys.", font=F, fill=(240, 240, 240))
d.text((24, 52), "left = before (the game as it was), right = after (60 Hz clips, smooth tracks). Number = parity ratio (smooth ~1; 30 Hz >> 2.5).", font=FS, fill=(190, 190, 190))
for r, (scene, key, title) in enumerate(rows):
    y = 100 + r * 190
    for c, mode in enumerate(("before", "after")):
        f = os.path.join(W, "proof", mode, f"tracks_{scene}.tsv")
        
        P = load(f).get(key) if os.path.exists(f) else None
        res = ns["analyse"](P) if P is not None else None
        tag = f"{title} - {mode}" + (f"   parity {res['parity_ratio']}  dup {res['duplicate_share']:.3f}" if res else "")
        bad = res and not res["passed"]
        panel(d, 24 + c * 885, y, 860, 175, window(P) if P is not None else None, tag, (220, 90, 80) if bad else (90, 190, 120))
# hole 12 signature track (from the file, see hole12_track_check.py)
y = 100 + len(rows) * 190
sj = json.load(open(os.path.join(W, "../../Unity/Assets/Resources/Course/hole_12_shot.json"))); n = sj["frames"]
P = np.array(sj["cam"]).reshape(-1, 10)[:n, :3]; f = np.arange(0, (n - 1) * 2 + 1) / 2.0
i = np.clip(np.floor(f).astype(int), 0, n - 1); j = np.minimum(i + 1, n - 1); u = (f - i)[:, None]; lin = P[i] * (1 - u) + P[j] * u
g = lambda k: P[np.clip(k, 0, n - 1)]; p0, p1, p2, p3 = g(i - 1), g(i), g(i + 1), g(i + 2)
cr = .5 * (2 * p1 + (p2 - p0) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u**2 + (3 * p1 - p0 - 3 * p2 + p3) * u**3)
for c, (Q, mode) in enumerate(((lin, "before"), (cr, "after"))):
    res = ns["analyse"](Q)
    panel(d, 24 + c * 885, y, 860, 175, window(Q), f"Golf hole 12 signature shot: chase camera - {mode}   parity {res['parity_ratio']:.3g}", (220, 90, 80) if not res["passed"] else (90, 190, 120))
img.save(os.path.join(W, "proof", "steps.jpg"), quality=88)
# res1080 grid
rt = [json.loads(l) for l in open(os.path.join(W, "proof/runtime/runtime.jsonl"))]
shots = [(r, os.path.join(W, "proof/runtime/res1080", r["scene"] + ".png")) for r in rt]
g = Image.new("RGB", (3 * 640 + 40, 2 * 400 + 90), (24, 24, 26)); d = ImageDraw.Draw(g)
d.text((20, 16), "RES_1080 + RUNTIME (Editor, Game view fixed at 1920x1080, muted): every frame below is a 1920x1080 capture of the scene as drawn", font=F, fill=(240, 240, 240))
for k, (r, p) in enumerate(shots):
    if not os.path.exists(p): continue
    im = Image.open(p); size = im.size; im = im.convert("RGB").resize((620, 349))
    x, y = 20 + (k % 3) * 640, 60 + (k // 3) * 400
    g.paste(im, (x, y)); d.text((x, y + 354), f"{r['scene']}: {size[0]}x{size[1]}  median {r['medianFps']} fps  p05 {r['p05Fps']}  30-fps slots {r['share30fpsSlot']:.0%}", font=FS, fill=(230, 230, 230))
g.save(os.path.join(W, "proof", "res1080.jpg"), quality=88)
print("sheets written")
