from lib import *
PD, OD = "game.Player.<HeroTennisDriver>", "game.Opponent.<HeroTennisDriver>"
HIDE = ["Spectacle overlay", "Predicted landing", "Shot aim target", "Timing cue", "Tennis HUD", "weather ball", "weather glow", "Contact shadow — Tennis ball"]
cams = [
 still("pface", [0.5, 0.0, 1.1], [0.02, 0.03, 0], 17, PD + ":Head", PD + ":Head", aperture=1.8, focal=85),
 still("oface", [0.42, 0.02, -1.15], [-0.02, 0.02, 0], 17, OD + ":Head", OD + ":Head", aperture=1.8, focal=85),
 still("sym", [0, 0.55, -20.5], [0, 2.4, 11], 30, aperture=5.6, focal=50, focusAnchor=PD),
 still("low", [-1.3, 0.22, 2.7], [0.1, 1.05, 0], 36, PD, PD, aperture=2.0, focal=50),
 still("olow", [1.1, 0.3, -2.9], [0, 1.0, 0], 34, OD, OD, aperture=2.0, focal=50),
 still("shoes", [0.9, 0.12, 1.3], [0, 0.12, 0.1], 24, PD, PD, aperture=1.8, focal=85),
]
def rig(who, z, n):
    return [lit(n+"key", [-1.6*z, 2.5, 2.6*z], [0, 1.45, 0], (1.0, .86, .72), 200, who, range=9, angle=38, shadows=True),
            lit(n+"rim", [1.9*z, 2.7, -2.6*z], [0, 1.5, 0], (.45, .7, 1.0), 460, who, range=9, angle=34),
            lit(n+"kick", [-2.2*z, 1.3, -1.8*z], [0, 1.3, 0], (1.0, .35, .6), 170, who, range=7, angle=40)]
post = dict(exposure=0.15, contrast=16, saturation=6, bloom=.45, bloomThreshold=1.1, vignette=.3, shadows=[.92, .98, 1.12, 0], highlights=[1.06, 1.0, .94, 0])
take(name="t04", warm=40, timeScale=1, frames=1, cams=cams, hide=HIDE, lights=rig(PD, 1, "p") + rig(OD, -1, "o"), post=post, env=dict(mainLight=1.0, ambient=.5), w=1920, h=1080, ss=1.5,
     events=[call(-40, "static:MajesticWeather", "SetEnabled", "false"), call(-40, "static:DreamEnvironment.Current", "SetWeather", "Clear"), call(-39, "game", "resetTimer", "1000000"),
             call(-39, "game.ball", "position", "0,-5,0")])
from PIL import Image
ims = [Image.open(f"stage/takes/t04/{n}/f_00000.jpg") for n in ["pface", "oface", "sym", "low", "olow", "shoes"]]
bar = (1080 - 804) // 2
S = Image.new("RGB", (1920 * 2 // 2, 0))
tiles = []
for im in ims:
    im = im.copy(); px = im.load()
    from PIL import ImageDraw
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 1920, bar], fill=(0, 0, 0)); d.rectangle([0, 1080 - bar, 1920, 1080], fill=(0, 0, 0)); tiles.append(im.resize((960, 540), Image.LANCZOS))
S = Image.new("RGB", (1920, 1620)); 
for i, t in enumerate(tiles): S.paste(t, ((i % 2) * 960, (i // 2) * 540))
S.save("shots/t04.jpg", quality=90)
