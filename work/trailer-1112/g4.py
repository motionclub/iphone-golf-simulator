from golf import *
from film import WARM, COOL
import sys
mode = sys.argv[1] if len(sys.argv) > 1 else "p"; who = sys.argv[2] if len(sys.argv) > 2 else "him"
her = who == "her"; N = 620
cams = [
 cam("mid", [key(0, [4.6, 1.0, -.6], [0, 1.15, 0], 30), key(N, [4.0, 1.0, -.4], [0, 1.2, 0], 30)], GV, GV, aperture=2.4, focal=70, focusAnchor=GV + ":Head", lookSmooth=10),
 cam("close", [key(0, [2.6, 1.5, -.9], [0, .02, 0], 20)], GV, GV + ":Head", aperture=2.0, focal=100, lookSmooth=10, focusAnchor=GV + ":Head"),
 cam("low", [key(0, [3.2, .3, 1.6], [0, 1.2, 0], 34)], GV, GV, aperture=2.8, focal=50, focusAnchor=GV + ":Head", lookSmooth=10),
]
moves = [("Emote_Shock", 40)] if her else [("Emote_JumpJoy", 40)]
evs = setup(female=her, club="Iron") + [ev(-30, "enable", on=G, s="0")] + [call(f, GV, "Perform", m, "0", "false") for m, f in moves] + [ev(-1, "get", on=GV, m="PerformanceDuration")]
tr = ["game.golfer.Performing"]
gtake("g4" + who, N, cams, evs, golfer_rig(), final=(mode != "p"), trace=tr, **({} if mode != "p" else dict(every=30)))
