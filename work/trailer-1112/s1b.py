from film import *
import sys
mode = sys.argv[1] if len(sys.argv) > 1 else "p"
N = 1100
cams = [cam("wave", [key(0, [1.5, 1.05, 4.6], [0, 1.15, 0], 30), key(520, [1.1, 1.05, 4.1], [0, 1.15, 0], 30)], P, P, aperture=2.0, focal=70, focusAnchor=PD + ":Head", to=540),
        cam("grin", [key(560, [.55, -.03, 1.2], [0, .0, 0], 17), key(N, [.45, -.03, 1.05], [0, .0, 0], 17)], PD + ":Head", PD + ":Head", aperture=1.8, focal=85, lookSmooth=12, posSmooth=12),
        cam("bring", [key(560, [-1.3, 1.0, 3.6], [0, 1.2, 0], 30), key(N, [-1.0, 1.0, 3.2], [0, 1.2, 0], 30)], P, P, aperture=2.0, focal=70, focusAnchor=PD + ":Head")]
evs = freeze_game(-30) + practicals_off(-30) + [ev(-20, "place", on="game.ball", v=[0, -5, 30]), ev(-20, "place", on=P, v=[.4, .035, -11.6]), ev(-20, "place", on=O, v=[.3, .035, 12.3]), tick(P, -15, N), tick(O, -15, N),
    call(-5, PD, "EmoteDuration", "IntroWave"), call(-5, PD, "EmoteDuration", "IntroBringIt"), call(-5, PD, "EmoteDuration", "IntroPushups"),
    emote(40, PD, "IntroWave"), face(40, P, "Happy", 4), emote(620, PD, "IntroBringIt"), face(560, P, "Happy", 5)]
lights = banks() + hero_rig(PD, 1, "p") + hero_rig(OD, -1, "o")
if mode != "p": cams = ranges(cams, {"wave": (20, 360), "grin": (560, 940), "bring": (590, 1040)})
(preview if mode == "p" else final)("s1b", N, cams, evs, lights, warm=30, trace=[PD + ".PlayingClip"], **(dict(every=10, cells=12) if mode == "p" else {}))
