#!/usr/bin/env python3
"""Trailer edit: cuts the filmed takes (edit.json), speed ramps with real frame blending, grade, widescreen bars,
captions (captions.json), and writes the picture.   edit.py [--half] [--from S] [--to S] [--sheet N] [--out FILE]

edit.json: {"fps":24, "shots":[ {...}, ... ]}   a shot:
  id        name (the score and the sound design look times up by id)
  take,cam  folder under stage/takes/<take>/<cam>/f_#####.jpg (filmed at 120 pictures per second of game time)
  start     first source frame;  dur = seconds on screen
  speed     1 = real time, .2 = five times slower; or [[second, speed], ...] for a ramp
  black     true = a black slug of `dur` seconds instead of a take
  fin/fout  fade from / to black (seconds);  flash = white flash at the cut (seconds);  exp = brightness multiplier
  zoom      [from, to] slow push in the edit (1 = none);  shift [x0,y0,x1,y1] in picture heights
  marks     {"name": seconds into the shot}  -> places the music is built around (see score.py)
  snd       [[seconds into the shot, "sound", gain, pan], ...]  a game sound (tennis/serve_1.wav) or boom / taiko / whoosh / heartbeat
"""
import os, sys, json, math, subprocess, functools, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W = os.path.dirname(os.path.abspath(__file__)); TAKES = os.path.join(W, "stage", "takes")
FF = os.path.expanduser("~/tai-films/ffmpeg")
FONTS = os.path.join(W, "..", "..", "Unity", "Assets", "Resources", "Fonts")
SRC_FPS = 120
LIN = (np.arange(256, dtype=np.float32) / 255.0) ** 2.2

@functools.lru_cache(maxsize=None)
def frames_of(take, cam):
    d = os.path.join(TAKES, take, cam)
    return np.array(sorted(int(f[2:7]) for f in os.listdir(d) if f.startswith("f_") and f.endswith(".jpg")))

