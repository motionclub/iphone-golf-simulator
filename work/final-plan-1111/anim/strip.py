"""strip.py <round> <out.jpg> <pattern>...: full-size before | after pairs (game and bend views) for the probe pictures whose name
contains each pattern (the worst one per pattern)."""
import sys, os, re, glob
from PIL import Image, ImageDraw, ImageFont
A = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(A, sys.argv[1]); out = sys.argv[2]
font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
rows = []
for pat in sys.argv[3:]:
    fs = [f for f in glob.glob(os.path.join(R, "*", "*_game_before.png")) if pat in f.replace(R, "")]
    if not fs: print("none for", pat); continue
    pick = int(os.environ.get("PICK", "0"))
    fs.sort(key=lambda f: -int(re.search(r"_(\d+)to(\d+)_", f).group(1))); rows.append(fs[min(pick, len(fs) - 1)])
S = 420; img = Image.new("RGB", (4 * S + 30, len(rows) * (S + 30) + 6), (18, 18, 22)); d = ImageDraw.Draw(img)
for i, f in enumerate(rows):
    y = i * (S + 30); name = os.path.basename(f).replace("_game_before.png", ""); d.text((6, y + 4), f"{os.path.basename(os.path.dirname(f))}  {name}   (as the game camera sees it: before, after;  side on to the bend: before, after)", font=font, fill=(255, 220, 150))
    for k, v in enumerate(["game_before", "game_after", "bend_before", "bend_after"]):
        img.paste(Image.open(f.replace("game_before", v)).convert("RGB"), (k * S + (10 if k >= 2 else 0) + (10 if k >= 2 else 0), y + 30))
img.save(out, quality=90); print(out, img.size)
