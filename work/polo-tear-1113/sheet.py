"""sheet.py <round> <out.jpg> <runA> <runB> <frames comma list> [prefix M|F]: rows = frames, columns = front/side/back for run A then run B."""
import sys, os
from PIL import Image, ImageDraw
rnd, out, a, b = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
frames = [int(x) for x in sys.argv[5].split(",")]
pre = sys.argv[6] if len(sys.argv) > 6 else "M"
S = 230
cols = [(a, v) for v in ("front", "side", "back")] + [(b, v) for v in ("front", "side", "back")]
sheet = Image.new("RGB", (60 + S * len(cols), 24 + S * len(frames)), "white"); d = ImageDraw.Draw(sheet)
for j, (run, v) in enumerate(cols):
    d.text((60 + j * S + 4, 6), f"{run}: {v}", fill="black")
for i, f in enumerate(frames):
    d.text((4, 24 + i * S + S // 2), f"frame\n{f}", fill="black")
    for j, (run, v) in enumerate(cols):
        p = os.path.join(rnd, run, f"{pre}_{f:05d}_{v}.png")
        if os.path.exists(p):
            sheet.paste(Image.open(p).convert("RGB").resize((S, S)), (60 + j * S, 24 + i * S))
sheet.save(out, quality=85); print(out)
