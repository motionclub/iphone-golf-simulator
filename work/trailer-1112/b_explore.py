from lib import *
G = "game"; BV = "game.ballView"
evs = [ev(-400, "gameclock"), call(-399, G, "KeyboardEnabled", "false"), call(-398, "game.Players", "Add", "Rival"), call(-397, "game.PlayerFemale", "Add", "true"), call(-396, "game.PlayerFemale", "Add", "false"),
       call(-395, G, "NewGame", "null"), call(-300, "game.Autoplay", "Enqueue", "3.5,7.6,300,45,0"),
       ev(-1, "get", on=G, m="Flow"), ev(-1, "get", on="game.heroes"), ev(-1, "get", on=BV), ev(-1, "get", on="cam")]
cams = [cam("wide", [key(0, [0, 4.2, -13.5], [0, .4, 12], 50)], dof=False), cam("side", [key(0, [5.2, 2.4, -1], [-.5, .4, 12], 50)], dof=False),
        cam("pins", [key(0, [.4, .55, 15.6], [0, .2, 18.3], 40)], dof=False), cam("lounge", [key(0, [2.5, 1.8, -3], [-1, 1.2, -13], 50)], dof=False),
        cam("gamecam", [key(0, [0, 0, 0], [0, 0, 5], 50)], "cam", "cam~", dof=False)]
take(name="bx", frames=1500, warm=400, events=evs, cams=cams, every=100, post=dict(exclusive=False, bloom=0, vignette=0, tonemap="none"), w=640, h=360, ss=2, trace=["game.Flow", "game.Current", "game.StandingPins", BV])
rows=[r.split(';') for r in open(W+'/stage/takes/bx/trace.csv').read().splitlines()]
prev=None
for r in rows[1:]:
    k=(r[1],r[2],r[3])
    if k!=prev or int(r[0])%150==0: print(r[0], r[1], r[2], r[3], r[4][:70]); prev=k
