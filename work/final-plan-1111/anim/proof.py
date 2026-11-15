"""proof.py <round> <out.jpg>: the board for Adnan: the worst wrist of each kind in real play, before | after the limits, the same frame
(left pair: from the game camera's side; right pair: side on to the bend)."""
import sys, os, re, glob
from PIL import Image, ImageDraw, ImageFont
A = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(A, sys.argv[1]); out = sys.argv[2]
F = lambda s: ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", s)
CASES = [("tennis_f/Tennis-tennis_F_L_support", "Tennis, her ready stance: the hand that steadies the racket"),
         ("bowl/Bowling-hub_M_L_free", "Bowling, his empty left hand"),
         ("bowl/Bowling-hub_M_R_free", "Bowling, his empty right hand"),
         ("golf/Golf-golf_F_L_support", "Golf, her gloved hand at address"),
         ("tennis_m/Tennis-tennis_M_R_grip", "Tennis, his racket arm in the follow-through (hand kept where the clip has it: little change)")]
S = 400; gap = 16; lab = 34; top = 96
img = Image.new("RGB", (4 * S + gap + 20, top + len(CASES) * (S + lab)), (18, 18, 22)); d = ImageDraw.Draw(img)
d.text((10, 12), "Wrist limits in real play: the same frame before and after", font=F(30), fill=(255, 255, 255))
for k, t in enumerate(["before", "after", "before (side on to the bend)", "after (side on to the bend)"]):
    d.text((10 + k * S + (gap if k >= 2 else 0) + 4, 60), t, font=F(20), fill=(255, 190, 120) if k % 2 == 0 else (140, 220, 255))
for i, (pat, title) in enumerate(CASES):
    fs = [f for f in glob.glob(os.path.join(R, "*", "*_game_before.png")) if pat in f.replace(R, "")]
    if not fs: print("none", pat); continue
    fs.sort(key=lambda f: -int(re.search(r"_(\d+)to(\d+)_", f).group(1))); f = fs[0]; m = re.search(r"_(\d+)to(\d+)_", f)
    y = top + i * (S + lab)
    d.text((10, y + 4), f"{title}:  {int(m.group(1))} to {int(m.group(2))} degrees off the forearm's line", font=F(21), fill=(235, 235, 235))
    for k, v in enumerate(["game_before", "game_after", "bend_before", "bend_after"]):
        img.paste(Image.open(f.replace("game_before", v)).convert("RGB").resize((S, S), Image.LANCZOS), (10 + k * S + (gap if k >= 2 else 0), y + lab))
img.save(out, quality=90); print(out, img.size)
