from film import *
import sys
mode = sys.argv[1] if len(sys.argv) > 1 else "p"
B = "game.ball"; N = 520
PS = dict(posSmooth=18, lookSmooth=10)
cams = [
 cam("toss", [key(0, [1.5, .28, 2.1], [0, .22, 0], 30)], P, PD + ":Head", aperture=2.8, focal=50, to=360, lookSmooth=6),
 cam("tossball", [key(0, [.75, .16, 1.5], [0, 0, 0], 38)], P, B, aperture=4, focal=35, to=320, lookSmooth=5, focusAnchor=B),
 cam("tossside", [key(0, [4.2, 1.1, .3], [0, 1.5, 0], 30), key(360, [3.8, 1.1, .9], [0, 1.6, 0], 30)], P, P, aperture=2.8, focal=50, focusAnchor=PD + ":Head", to=360),
 cam("pface", [key(0, [.55, .0, 1.25], [0, .02, 0], 17)], PD + ":Head", PD + ":Head", aperture=1.8, focal=85, lookSmooth=10, posSmooth=10, to=200),
 cam("pback", [key(0, [-.95, 1.95, -3.3], [0, 1.0, 0], 32)], P, O, aperture=4, focal=50, focusAnchor=PD + ":Head", **PS),
 cam("netlow", [key(0, [5.6, .32, .7], [0, 0, 0], 30)], "world", B, aperture=4, focal=50, lookSmooth=4, focusAnchor=B, **{"from": 240}),
 cam("sidelong", [key(0, [16, 1.5, 0], [0, .2, 0], 13)], "world", B, aperture=2.8, focal=135, lookSmooth=7, focusAnchor=B, **{"from": 240}),
 cam("omid", [key(0, [-2.0, .95, -3.9], [0, 1.1, 0], 30)], O, O, aperture=2.0, focal=70, focusAnchor=OD + ":Head", posSmooth=18, lookSmooth=10, **{"from": 200}),
 cam("oback", [key(0, [1.0, 1.85, 3.3], [0, 1.0, 0], 30)], O, P, aperture=4, focal=50, focusAnchor=OD + ":Head", posSmooth=18, lookSmooth=10),
 cam("ump", [key(0, [-4.6, 2.75, -1.5], [-7.45, 2.85, 0], 24)], aperture=2.0, focal=85, every=2),
]
evs = practicals_off(-60) + no_rings(-60) + [call(-60, "static:DreamEnvironment.Current", "SetWeather", "Clear"), ev(-60, "enable", on="game", s="1"), call(-59, "type:TennisPresentation", "Finish"),
       call(-58, "game", "AutoPlay", "true"), call(-58, "game", "ConfigureMatch", "Exhibition", "", "", ""), call(-56, "type:TennisPresentation", "Finish"), call(-55, "game", "AutoPlay", "true"), call(-54, "game", "Refeed")]
lights = banks() + hero_rig(PD, 1, "p") + hero_rig(OD, -1, "o") + [lit("ump", [-3.5, 4.5, -2.5], [-7.45, 2.6, 0], WARM, 260, range=9, angle=30), lit("umprim", [-10, 4, 2], [-7.45, 2.8, 0], COOL, 300, range=9, angle=30)]
tr = ["game.Flow", "game.BallPosition", PD + ".PlayingClip", OD + ".PlayingClip", P + ".Swinging", O + ".Swinging", P, O]
if mode == "p": preview("s2s", N, cams, evs, lights, every=24, warm=60, cells=12, trace=tr)
else: final("s2s", N, cams, evs, lights, warm=60, trace=tr, quality=92)
