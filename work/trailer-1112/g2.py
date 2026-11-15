from golf import *
import sys
mode = sys.argv[1] if len(sys.argv) > 1 else "p"; who = sys.argv[2] if len(sys.argv) > 2 else "him"
her = who == "her"; N = 420
cams = [
 cam("down", [key(0, [-.7, .45, -3.4], [.2, 1.5, 6], 34), key(N, [-.55, .5, -2.9], [.2, 1.6, 6], 34)], GV, GV, aperture=2.8, focal=40, focusAnchor=GV),
 cam("side", [key(0, [6.2, 1.0, .5], [0, 1.0, 0], 30), key(N, [5.6, 1.0, .2], [0, 1.0, 0], 30)], GV, GV, aperture=2.8, focal=50, focusAnchor=GV),
 cam("up", [key(0, [1.5, -.75, -.35], [0, -.02, 0], 19)], GV + ":Head", GV + ":Head", aperture=2.0, focal=100, posSmooth=14, lookSmooth=10),
 cam("lowfront", [key(0, [2.6, .2, 1.4], [0, 1.1, 0], 36), key(N, [2.2, .2, 1.2], [0, 1.2, 0], 36)], GV, GV, aperture=2.8, focal=50, focusAnchor=GV + ":Head"),
 cam("impact", [key(0, [1.0, TEE_Y + .08, .75], [0, TEE_Y + .1, 0], 26)], aperture=2.8, focal=60),
]
evs = setup(female=her, club="Iron" if her else "Hybrid") + [call(-5, "game.Swing.Synthetic", "FixedStepSeconds", "0.008333333"), call(40, "game.Swing.Synthetic", "Backswing", "true"), call(130, "game.Swing.Synthetic", "Backswing", "false")]
tr = ["game.Current", "game.Swing.Phase", "game.BallPosition"]
gtake("g2" + who, N, cams, evs, golfer_rig(), final=(mode != "p"), trace=tr, **({} if mode != "p" else dict(every=20)))
