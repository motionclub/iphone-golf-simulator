from lib import *
import film, sys
mode = sys.argv[1] if len(sys.argv) > 1 else "p"
G = "game"; BV = "game.ballView"; F = "find:Bowler Female"; M = "find:Bowler Male"
BHIDE = ["BowlingHud", "Club wipe"]
N = 2620; T2 = 1720        # T2: his delivery is queued here (after her strike, its replay and the sweep)
send(dict(op="scene", scene="Bowling"), quiet=True)       # a fresh alley: the same delivery then gives the same pins every time
PINK, CYAN, WARM = (1.0, .3, .75), (.3, .85, 1.0), film.WARM
def rig(who, n):   # bowlers face +z (down the lane)
    return [lit(n + "key", [-1.5, 2.3, 2.8], [0, 1.4, 0], WARM, 200, who, range=9, angle=40, shadows=True), lit(n + "rim", [1.8, 2.6, -2.4], [0, 1.4, 0], CYAN, 420, who, range=9, angle=36), lit(n + "kick", [-2.0, 1.3, -1.8], [0, 1.2, 0], PINK, 260, who, range=8, angle=40)]
R = lambda a, b: {"from": a, "to": b}
cams = [
 cam("wide", [key(-240, [3.2, 1.5, -7.5], [0, 1.0, 4], 34), key(300, [2.4, 1.4, -6.5], [0, 1.0, 4], 34)], aperture=4, focal=40, focusAnchor=F, **R(-240, 300)),
 cam("f_low", [key(0, [-1.8, .28, -.2], [0, .9, 0], 34)], "world", F, aperture=2.8, focal=50, lookSmooth=8, focusAnchor=F, **R(-240, 200)),
 cam("f_back", [key(0, [-.55, 1.45, -3.0], [0, .9, 9], 36)], F, F, aperture=4, focal=40, posSmooth=10, lookSmooth=10, focusAnchor=F, **R(-240, 300)),
 cam("release", [key(0, [.75, .1, 1.0], [0, .1, 0], 30)], "world", BV, aperture=2.8, focal=50, lookSmooth=3, focusAnchor=BV, **R(0, 200)),
 cam("chase", [key(0, [0, .2, -1.15], [0, .05, 4], 42)], BV, BV, aperture=5.6, focal=28, posSmooth=3, lookSmooth=3, **R(50, 330)),
 cam("pinsfront", [key(250, [.38, .12, 16.2], [0, .2, 18.5], 36), key(640, [.34, .14, 16.5], [0, .2, 18.5], 36)], aperture=4, focal=35, **R(250, 640)),
 cam("pinstop", [key(250, [1.15, 1.0, 17.0], [0, .12, 18.7], 34)], aperture=4, focal=50, **R(250, 640)),
 cam("f_react", [key(0, [1.0, 1.25, 3.0], [0, .02, 0], 20)], "world", F + ":Head", aperture=2.4, focal=85, lookSmooth=8, focusAnchor=F + ":Head", **R(780, 1046)),
 cam("f_reactwide", [key(0, [-1.4, .5, 3.6], [0, 1.0, 0], 34)], "world", F, aperture=2.8, focal=50, lookSmooth=10, focusAnchor=F, **R(780, 1046)),
 cam("m_watch", [key(0, [1.2, .1, 2.2], [0, .02, 0], 22)], M + ":Head", M + ":Head", aperture=2.4, focal=85, posSmooth=14, lookSmooth=10, every=2, **R(-240, 1046)),
 cam("m_step", [key(0, [2.6, 1.3, 1.5], [0, 1.1, 0], 34)], "world", M, aperture=2.8, focal=50, lookSmooth=10, focusAnchor=M, every=2, **R(1526, 1900)),
 cam("m_face", [key(0, [.9, 1.3, 2.6], [0, .02, 0], 18)], "world", M + ":Head", aperture=2.0, focal=100, lookSmooth=8, focusAnchor=M + ":Head", **R(1900, 2260)),
 cam("m_low", [key(0, [-1.8, .28, -.2], [0, .9, 0], 34)], "world", M, aperture=2.8, focal=50, lookSmooth=8, focusAnchor=M, **R(1930, 2330)),
 cam("m_back", [key(0, [-.55, 1.45, -3.0], [0, .9, 9], 36)], M, M, aperture=4, focal=40, posSmooth=10, lookSmooth=10, focusAnchor=M, **R(1930, 2400)),
 cam("release2", [key(0, [.75, .1, 1.0], [0, .1, 0], 30)], "world", BV, aperture=2.8, focal=50, lookSmooth=3, focusAnchor=BV, **R(2140, 2330)),
 cam("chase2", [key(0, [0, .2, -1.15], [0, .05, 4], 42)], BV, BV, aperture=5.6, focal=28, posSmooth=3, lookSmooth=3, **R(2190, 2490)),
 cam("f_watch", [key(0, [1.2, .1, 2.2], [0, .02, 0], 22)], F + ":Head", F + ":Head", aperture=2.4, focal=85, posSmooth=14, lookSmooth=10, every=2, **R(1900, N)),
 cam("pinsfront2", [key(2380, [.38, .12, 16.2], [0, .2, 18.5], 36), key(2520, [.34, .14, 16.5], [0, .2, 18.5], 36)], aperture=4, focal=35, **R(2380, 2540)),
]
evs = [ev(-400, "gameclock"), call(-399, G, "KeyboardEnabled", "false"), call(-398, "game.Players", "Add", "Rival"), call(-397, "game.PlayerFemale", "Add", "true"), call(-396, "game.PlayerFemale", "Add", "false"),
       call(-395, G, "NewGame", "null"), ev(-394, "seed", v=[1]), call(-300, "game.Autoplay", "Enqueue", "20,8.0,60,0,0"), call(T2, "game.Autoplay", "Enqueue", "17.5,7.8,120,0,0"), call(1900, G, "SkipWalks"),
       ev(-390, "active", on="find:BowlingHud", s="0"), ev(1708, "active", on="find:BowlingHud", s="0"), ev(1902, "active", on="find:BowlingHud", s="0")]
lights = rig(F, "f") + rig(M, "m")
post = dict(exposure=0.1, contrast=14, saturation=6, bloom=.55, bloomThreshold=1.0, vignette=.3, shadows=[.95, .95, 1.1, 0], highlights=[1.05, 1.0, .97, 0])
tr = ["game.Flow", "game.Current", "game.StandingPins", F, M, BV]
if mode == "p":
    cams = [dict(c, every=0, sub=1) for c in cams]
    take(name="b1", frames=N, warm=400, events=evs, cams=cams, lights=lights, hide=BHIDE, post=post, env=dict(mainLight=1, ambient=1), w=640, h=360, ss=2, quality=88, every=40, trace=tr)
else:
    import shutil; shutil.rmtree(f"{W}/stage/takes/b1", ignore_errors=True)
    take(name="b1", frames=N, warm=400, events=evs, cams=cams, lights=lights, hide=BHIDE, post=post, env=dict(mainLight=1, ambient=1), w=1920, h=1080, ss=1.5, quality=92, trace=tr)
rows=[r.split(';') for r in open(W+'/stage/takes/b1/trace.csv').read().splitlines()]
prev=None
for r in rows[1:]:
    k=(r[1],r[2])
    if k!=prev or int(r[0])%300==0: print(r[0], r[1], r[2], r[3], r[4][r[4].find('pos='):][:52], r[5][r[5].find('pos='):][:52]); prev=k
