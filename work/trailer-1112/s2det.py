from film import *
import sys
N = 1300
evs = [call(-60, "static:DreamEnvironment.Current", "SetWeather", "Clear"), ev(-60, "enable", on="game", s="1"), call(-59, "type:TennisPresentation", "Finish"),
       ev(-58, "seed", v=[11]), call(-58, "game", "AutoPlay", "true"), call(-57, "game", "Refeed")] + practicals_off(-60)
take(name=sys.argv[1], frames=N, warm=60, events=evs, trace=["game.Flow", "game.BallPosition", PD + ".PlayingClip", OD + ".PlayingClip"])
