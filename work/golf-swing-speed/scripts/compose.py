#!/usr/bin/env python3
"""compose.py <before_root> <after_root> <out.mp4> <tag> [tag2 ...]
Before | after film of GolfSwingSpeedFilm takes: per take the TV game camera on top and the face-on side camera below, synced on the
phone reaching the ball (motion takes) or the ball leaving (others). Real speed, then the same window at 0.25x. A strip under each column
shows the phone timeline: where the phone is (top / ball) and when the ball leaves.
"""
import os, sys, csv, math, subprocess
from PIL import Image, ImageDraw, ImageFont

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENC = os.path.join(W, '..', 'emotes', 'scripts', 'enc')
B = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'; R = '/System/Library/Fonts/Supplemental/Arial.ttf'
fb, fm, fs = ImageFont.truetype(B, 30), ImageFont.truetype(B, 22), ImageFont.truetype(R, 19)
CW, GH, SH = 800, 450, 560          # column width, game panel height, side panel height
HEAD, FOOT = 46, 64

def rows(root, tag): return list(csv.DictReader(open(f'{root}/{tag}/trace.csv')))
def events(root, tag): return [l.split() for l in open(f'{root}/{tag}/events.txt') if l.strip()]

def anchor(root, tag):
    r = rows(root, tag)
    if r[0]['phoneAngle']:
        kd = next(i for i, x in enumerate(r) if x['stage'] == 'downswing')
        return next(i for i in range(kd, len(r)) if float(r[i]['phoneAngle']) <= 0), r
    ev = events(root, tag)
    return next(int(e[0]) for e in ev if 'ball' in e and 'moves' in e), r

def marks(root, tag, r):
    ev = events(root, tag)
    m = {}
    ball = next((int(e[0]) for e in ev if 'ball' in e and 'moves' in e), None)
    if ball is not None: m['ball'] = ball
    if r[0]['phoneAngle']:
        kd = next(i for i, x in enumerate(r) if x['stage'] == 'downswing')
        m['phone top'] = kd
        m['phone at ball'] = next(i for i in range(kd, len(r)) if float(r[i]['phoneAngle']) <= 0)
    return m

def panel(root, tag, view, k, n):
    k = max(0, min(n - 1, k))
    p = f'{root}/{tag}/{view}_{k:05d}.jpg'
    if not os.path.exists(p): return Image.new('RGB', (CW, GH if view == 'game' else SH), (30, 30, 30))
    im = Image.open(p).convert('RGB')
    if view == 'game': return im.resize((CW, GH))
    w, h = im.size   # 720 x 960 portrait: the body sits in the middle band
    band = im.crop((0, int(h * .14), w, int(h * .14) + int(w * SH / CW)))
    return band.resize((CW, SH))

def column(root, tag, k, n, label, colour, m, r):
    col = Image.new('RGB', (CW, HEAD + GH + SH + FOOT), (18, 18, 22))
    d = ImageDraw.Draw(col)
    d.rectangle((0, 0, CW, HEAD), fill=colour); d.text((14, 8), label, font=fb, fill='white')
    col.paste(panel(root, tag, 'game', k, n), (0, HEAD)); col.paste(panel(root, tag, 'faceon', k, n), (0, HEAD + GH))
    y = HEAD + GH + SH + 8
    kk = max(0, min(n - 1, k))
    stage = r[kk]['stage']; ph = r[kk]['gvPhase']
    d.text((14, y), f'phone: {stage}', font=fm, fill='white')
    x = 300
    for name, f in sorted(m.items(), key=lambda kv: kv[1]):
        on = kk >= f
        d.text((x, y), name + (' ✓' if on else ''), font=fs, fill=(255, 210, 90) if on else (110, 110, 110)); x += 170
    d.text((14, y + 30), f'frame {kk}   clip t {float(r[kk]["clipTime"]):.3f}   golfer phase {ph}', font=fs, fill=(170, 170, 180))
    return col

def main():
    broot, aroot, out = sys.argv[1:4]; tags = sys.argv[4:]
    frames = []; tmp = out + '.frames'; os.makedirs(tmp, exist_ok=True)
    idx = 0
    for tag in tags:
        a0, ra = anchor(aroot, tag); b0, rb = anchor(broot, tag)
        ma, mb = marks(aroot, tag, ra), marks(broot, tag, rb)
        pre, post = min(a0, b0, 100), min(len(ra) - a0, len(rb) - b0, 75)
        seq = list(range(-pre, post)) + [None] * 20 + [x for x in range(-40, 50) for _ in range(4)]   # real, pause, then 0.25x
        for o in seq:
            img = Image.new('RGB', (CW * 2 + 10, HEAD + GH + SH + FOOT + 44), (8, 8, 10))
            d = ImageDraw.Draw(img)
            if o is None:
                d.text((20, 10), f'{tag}  -  next: the same swing at quarter speed', font=fm, fill='white')
                img.save(f'{tmp}/{idx:06d}.jpg', quality=88); frames.append(f'{tmp}/{idx:06d}.jpg'); idx += 1; continue
            d.text((20, 10), f'{tag}   t = {o / 60:+.3f} s from the phone reaching the ball' if ra[0]['phoneAngle'] else f'{tag}   t = {o / 60:+.3f} s from the ball leaving', font=fm, fill='white')
            img.paste(column(broot, tag, b0 + o, len(rb), 'BEFORE (current game)', (150, 60, 60), mb, rb), (0, 44))
            img.paste(column(aroot, tag, a0 + o, len(ra), 'AFTER', (24, 120, 200), ma, ra), (CW + 10, 44))
            p = f'{tmp}/{idx:06d}.jpg'; img.save(p, quality=88); frames.append(p); idx += 1
    w, h = Image.open(frames[0]).size
    subprocess.run([ENC, out, '60', str(w), str(h)] + frames, check=True, stdout=subprocess.DEVNULL)
    for p in frames: os.remove(p)
    os.rmdir(tmp)
    print(out, len(frames), 'frames')

if __name__ == '__main__':
    main()
