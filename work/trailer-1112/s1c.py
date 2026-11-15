from film import *
import sys
mode = sys.argv[1] if len(sys.argv) > 1 else "p"; only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
B = "game.ball"; FARON = 900; N = 1150
PP = [.4, .035, -11.6]
cams = [cam("ballfar", [key(0, [-.35, .14, -7.4], [0, .15, 0], 34)], "world", B, aperture=4, focal=40, lookSmooth=6),
        cam("balltele", [key(0, [-.9, .22, -13.5], [0, .25, 0], 9)], "world", B, aperture=4, focal=135, lookSmooth=5, focusAnchor=B),
        cam("ballside", [key(0, [5.5, .25, -1.0], [0, .2, 0], 16)], "world", B, aperture=2.8, focal=100, lookSmooth=4, focusAnchor=B),
        cam("shoe", [key(300, [1.25, .09, 1.15], [.2, .07, .28], 20), key(620, [1.1, .09, 1.25], [.2, .07, .28], 20)], P, P, aperture=2.0, focal=85),
        cam("pface", [key(380, [.5, -.02, 1.15], [0, .02, 0], 17), key(800, [.42, -.02, 1.05], [0, .02, 0], 17)], PD + ":Head", PD + ":Head", aperture=1.8, focal=85, lookSmooth=10, posSmooth=10),
        cam("herlong", [key(560, [-1.1, 1.7, -14.2], [.5, 1.15, 15], 5), key(N, [-1.0, 1.7, -14.0], [.3, 1.15, 12.3], 5)], aperture=2.8, focal=200, focusAnchor=OD + ":Head"),
        cam("herback", [key(820, [.95, .5, 2.9], [0, 1.2, -6], 34), key(N, [.8, .55, 2.5], [0, 1.2, -6], 34)], O, O, aperture=2.8, focal=50, focusAnchor=OD + ":Head"),
        cam("hermid", [key(600, [-.9, .5, -4.4], [0, 1.2, 0], 26), key(N, [-.7, .5, -3.6], [0, 1.25, 0], 26)], O, O, aperture=2.0, focal=85, focusAnchor=OD + ":Head", lookSmooth=8)]
if only: cams = [c for c in cams if c["name"] in only]
NAME = "s1c2" if only else "s1c"
evs = freeze_game(-30) + practicals_off(-30) + [ev(-20, "place", on=P, v=PP + [0]), ev(-20, "place", on=O, v=[1.0, .035, 18.2, 180]), call(-20, B, "localScale", "0.125,0.125,0.125"),
    tick(P, -15, N), tick(O, -15, 429),
    move(B, 0, 40, [2.0, 1.3, 15], [1.3, .098, 8.2], 0, "in"), move(B, 40, 150, [1.3, .098, 8.2], [.85, .098, -2.6], 1.55), move(B, 150, 220, [.85, .098, -2.6], [.72, .098, -6.6], .5),
    move(B, 220, 262, [.72, .098, -6.6], [.68, .098, -8.6], .16), move(B, 262, 500, [.68, .098, -8.6], [.66, .098, -11.22], 0, "out"),
    dict(f=120, until=560, do="call", on=P, m="LookAt", a=["@" + B, "1"]), dict(f=561, until=N, do="call", on=P, m="LookAt", a=["@" + OD + ":Head", "1"]),
    face(560, P, "Surprised", 2.2), face(840, P, "Focus", 4),
    drive(O, 430, 880, [1.0, .035, 18.2], [.3, .035, 12.3]), tick(O, 881, N), face(430, O, "Focus", 9)]
lights = banks(near=-1000, far=FARON) + hero_rig(PD, 1, "p") + [lit("orim", [-1.6, 2.8, 3.2], [0, 1.4, 0], COOL, 520, OD, range=9, angle=34, on=600, fade=180), lit("okick", [2.2, 1.4, 2.2], [0, 1.3, 0], PINK, 150, OD, range=7, angle=40, on=700, fade=150),
    lit("okey", [1.6, 2.5, -2.6], [0, 1.45, 0], WARM, 200, OD, range=9, angle=38, shadows=True, on=FARON, fade=6)]
if mode != "p": cams = ranges(cams, {"ballfar": (0, 340), "balltele": (0, 520), "ballside": (0, 520), "shoe": (340, 620), "pface": (500, 820), "herlong": (590, 1080), "herback": (830, 1149), "hermid": (600, 920)})
(preview if mode == "p" else final)(NAME, N, cams, evs, lights, warm=30, **(dict(every=10, cells=12) if mode == "p" else {}))
