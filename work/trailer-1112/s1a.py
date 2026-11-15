from film import *
import sys
mode = sys.argv[1] if len(sys.argv) > 1 else "p"
cams = [cam("wide", [key(0, [12.5, 6.0, -25], [0, .5, -3], 30), key(600, [10.5, 5.2, -22.5], [0, .5, -3], 30)], dof=False),
        cam("low", [key(0, [3.4, .28, 1.1], [.2, .45, 0], 30), key(600, [2.9, .28, 2.0], [.2, .45, 0], 30)], P, P, aperture=2.0, focal=85, focusAnchor=PD + ":Head"),
        cam("ump", [key(0, [-4.6, 2.75, -1.6], [-7.45, 2.85, 0], 24), key(600, [-4.7, 2.75, -1.3], [-7.45, 2.85, 0], 24)], aperture=2.0, focal=85)]
evs = freeze_game(-30) + practicals_off(-30) + [ev(-20, "place", on="game.ball", v=[0, -5, 30]), ev(-20, "place", on=P, v=[.4, .035, -11.6]), ev(-20, "place", on=O, v=[1.5, .035, 30]),
    tick(P, -15, 600), tick(O, -15, -10), emote(150, PD, "IntroPushups")]
lights = banks(near=70, far=100000) + hero_rig(PD, 1, "p", on=70) + [lit("ump", [-3.5, 4.5, -2.5], [-7.45, 2.6, 0], WARM, 260, range=9, angle=30, on=70, fade=5), lit("umprim", [-10, 4, 2], [-7.45, 2.8, 0], COOL, 300, range=9, angle=30, on=70, fade=5)]
if mode != "p": cams = ranges(cams, {"wide": (0, 540), "low": (160, 560), "ump": (260, 580)})
(preview if mode == "p" else final)("s1a", 600, cams, evs, lights, warm=30, **(dict(every=20) if mode == "p" else {}))