@functools.lru_cache(maxsize=48)
def load(take, cam, f, half):
    im = Image.open(os.path.join(TAKES, take, cam, "f_%05d.jpg" % f)).convert("RGB")
    if half: im = im.resize((im.width // 2, im.height // 2), Image.BILINEAR)
    return LIN[np.asarray(im)]

def speed_at(sp, t):
    if not isinstance(sp, list): return float(sp)
    if t <= sp[0][0]: return sp[0][1]
    for (a, va), (b, vb) in zip(sp, sp[1:]):
        if t <= b: return va + (vb - va) * (t - a) / max(1e-6, b - a)
    return sp[-1][1]

def source_frame(shot, fps, n, half, shutter=.55):
    """Picture n of a shot: the average (in linear light) of the filmed frames its shutter was open for."""
    sp = shot.get("speed", 1); pos = shot.get("start", 0)
    for i in range(n): pos += SRC_FPS / fps * speed_at(sp, i / fps)
    span = SRC_FPS / fps * speed_at(sp, n / fps) * shot.get("shutter", shutter)
    have = frames_of(shot["take"], shot["cam"])
    sel = have[(have >= pos - 1e-6) & (have < pos + max(span, 1e-6))]
    if len(sel) == 0: sel = [have[np.argmin(np.abs(have - pos))]]
    if len(sel) > 6: sel = sel[np.linspace(0, len(sel) - 1, 6).round().astype(int)]
    acc = None
    for f in sel:
        a = load(shot["take"], shot["cam"], int(f), half); acc = a.copy() if acc is None else acc + a
    return acc / len(sel)

# ---------------------------------------------------------------- look
def smooth(x): return x * x * (3 - 2 * x)

class Look:
    def __init__(self, w, h):
        self.w, self.h = w, h; self.ph = int(round(w / 2.39 / 2)) * 2; self.y0 = (h - self.ph) // 2
        yy, xx = np.mgrid[0:self.ph, 0:w].astype(np.float32)
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - self.ph / 2) / (self.ph / 2)) ** 2 * .55)
        self.vig = (1 - .32 * np.clip(r - .35, 0, 1) ** 1.6)[..., None]
        self.rng = np.random.default_rng(7)
    def streak(self, lin):
        """Anamorphic streak + soft halation from the highlights (quarter size, cheap)."""
        q = lin[::4, ::4]; lum = q @ np.array([.2126, .7152, .0722], np.float32)
        b = np.clip(lum - .62, 0, None)[..., None] * q
        def box(a, k, axis):
            c = np.cumsum(np.pad(a, [(k, k) if i == axis else (0, 0) for i in range(a.ndim)], mode="edge"), axis=axis, dtype=np.float32)
            n = a.shape[axis]; sl1 = [slice(None)] * a.ndim; sl0 = [slice(None)] * a.ndim
            sl1[axis] = slice(2 * k, 2 * k + n); sl0[axis] = slice(0, n); return (c[tuple(sl1)] - c[tuple(sl0)]) / (2 * k)
        k = max(2, q.shape[1] // 14); s = box(box(b, k, 1), k, 1); s = box(s, 1, 0) * np.array([.35, .6, 1.0], np.float32)
        g = max(2, q.shape[1] // 90); halo = box(box(box(box(b, g, 1), g, 0), g, 1), g, 0) * np.array([1.0, .75, .6], np.float32)
        add = s * 1.1 + halo * .7
        return np.repeat(np.repeat(add, 4, 0), 4, 1)[:lin.shape[0], :lin.shape[1]]
    def finish(self, lin, exp=1.0, fade=1.0, flash=0.0):
        """lin = full 16:9 linear picture -> graded sRGB uint8 with the bars."""
        h, w = self.h, self.w; pic = lin[self.y0:self.y0 + self.ph]
        pic = pic * exp + self.streak(pic) * .9
        pic = pic * self.vig
        # filmic shoulder + a little toe, cool shadows / warm highlights
        x = np.clip(pic, 0, None); x = x / (x + .92) * 1.92 * .98
        lum = (x @ np.array([.2126, .7152, .0722], np.float32))[..., None]
        x = x * (1 + (np.array([-.035, .0, .05], np.float32)) * (1 - np.clip(lum * 3, 0, 1)) + np.array([.03, .005, -.03], np.float32) * np.clip(lum * 1.6 - .5, 0, 1))
        x = lum + (x - lum) * 1.06
        x = np.clip(x, 0, 1) ** (1 / 2.2)
        x = np.clip((x - .5) * 1.07 + .5 - .004, 0, 1)
        x = x + self.rng.normal(0, .011, (self.ph, w, 1)).astype(np.float32) * (1.15 - x.mean(axis=2, keepdims=True))
        if flash > 0: x = x + flash
        x = np.clip(x * fade, 0, 1)
        out = np.zeros((h, w, 3), np.uint8); out[self.y0:self.y0 + self.ph] = (x * 255 + .5).astype(np.uint8); return out

def reframe(lin, z, sx, sy):
    if abs(z - 1) < 1e-4 and abs(sx) < 1e-4 and abs(sy) < 1e-4: return lin
    h, w = lin.shape[:2]; cw, ch = w / z, h / z; x0 = (w - cw) / 2 + sx * h; y0 = (h - ch) / 2 + sy * h
    im = Image.fromarray((np.clip(lin, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)).transform((w, h), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BICUBIC)
    return LIN[np.asarray(im)]

# ---------------------------------------------------------------- captions
def font(name, size):
    for root, _, files in os.walk(FONTS):
        for f in files:
            if f.lower() == name.lower() + ".ttf": return ImageFont.truetype(os.path.join(root, f), size)
    raise SystemExit("font not found: " + name)

def text_layer(text, fnt, tracking, fill=(255, 255, 255), glow=0):
    """One line of text with letter spacing, as an RGBA image (plus an optional glow)."""
    widths = [fnt.getlength(ch) for ch in text]; asc, desc = fnt.getmetrics(); pad = int(fnt.size * .6) + glow * 3
    w = int(sum(widths) + tracking * (len(text) - 1)) + pad * 2; h = asc + desc + pad * 2
    im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im); x = pad
    for ch, cw in zip(text, widths): d.text((x, pad), ch, font=fnt, fill=255); x += cw + tracking
    out = Image.new("RGBA", (w, h), fill + (0,)); out.putalpha(im)
    if glow:
        g = Image.new("RGBA", (w, h), (120, 190, 255, 0)); g.putalpha(im.filter(ImageFilter.GaussianBlur(glow)).point(lambda v: min(255, int(v * 1.6))))
        out = Image.alpha_composite(g, out)
    return out

class Captions:
    def __init__(self, path, w, h, ph, marks=None):
        self.w, self.h, self.ph = w, h, ph; self.k = w / 1920.0
        data = json.load(open(path)); self.items = data["captions"]; self.fontname = data.get("font", "Kanit-ExtraBoldItalic"); self.cache = {}
        marks = marks or {}
        for c in self.items:                       # "at": a mark in edit.json (+ "offset" seconds) keeps a caption glued to its shot when the cut changes
            if c.get("at") in marks: c["start"] = marks[c["at"]] + c.get("offset", 0)
            elif "start" not in c: c["start"] = -1e9
    def layers(self, c):
        key = (c["text"], c["style"])
        if key in self.cache: return self.cache[key]
        k = self.k; st = c["style"]; ls = []
        if st == "title":
            ls.append((text_layer(c["text"], font(self.fontname, int(150 * k)), 6 * k, glow=int(14 * k)), .5, .5))
        elif st == "score":
            ls.append((text_layer(c["text"], font(self.fontname, int(210 * k)), 10 * k, glow=int(10 * k)), .5, .5))
        elif st == "chapter":
            ls.append((text_layer(c["text"], font("Kanit-SemiBold", int(46 * k)), 26 * k), .5, .8))
        elif st == "end":
            lines = c["text"].split("\n")
            ls.append((text_layer(lines[0], font("Kanit-SemiBold", int(44 * k)), 14 * k), .5, .46))
            if len(lines) > 1: ls.append((text_layer(lines[1], font(self.fontname, int(60 * k)), 5 * k, glow=int(6 * k)), .5, .56))
        else:
            ls.append((text_layer(c["text"], font("Kanit-SemiBold", int(40 * k)), 12 * k), .5, .80))
        self.cache[key] = ls; return ls
    def draw(self, frame, t):
        img = None
        for c in self.items:
            u = t - c["start"]; d = c["duration"]
            if u < 0 or u > d: continue
            a = min(1, u / .35) * min(1, (d - u) / .45); a = smooth(max(0, min(1, a)))
            st = c["style"]; grow = 1 + (.035 if st in ("title", "score") else .02) * (u / d)
            if st in ("title", "score"): grow *= 1 + .22 * (1 - min(1, u / .22)) ** 2
            if img is None: img = Image.fromarray(frame).convert("RGBA")
            for layer, cx, cy in self.layers(c):
                L = layer if abs(grow - 1) < 1e-3 else layer.resize((max(1, int(layer.width * grow)), max(1, int(layer.height * grow))), Image.BICUBIC)
                if a < 1: L = L.copy(); L.putalpha(L.getchannel("A").point(lambda v: int(v * a)))
                y0 = (self.h - self.ph) // 2
                img.alpha_composite(L, (int(self.w * cx - L.width / 2), int(y0 + self.ph * cy - L.height / 2)))
                if st == "chapter" and layer is self.layers(c)[0][0]:
                    dr = ImageDraw.Draw(img); lw = int(L.width * .32 * min(1, u / .6)); yy = int(y0 + self.ph * cy + L.height * .32)
                    dr.line([(self.w // 2 - lw, yy), (self.w // 2 + lw, yy)], fill=(255, 255, 255, int(200 * a)), width=max(1, int(2 * self.k)))
        return frame if img is None else np.asarray(img.convert("RGB"))

# ---------------------------------------------------------------- run
def timeline(edl):
    t = 0; out = []
    for s in edl["shots"]:
        out.append((t, s)); t += s["dur"]
    return out, t

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--half", action="store_true"); ap.add_argument("--from", dest="a", type=float, default=0); ap.add_argument("--to", dest="b", type=float, default=1e9)
    ap.add_argument("--sheet", type=int, default=0); ap.add_argument("--out", default=None); ap.add_argument("--edl", default=os.path.join(W, "edit.json")); ap.add_argument("--audio", default=None); ap.add_argument("--timeline", action="store_true")
    a = ap.parse_args()
    edl = json.load(open(a.edl)); fps = edl.get("fps", 24); tl, total = timeline(edl)
    w, h = (960, 540) if a.half else (1920, 1080); look = Look(w, h)
    t0, t1 = max(0, a.a), min(total, a.b); n0, n1 = int(round(t0 * fps)), int(round(t1 * fps))
    marks = {}; snd = []
    for t, s in tl:
        for k, off in (s.get("marks") or {}).items(): marks[k] = round(t + off, 4)
        for e in s.get("snd") or []: snd.append([round(t + e[0], 4)] + list(e[1:]))
    json.dump({"total": total, "fps": fps, "marks": marks, "snd": snd, "shots": [{"id": s.get("id", ""), "t": round(t, 4), "dur": s["dur"]} for t, s in tl]}, open(os.path.join(W, "timeline.json"), "w"), indent=1)
    if a.timeline: print("timeline.json  %.2f s" % total); return
    caps = Captions(os.path.join(W, "captions.json"), w, h, look.ph, marks)
    if a.sheet:
        picks = [n0 + round(i * (n1 - 1 - n0) / max(1, a.sheet - 1)) for i in range(a.sheet)]; cells = []
    else:
        out = a.out or os.path.join(W, "trailer_picture.mp4")
        cmd = [FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-"]
        if a.audio: cmd += ["-ss", str(t0), "-i", a.audio, "-c:a", "aac", "-b:a", "256k", "-shortest"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18" if not a.half else "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in (picks if a.sheet else range(n0, n1)):
        t = n / fps
        i = max(j for j, (ts, _) in enumerate(tl) if ts <= t + 1e-6); ts, s = tl[i]; u = t - ts; k = int(round(u * fps))
        if s.get("black"): lin = np.zeros((h, w, 3), np.float32)
        else:
            lin = source_frame(s, fps, k, a.half)
            if lin.shape[0] != h: lin = LIN[np.asarray(Image.fromarray((lin ** (1 / 2.2) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR))]
            z = s.get("zoom"); sh = s.get("shift"); p = u / max(1e-6, s["dur"])
            if z or sh: lin = reframe(lin, (z[0] + (z[1] - z[0]) * p) if z else 1, (sh[0] + (sh[2] - sh[0]) * p) if sh else 0, (sh[1] + (sh[3] - sh[1]) * p) if sh else 0)
        fade = 1.0
        if s.get("fin"): fade *= smooth(min(1, u / s["fin"]))
        if s.get("fout"): fade *= smooth(min(1, max(0, (s["dur"] - u) / s["fout"])))
        flash = max(0, 1 - u / s["flash"]) ** 2 * .55 if s.get("flash") else 0
        frame = look.finish(lin, s.get("exp", 1.0), fade, flash); frame = caps.draw(frame, t)
        if a.sheet:
            im = Image.fromarray(frame).resize((480, 270)); ImageDraw.Draw(im).text((4, 2), "%.2fs %s" % (t, s.get("id", "")), fill=(255, 255, 0)); cells.append(im)
        else:
            ff.stdin.write(frame.tobytes())
            if (n - n0) % 48 == 0: print("%.1f / %.1f s" % (t, t1), flush=True)
    if a.sheet:
        cols = 4; S = Image.new("RGB", (cols * 480, ((len(cells) + cols - 1) // cols) * 270))
        for j, im in enumerate(cells): S.paste(im, ((j % cols) * 480, (j // cols) * 270))
        o = a.out or os.path.join(W, "shots", "edit_sheet.jpg"); S.save(o, quality=88); print(o)
    else:
        ff.stdin.close(); ff.wait(); print(out, "%.1f s" % (t1 - t0))

if __name__ == "__main__": main()
