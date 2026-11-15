from film import *
import sys
N = 520; RQ = int(sys.argv[1]) if len(sys.argv) > 1 else 85; VX = sys.argv[2] if len(sys.argv) > 2 else "3.6"
cams = [cam("front", [key(0, [1.5, .5, -5.5], [1.6, .8, -11.5], 40)], dof=False),
        cam("side", [key(0, [9, .7, -11.6], [2, .8, -11.4], 34)], dof=False)]
evs = practicals_off(-60) + [call(-60, "static:DreamEnvironment.Current", "SetWeather", "Clear"), ev(-60, "enable", on="game", s="1"), call(-59, "type:TennisPresentation", "Finish"),
       call(-58, "game", "AutoPlay", "false"), call(-50, "game", "PrepareLesson"),
       ev(-1, "get", on=P), ev(-1, "get", on=O),
       call(20, "game", "InjectBall", "@" + O + "+0,1.0,-1.0", VX + ",3.4,-19"),
       call(RQ, "game", "RequestDive")]
lights = banks() + hero_rig(PD, 1, "p") + hero_rig(OD, -1, "o")
preview("s2dive", N, cams, evs, lights, every=12, warm=60, cells=18,
        trace=["game.Flow", "game.BallPosition", PD + ".PlayingClip", "game.DiveActive", P, OD + ".PlayingClip"])
