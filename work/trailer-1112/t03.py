from lib import *
import sys
PD, OD = "game.Player.<HeroTennisDriver>", "game.Opponent.<HeroTennisDriver>"
HIDE = ["Spectacle overlay", "Predicted landing", "Shot aim target", "Timing cue", "Tennis HUD", "weather ball", "weather glow"]
cams = [
 still("wide", [9, 2.2, -19], [0, 1.2, 0], 32, dof=False),
 still("pmid", [1.6, 1.25, 3.4], [0, 1.05, 0], 30, PD, PD, aperture=2.0, focal=70),
 still("pface", [0.5, 0.0, 1.1], [0, 0.03, 0], 18, PD + ":Head", PD + ":Head", aperture=2.0, focal=85),
 still("oface", [-0.5, 0.0, -1.1], [0, 0.03, 0], 18, OD + ":Head", OD + ":Head", aperture=2.0, focal=85),
 still("low", [-1.2, 0.25, 2.6], [0, 1.0, 0], 38, PD, PD, aperture=2.0, focal=50),
 still("sym", [0, 1.0, -19.5], [0, 1.3, 11], 28, aperture=4, focal=60),
 still("omid", [-1.4, 1.2, -3.0], [0, 1.05, 0], 30, OD, OD, aperture=2.0, focal=70),
 still("pback", [0.9, 1.7, -2.6], [0, 1.2, 12], 35, PD, "world", aperture=2.8, focal=50, focusAnchor=PD+":Head"),
]
def rig(who, z, n):
    return [lit(n+"key", [-1.6*z, 2.5, 2.6*z], [0, 1.45, 0], (1.0, .86, .72), 220, who, range=9, angle=38, shadows=True),
            lit(n+"rim", [1.9*z, 2.7, -2.6*z], [0, 1.5, 0], (.45, .7, 1.0), 420, who, range=9, angle=34),
            lit(n+"kick", [-2.2*z, 1.3, -1.8*z], [0, 1.3, 0], (1.0, .35, .6), 160, who, range=7, angle=40)]
lights = rig(PD, 1, "p") + rig(OD, -1, "o")
post = dict(exposure=0.1, contrast=18, saturation=8, bloom=.6, bloomThreshold=1.0, vignette=.32, shadows=[.92, .98, 1.12, 0], highlights=[1.06, 1.0, .94, 0])
take(name="t03", warm=300, timeScale=1, frames=1, cams=cams, hide=HIDE, lights=lights, post=post, env=dict(mainLight=.6, ambient=.45), w=1280, h=720, ss=1.5,
     events=[ev(-1, "get", on=PD, m="State"), ev(-1, "get", on=OD, m="State"), ev(-1,"get",on="game.Player"), ev(-1,"get",on="game.Opponent")])
sheet([f"stage/takes/t03/{c['name']}/f_00000.jpg" for c in cams], "shots/t03.jpg", cols=4, w=600)
