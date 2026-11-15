"""pick.py take out.jpg cam:f,f,f cam:f ...  -> contact sheet of chosen filmed frames (nearest existing frame)."""
import sys, os
from PIL import Image, ImageDraw
W = os.path.dirname(os.path.abspath(__file__)); take = sys.argv[1]; out = sys.argv[2]; cells = []
for spec in sys.argv[3:]:
    cam, fs = spec.split(":"); d = f"{W}/stage/takes/{take}/{cam}"; have = sorted(int(x[2:7]) for x in os.listdir(d) if x.endswith(".jpg"))
    for f in fs.split(","):
        g = min(have, key=lambda h: abs(h - int(f))); im = Image.open(f"{d}/f_{g:05d}.jpg").resize((480, 270)); ImageDraw.Draw(im).text((4, 2), f"{cam} {g}", fill=(255, 255, 0)); cells.append(im)
cols = int(os.environ.get("COLS", 5)); S = Image.new("RGB", (cols * 480, ((len(cells) + cols - 1) // cols) * 270))
for i, im in enumerate(cells): S.paste(im, ((i % cols) * 480, (i // cols) * 270))
S.save(out, quality=85); print(out, S.size)
