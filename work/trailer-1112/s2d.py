from film import *
import sys
mode = sys.argv[1] if len(sys.argv) > 1 else "p"
B = "game.ball"; N = 640
cams = [
 cam("dfront", [key(0, [3.6, .32, -5.6], [0, .7, 0], 38)], "world", P, aperture=2.8, focal=40, lookSmooth=4, focusAnchor=PD + ":Hips", to=330),
 cam("dside", [key(0, [9.5, .45, -9.6], [0, .6, 0], 17)], "world", P, aperture=2.8, focal=100, lookSmooth=8, focusAnchor=PD + ":Hips", to=330),
 cam("dtip", [key(0, [4.9, .42, -13.1], [2.2, .6, -9.2], 30)], aperture=4, focal=35, focusAnchor=PD + ":Hips", to=260),
 cam("dface", [key(120, [1.0, 1.45, 2.4], [0, .04, 0], 16)], P, PD + ":Head", aperture=2.0, focal=100, posSmooth=14, lookSmooth=10, **{"from": 110}),
 cam("dlow", [key(120, [-1.6, .25, 3.2], [0, .9, 0], 30)], P, P, aperture=2.0, focal=60, posSmooth=14, lookSmooth=10, focusAnchor=PD + ":Head", **{"from": 110}),
 cam("dher", [key(0, [-1.7, .9, -3.6], [0, 1.15, 0], 28)], O, O, aperture=2.0, focal=70, focusAnchor=OD + ":Head", posSmooth=14, lookSmooth=10),
 cam("dherback", [key(0, [.9, 1.75, 3.2], [0, .8, 0], 30)], O, P, aperture=4, focal=50, focusAnchor=OD + ":Head", posSmooth=14, lookSmooth=10, every=2),
 cam("dump", [key(0, [-4.6, 2.75, -1.5], [-7.45, 2.85, 0], 24)], aperture=2.0, focal=85, every=2),
]
evs = practicals_off(-60) + no_rings(-60) + [call(-60, "static:DreamEnvironment.Current", "SetWeather", "Clear"), ev(-60, "enable", on="game", s="1"), call(-59, "type:TennisPresentation", "Finish"),
       call(-178, "game", "AutoPlay", "false"), call(-176, "game", "Refeed"), call(-20, "game", "PrepareLesson"),
       ev(18, "place", on=O, v=[.615, .035, 11.2]), call(20, "game", "InjectBall", "0.615,1.035,10.2", "3.6,3.4,-19"), call(85, "game", "RequestDive"),
       call(196, "game", "resetTimer", "1000000"), emote(196, OD, "EmoteFistPump"), emote(345, PD, "EmoteSlump")]
lights = banks() + hero_rig(PD, 1, "p") + hero_rig(OD, -1, "o") + [lit("ump", [-3.5, 4.5, -2.5], [-7.45, 2.6, 0], WARM, 260, range=9, angle=30), lit("umprim", [-10, 4, 2], [-7.45, 2.8, 0], COOL, 300, range=9, angle=30)]
tr = ["game.Flow", "game.BallPosition", PD + ".PlayingClip", OD + ".PlayingClip", "game.DiveActive", P]
if mode == "p": preview("s2d", N, cams, evs, lights, every=20, warm=180, cells=12, trace=tr)
else: final("s2d", N, cams, evs, lights, warm=180, trace=tr, quality=92)
