from lib import *
P, O = "game.Player", "game.Opponent"
HIDE = ["Spectacle overlay", "Predicted landing", "Shot aim target", "Timing cue", "Tennis HUD"]
cams = [
 still("wide", [9, 2.2, -19], [0, 1.2, 0], 32, dof=False),
 still("pmid", [1.6, 1.25, 3.4], [0, 1.05, 0], 30, P, P, aperture=2.0, focal=70),
 still("pface", [0.35, 0.02, 1.0], [0, 0.0, 0], 20, P + ":Head", P + ":Head", aperture=2.0, focal=85),
 still("oface", [-0.35, 0.02, -1.0], [0, 0.0, 0], 20, O + ":Head", O + ":Head", aperture=2.0, focal=85),
 still("low", [-1.2, 0.25, 2.6], [0, 1.0, 0], 38, P, P, aperture=2.0, focal=50),
 still("sym", [0, 1.0, -19.5], [0, 1.3, 11], 28, aperture=4, focal=60),
]
setup = [call(-60, "type:TennisPresentation", "Finish"), call(-58, "game", "Flow", "PointOver"), call(-58, "game", "resetTimer", "1000000")]
take(name="t01a", warm=60, frames=1, events=setup, cams=cams, hide=HIDE, post=dict(exclusive=False, bloom=0, vignette=0, tonemap="none"), w=1280, h=720, ss=1.5)
sheet([f"stage/takes/t01a/{c['name']}/f_00000.jpg" for c in cams], "shots/t01a.jpg")
