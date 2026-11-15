from golf import *
from film import move, drive, tick, emote, face
import sys
mode = sys.argv[1] if len(sys.argv) > 1 else "p"
N = 900; PX, PY, PZ = PIN; R = float(sys.argv[2]) if len(sys.argv) > 2 else .11; BR = .0
A = [PX - .55, 26.875 + .062, PZ - 4.2]; LIP = [PX - .02, PY + .075, PZ - R]; IN = [PX, PY - .10, PZ - .02]
cams = [
 cam("cup", [key(0, [PX + .42, PY + .075, PZ + 1.0], [PX, PY + .03, PZ - .15], 22), key(N, [PX + .36, PY + .075, PZ + .9], [PX, PY + .03, PZ - .1], 22)], aperture=2.4, focal=85, focusAnchor=B),
 cam("cupside", [key(0, [PX + 1.3, PY + .06, PZ - .5], [PX, PY + .04, PZ - .2], 18)], aperture=2.4, focal=100, focusAnchor=B),
 cam("cuptop", [key(0, [PX - .25, PY + 1.1, PZ - 1.5], [PX, PY, PZ - .25], 30), key(N, [PX - .2, PY + .9, PZ - 1.2], [PX, PY, PZ - .15], 30)], aperture=4, focal=50, focusAnchor=B),
 cam("roll", [key(0, [-.5, .12, -1.3], [0, .03, .6], 30)], B, B, aperture=2.8, focal=50, posSmooth=6, lookSmooth=4, to=430),
]
evs = setup(female=False, club="Putter", at="12,160") + [ev(-20, "get", on=B, m="localScale"), ev(-20, "get", on=B), call(-20, "static:HoleView", "ToWorld", "12,161"), call(-20, "static:HoleView", "ToWorld", "12,165"),
    ev(-10, "enable", on=G, s="0"), ev(-9, "place", on=B, v=A), ev(-9, "active", on=GV, s="0"),
    move(B, 0, 430, A, LIP, 0, "out"), move(B, 560, 578, LIP, IN, 0, "in")]
if mode == "p": gtake("g3", N, cams, evs, every=30)
else: gtake("g3", N, cams, evs, final=True)
