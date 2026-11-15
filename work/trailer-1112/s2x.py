from film import *
B = "game.ball"; N = 1800
cams = [cam("side", [key(0, [14, 3.2, -3], [0, 1.0, 0], 40)], dof=False),
        cam("behind", [key(0, [2.5, 3.2, -19], [0, 1.0, 2], 36)], dof=False)]
evs = [call(-60, "static:DreamEnvironment.Current", "SetWeather", "Clear"), ev(-60, "enable", on="game", s="1"), call(-59, "type:TennisPresentation", "Finish"),
       call(-58, "game", "AutoPlay", "true"), call(-57, "game", "Refeed")] + practicals_off(-60)
lights = banks() + hero_rig(PD, 1, "p") + hero_rig(OD, -1, "o")
preview("s2x", N, cams, evs, lights, every=30, warm=60, cells=30,
        trace=["game.Flow", "game.BallPosition", "game.BallVelocity", PD + ".PlayingClip", OD + ".PlayingClip", P + ".Swinging", O + ".Swinging", P, O])
