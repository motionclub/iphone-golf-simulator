from film import *
# E1: base light + banks; E2: hand-driven actors with the game switched off
cams = [still("wide", [10, 3.0, -21], [0, 1.0, 0], 30, dof=False),
        cam("pmid", [key(0, [2.2, 1.2, 3.6], [0, 1.0, 0], 32)], PD, PD, aperture=2.0, focal=70),
        cam("omid", [key(0, [-2.4, 1.3, -5.5], [0, 1.0, 0], 30)], OD, OD, aperture=2.0, focal=70),
        still("far", [0, 1.4, -4], [0, 1.2, 13], 26, aperture=2.8, focal=85, focusAnchor=OD)]
evs = freeze_game(-20) + practicals_off(-20) + [
    ev(-10, "place", on=P, v=[0, .035, -11.6]), ev(-10, "place", on=O, v=[1.5, .035, 19.5]),
    tick(P, 0, 400), emote(20, PD, "IntroPushups"),
    drive(O, 0, 300, [1.5, .035, 19.5], [0.6, .035, 12.2]), tick(O, 301, 400),
    face(300, O, "Focus", 5),
]
lights = banks(near=0, far=120) + hero_rig(PD, 1, "p") + hero_rig(OD, -1, "o", on=200)
preview("s1test", 400, cams, evs, lights, every=10, warm=20, trace=[PD + ".State", PD + ".PlayingClip", OD + ".State", OD + ".PlayingClip", O])
