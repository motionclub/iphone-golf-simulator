"""Before/after strips from two JoyFilm runs with the same layout.
usage: film_ba.py <before_dir> <after_dir> <out.jpg> <view> <step> <move> [<move> ...]
Each move gives two rows (before, after) of every <step>-th frame of <view>_*.jpg, same frame numbers in both."""
import sys, glob, os
from PIL import Image, ImageDraw

before, after, out, view, step = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
moves = sys.argv[6:]
W, H = 170, 0
rows = []
for m in moves:
    for tag, d in (("BEFORE", before), ("AFTER", after)):
        files = sorted(glob.glob(os.path.join(d, m, f"{view}_*.jpg")))
        rows.append((m, tag, files[::step]))
cols = max(len(r[2]) for r in rows)
first = Image.open(rows[0][2][0]); H = int(W * first.height / first.width)
sheet = Image.new("RGB", (110 + cols * W, len(rows) * H), "white")
d = ImageDraw.Draw(sheet)
for i, (m, tag, files) in enumerate(rows):
    d.text((4, i * H + H // 2 - 10), f"{m.replace('result_Emote_', '').replace('emote_Emote_', '')}\n{tag}", fill="black")
    for k, f in enumerate(files):
        im = Image.open(f).convert("RGB").resize((W, H))
        ImageDraw.Draw(im).text((3, 3), os.path.basename(f).split("_")[-1][:-4], fill="white")
        sheet.paste(im, (110 + k * W, i * H))
sheet.save(out, quality=82)
print(out, len(rows), "rows", cols, "cols")
