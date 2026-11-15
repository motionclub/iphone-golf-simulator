from lib import *
PD, OD = "game.Player.<HeroTennisDriver>", "game.Opponent.<HeroTennisDriver>"
HIDE = ["Spectacle overlay", "Predicted landing", "Shot aim target", "Timing cue", "Tennis HUD", "weather ball", "weather glow"]
cams = [
 still("wide", [9, 2.2, -19], [0, 1.2, 0], 32, dof=False),
 still("pmid", [1.6, 1.25, 3.4], [0, 1.05, 0], 30, PD, PD, aperture=2.0, focal=70),
 still("pface", [0.45, 0.03, 1.0], [0, 0.03, 0], 20, PD + ":Head", PD + ":Head", aperture=2.0, focal=85),
 still("oface", [-0.45, 0.03, -1.0], [0, 0.03, 0], 20, OD + ":Head", OD + ":Head", aperture=2.0, focal=85),
 still("low", [-1.2, 0.25, 2.6], [0, 1.0, 0], 38, PD, PD, aperture=2.0, focal=50),
 still("sym", [0, 1.0, -19.5], [0, 1.3, 11], 28, aperture=4, focal=60),
]
evs = [ev(-30, "get", on="static:DreamEnvironment.Current", m="Condition"), ev(-30, "get", on="static:DreamEnvironment", m="Snapshot"),
       call(-29, "static:DreamEnvironment.Current", "SetWeather", "Clear"), ev(-1, "get", on="game", m="Flow"), ev(-1, "get", on=PD, m="State")]
take(name="t02a", warm=30, frames=1, events=evs, cams=cams, hide=HIDE, post=dict(exclusive=False, bloom=0, vignette=0, tonemap="none"), w=1280, h=720, ss=1.5)
sheet([f"stage/takes/t02a/{c['name']}/f_00000.jpg" for c in cams], "shots/t02a.jpg")
