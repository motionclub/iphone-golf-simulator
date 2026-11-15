"""Shared rooftop set-up for the trailer takes."""
from lib import *
P, O = "game.Player", "game.Opponent"
PD, OD = P + ".<HeroTennisDriver>", O + ".<HeroTennisDriver>"
HIDE = ["Spectacle overlay", "Predicted landing", "Shot aim target", "Timing cue", "Tennis HUD", "Weather", "Toss meter", "Bounce mark"]
WARM, COOL, PINK, WHITE = (1.0, .86, .72), (.45, .7, 1.0), (1.0, .35, .6), (.86, .92, 1.0)

def hero_rig(who, z, n, key=270, rim=480, kick=170, on=-100000):
    """z = +1 for the player (faces +z), -1 for the rival."""
    return [lit(n + "key", [-1.6 * z, 2.5, 2.6 * z], [0, 1.45, 0], WARM, key, who, range=9, angle=38, shadows=True, on=on, fade=14),
            lit(n + "rim", [1.9 * z, 2.7, -2.6 * z], [0, 1.5, 0], COOL, rim, who, range=9, angle=34, on=on, fade=14),
            lit(n + "kick", [-2.2 * z, 1.3, -1.8 * z], [0, 1.3, 0], PINK, kick, who, range=7, angle=40, on=on, fade=14)]

def banks(near=-100000, far=-100000, power=520, fade=5):
    """Four floodlight banks over the court; `near`/`far` = the frame each half comes on."""
    out = []
    for name, x, z, on in (("nl", -10, -9, near), ("nr", 10, -9, near + 22 if near > -1000 else near), ("fl", -10, 9, far), ("fr", 10, 9, far + 22 if far > -1000 else far)):
        out.append(lit("bank" + name, [x, 13, z * 1.6], [x * .12, 0, z * .62], WHITE, power, range=34, angle=54, inner=34, on=on, fade=fade))
    return out

POST = dict(exposure=0.15, contrast=16, saturation=6, bloom=.45, bloomThreshold=1.1, vignette=.3, shadows=[.92, .98, 1.12, 0], highlights=[1.06, 1.0, .94, 0])
ENV = dict(mainLight=.3, ambient=.16)

def freeze_game(f=-1000):
    """Game logic off: nothing serves, nothing scores; actors are moved and ticked by the take."""
    return [call(f, "static:DreamEnvironment.Current", "SetWeather", "Clear"), call(f, "type:TennisPresentation", "Finish"),
            call(f + 1, "game", "Flow", "PointOver"), call(f + 1, "game", "resetTimer", "1000000"), ev(f + 2, "enable", on="game", s="0")]
def practicals_off(f=-1000): return [ev(f + i, "active", on="find:Court practical", s="0") for i in range(4)]
def tick(who, f0, f1): return dict(f=f0 - 1, until=f1, do="tick", on=who)
def drive(who, f0, f1, a, b, s="linear"): return dict(f=f0, until=f1, do="drive", on=who, v=list(a) + list(b), s=s)
def move(what, f0, f1, a, b, arc=0, s="linear"): return dict(f=f0, until=f1, do="move", on=what, v=list(a) + list(b) + [arc], s=s)
def emote(f, drv, clip): return call(f, drv, "PlayEmote", clip)
def face(f, who, expr, secs=3): return call(f, who, "SetExpression", expr, secs)
def preview(name, frames, cams, events, lights, every=8, warm=0, cells=12, **kw):
    kw["cells"] = cells
    cams = [dict(c, every=0, sub=1) for c in cams]
    """Low-res look at a take: every Nth frame of each camera, one contact sheet per camera."""
    ok = take(name=name, frames=frames, warm=warm, cams=cams, events=events, lights=lights, hide=HIDE, post=kw.pop("post", POST), env=kw.pop("env", ENV), w=640, h=360, ss=2, every=every, quality=88, **{k: v for k, v in kw.items() if k != "cells"})
    if not ok: return False
    import glob
    from PIL import Image, ImageDraw
    n = kw.get("cells", 12); cols = 6; rows = []
    for c in cams:
        fs = sorted(glob.glob(f"{W}/stage/takes/{name}/{c['name']}/f_*.jpg"))
        if len(fs) > n: fs = [fs[round(i * (len(fs) - 1) / (n - 1))] for i in range(n)]
        S = Image.new("RGB", (cols * 320, ((len(fs) + cols - 1) // cols) * 180)); d = ImageDraw.Draw(S)
        for i, p in enumerate(fs):
            S.paste(Image.open(p).resize((320, 180)), ((i % cols) * 320, (i // cols) * 180)); d.text(((i % cols) * 320 + 4, (i // cols) * 180 + 2), c['name'] + " " + os.path.basename(p)[2:7], fill=(255, 255, 0))
        rows.append(S)
    A = Image.new("RGB", (cols * 320, sum(r.height for r in rows))); y = 0
    for r in rows: A.paste(r, (0, y)); y += r.height
    A.save(f"{W}/shots/{name}.jpg", quality=85)
    return True
def final(name, frames, cams, events, lights, warm=0, **kw):
    import shutil; shutil.rmtree(f"{W}/stage/takes/{name}", ignore_errors=True)
    return take(name=name, frames=frames, warm=warm, cams=cams, events=events, lights=lights, hide=HIDE, post=kw.pop("post", POST), env=kw.pop("env", ENV), w=1920, h=1080, ss=1.5, every=kw.pop("every", 1), quality=kw.pop("quality", 95), **kw)

def ranges(cams, R, every=5, sub=3):
    """Final renders: each camera only over its own frames; every/sub = which of the 120 fps frames are kept."""
    out = []
    for c in cams:
        if c["name"] not in R: continue
        a, b = R[c["name"]][:2]; e, sb = (R[c["name"]][2:] + (every, sub))[:2] if len(R[c["name"]]) > 2 else (every, sub)
        d = dict(c); d["from"] = a; d["to"] = b; d["every"] = e; d["sub"] = sb; out.append(d)
    return out

def no_rings(f=-1000):
    """The game redraws its landing / aim rings every frame; a zero width keeps them out of the film."""
    return [call(f, "game.landingRing", "widthMultiplier", "0"), call(f, "game.aimRing", "widthMultiplier", "0")]
