from lib import *
import sys
hole = int(sys.argv[1]) if len(sys.argv) > 1 else 22
G = "game"; GV = "game.golfer"; B = "game.ball"
evs = [call(-200, G, "JumpToHole", hole), call(-150, G, "DropBall", "=game.CurrentHole.Tee"), call(-140, G, "SelectClub", "Driver"),
       call(-100, "static:HoleView", "ToWorld", "=game.CurrentHole.Tee"), call(-100, "static:HoleView", "ToWorld", "=game.CurrentHole.Pin"),
       ev(-1, "get", on=G, m="Current"), ev(-1, "get", on=GV), ev(-1, "get", on=B), ev(-1, "get", on="cam")]
cams = [cam("behind", [key(0, [1.2, 1.5, -4.0], [0, 1.0, 8], 45)], B, B, dof=False), cam("high", [key(0, [10, 45, -50], [0, 0, 60], 50)], B, B, dof=False),
        cam("front", [key(0, [2.5, 1.0, 4.5], [0, .9, 0], 35)], GV, GV, dof=False), cam("side", [key(0, [5.0, 1.0, 0], [0, .9, 0], 35)], GV, GV, dof=False), cam("gamecam", [key(0, [0, 0, 0], [0, 0, 5], 50)], "cam", "cam~", dof=False)]
take(name=f"gx{hole}", frames=1, warm=200, events=evs, cams=cams, post=dict(exclusive=False, bloom=0, vignette=0, tonemap="none"), w=960, h=540, ss=1.5)
