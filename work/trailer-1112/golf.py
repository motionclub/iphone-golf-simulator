"""Shared set-up for the golf takes (hole 21, the island par 3 in the lava)."""
from lib import *
import film
G = "game"; GV = "game.golfer"; B = "game.ball"
GHIDE = ["Golf broadcast", "HUD", "Club wipe", "Green read", "Aim line", "Aim dots", "Landing zone", "Shot result", "Weather", "Big screen"]
HOLE = 21
def setup(f=-200, female=True, club="Iron", at="=game.CurrentHole.Tee"):
    return [ev(f, "enable", on=G, s="1"), ev(f, "active", on=GV, s="1"), call(f, "static:GolferStyle", "Body", "Female" if female else "Male"), call(f + 1, G, "RestyleGolfer"), call(f + 2, G, "JumpToHole", HOLE), call(f + 40, G, "SetWind", "=static:Wind.Calm"),
            call(f + 50, G, "DropBall", at), call(f + 55, G, "SelectClub", club), call(f + 56, G, "InstantReplays", "false"), ev(f + 57, "active", on="find:Golf broadcast", s="0")]
def gtake(name, frames, cams, events, lights=None, final=False, warm=200, **kw):
    post = kw.pop("post", GPOST); env = kw.pop("env", GENV)
    if final:
        import shutil; shutil.rmtree(f"{W}/stage/takes/{name}", ignore_errors=True)
        return take(name=name, frames=frames, warm=warm, cams=cams, events=events, lights=lights or [], hide=GHIDE, post=post, env=env, w=1920, h=1080, ss=1.5, quality=92, **kw)
    cams = [dict(c, every=0, sub=1) for c in cams]
    return take(name=name, frames=frames, warm=warm, cams=cams, events=events, lights=lights or [], hide=GHIDE, post=post, env=env, w=640, h=360, ss=2, quality=88, **kw)
GPOST = dict(exposure=0.1, contrast=14, saturation=8, bloom=.5, bloomThreshold=1.0, vignette=.3, shadows=[.95, .95, 1.1, 0], highlights=[1.08, 1.0, .92, 0])
GENV = dict(mainLight=1.0, ambient=.8)

TEE_Y, PIN = 19.41, (12.0, 26.39, 165.1)
LAVA = (1.0, .5, .2)
def golfer_rig(on=-100000):
    """Golfer faces +x on the tee (the hole runs +z): warm key from the front, lava-orange rim from behind, cool kicker."""
    return [lit("gkey", [2.6, 2.4, -1.6], [0, 1.3, 0], film.WARM, 240, GV, range=9, angle=40, shadows=True, on=on),
            lit("grim", [-2.4, 2.7, 1.9], [0, 1.4, 0], LAVA, 520, GV, range=9, angle=36, on=on),
            lit("gkick", [-1.2, 1.3, -2.6], [0, 1.2, 0], film.COOL, 220, GV, range=8, angle=40, on=on)]
