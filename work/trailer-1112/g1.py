from golf import *
import sys
mode = sys.argv[1] if len(sys.argv) > 1 else "p"; who = sys.argv[2] if len(sys.argv) > 2 else "her"
her = who == "her"; N = 1100 if her else 1250; HIT = 240
STRIKE_ONLY = len(sys.argv) > 3 and sys.argv[3] == "strike"; NAME = ("g5" if STRIKE_ONLY else "g1") + who
cams = [
 cam("tee", [key(0, [-.12, .07, -.8], [0, .035, 0], 22), key(HIT, [-.1, .07, -.7], [0, .035, 0], 22)], B, B, aperture=2.0, focal=85, to=HIT + 40),
 cam("side", [key(0, [6.2, 1.0, .5], [0, 1.0, 0], 30), key(HIT + 200, [5.6, 1.0, .2], [0, 1.0, 0], 30)], GV, GV, aperture=2.8, focal=50, focusAnchor=GV, to=HIT + 260),
 cam("down", [key(0, [-.7, .45, -3.4], [.2, 1.5, 6], 34), key(HIT + 200, [-.6, .5, -3.0], [.2, 1.6, 6], 34)], GV, GV, aperture=2.8, focal=40, focusAnchor=GV, to=HIT + 260),
 cam("face", [key(0, [1.5, -.75, -.35], [0, -.02, 0], 19)], GV + ":Head", GV + ":Head", aperture=2.0, focal=100, posSmooth=14, lookSmooth=10, to=HIT + 60),
 cam("lowfront", [key(0, [2.6, .2, 1.4], [0, 1.1, 0], 36), key(HIT + 200, [2.2, .2, 1.2], [0, 1.2, 0], 36)], GV, GV, aperture=2.8, focal=50, focusAnchor=GV + ":Head", to=HIT + 260),
 cam("impact", [key(0, [1.0, .08, .75], [0, .05, 0], 26)], B, "world", aperture=2.8, focal=60, to=HIT + 80) if False else cam("impact", [key(0, [1.0, TEE_Y + .08, .75], [0, TEE_Y + .1, 0], 26)], aperture=2.8, focal=60, to=HIT + 80),
 cam("follow", [key(0, [1.6, 1.3, -6.5], [0, 0, 0], 40)], B, B, dof=False, posSmooth=22, lookSmooth=4, **{"from": HIT}),
 cam("fly", [key(0, [0, 3.5, -10], [0, -3, 22], 46)], B, B, dof=False, posSmooth=30, lookSmooth=18, **{"from": HIT}),
 cam("green", [key(0, [PIN[0] + 5, PIN[1] + 1.4, PIN[2] + 9], [PIN[0] - 1, PIN[1] + .3, PIN[2] - 6], 34)], aperture=4, focal=60, focusAnchor=B, **{"from": HIT + 300}),
 cam("cup", [key(0, [PIN[0] + .5, PIN[1] + .1, PIN[2] + 1.1], [PIN[0], PIN[1] + .04, PIN[2]], 24)], aperture=2.8, focal=85, **{"from": HIT + 300}),
]
BS0, BS1 = HIT - 150, HIT - 22
def ease(u): return u * u * (3 - 2 * u)
wind = [] if STRIKE_ONLY else [call(f, G, "ShowBackswing", round(ease((f - BS0) / (BS1 - BS0)), 4)) for f in range(BS0, BS1 + 1, 2)]
evs = setup(female=her, club="Iron" if her else "Hybrid") + wind + [call(HIT - 20, G, "StrikeToward", "12,159" if her else "12,165.1")]
tr = ["game.Current", "game.BallPosition", "game.golfer.Performing"]
if STRIKE_ONLY: cams = [c for c in cams if c["name"] in ("impact", "side", "down", "follow", "fly", "green", "cup")]
if mode == "p":
    gtake(NAME, N, cams, evs, golfer_rig(), every=40, trace=tr)
else: gtake(NAME, N, cams, evs, golfer_rig(), final=True, trace=tr)
