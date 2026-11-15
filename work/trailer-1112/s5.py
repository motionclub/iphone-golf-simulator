from film import *
import sys
mode = sys.argv[1] if len(sys.argv) > 1 else "p"
N = 1500
PP, OP = [.5, .035, -1.5], [.3, .035, 1.5]
cams = [
 cam("two", [key(0, [7.5, .9, -.4], [.4, 1.15, 0], 26), key(700, [6.8, .9, .2], [.4, 1.15, 0], 26)], aperture=2.8, focal=70, focusAnchor=PD + ":Head", to=720),
 cam("him", [key(0, [1.1, 1.75, 2.4], [0, 1.45, 0], 22), key(700, [.9, 1.75, 2.2], [0, 1.45, 0], 22)], O, P, aperture=2.0, focal=85, focusAnchor=PD + ":Head", to=720),
 cam("her", [key(0, [-1.0, 1.7, -2.5], [0, 1.4, 0], 22), key(900, [-.8, 1.7, -2.3], [0, 1.4, 0], 22)], P, O, aperture=2.0, focal=85, focusAnchor=OD + ":Head", lookSmooth=10, to=1000),
 cam("away", [key(640, [5.5, 1.3, -12], [0, 1.0, 2], 30), key(N, [4.5, 2.2, -14.5], [0, 1.0, 2], 30)], aperture=4, focal=40, focusAnchor=PD + ":Head", **{"from": 640}),
 cam("top", [key(640, [0, 17, -1.5], [0, 0, -.6], 36), key(N, [0, 24, -1.5], [0, 0, -.6], 36)], dof=False, every=5, **{"from": 640}),
]
evs = freeze_game(-30) + practicals_off(-30) + no_rings(-30) + [ev(-20, "place", on="game.ball", v=[0, -5, 30]), ev(-20, "place", on=P, v=PP + [0]), ev(-20, "place", on=O, v=OP + [180]),
    tick(P, -15, 759), tick(O, -15, 699), face(0, P, "Happy", 12), face(0, O, "Neutral", 3), face(360, O, "Happy", 10),
    emote(120, PD, "IntroBringIt"),
    dict(f=700, until=760, do="yaw", on=O, v=[180, 0]), drive(O, 761, 1500, OP, [.3, .035, 11.8]),
    dict(f=760, until=820, do="yaw", on=P, v=[0, 180]), drive(P, 821, 1500, PP, [.5, .035, -11.5]),
    dict(f=700, until=760, do="tick", on=O), dict(f=760, until=820, do="tick", on=P)]
lights = banks(power=380) + hero_rig(PD, 1, "p") + hero_rig(OD, -1, "o")
tr = [PD + ".PlayingClip", OD + ".PlayingClip", P, O]
cams = [c for c in cams if c["name"] != "two"]
if mode == "p": preview("s5", N, cams, evs, lights, every=20, warm=30, cells=12, trace=tr)
else: final("s5", N, cams, evs, lights, warm=30, trace=tr, quality=92)
