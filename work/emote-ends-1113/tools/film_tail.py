"""The end of each emote, before vs after, large: the last <n> frames (every <step>) of <view>, cropped to the hero's middle.
usage: film_tail.py <before_dir> <after_dir> <out.jpg> <view> <n> <step> <crop x0,y0,x1,y1 as 0..1> <move> [...]"""
import sys, glob, os
from PIL import Image, ImageDraw

before, after, out, view, n, step, crop = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6]), [float(x) for x in sys.argv[7].split(",")]
moves = sys.argv[8:]
rows = []
for m in moves:
    for tag, d in (("BEFORE", before), ("AFTER", after)):
        skip = int(os.environ.get("TAIL_SKIP", "0"))   # frames to leave off the end (a film's idle tail)
        allf = sorted(glob.glob(os.path.join(d, m, f"{view}_*.jpg")))
        files = allf[max(0, len(allf) - skip - n):len(allf) - skip][::step]
        rows.append((m, tag, files))
W = 220
im0 = Image.open(rows[0][2][0]); cw, ch = im0.width * (crop[2] - crop[0]), im0.height * (crop[3] - crop[1]); H = int(W * ch / cw)
cols = max(len(r[2]) for r in rows)
sheet = Image.new("RGB", (110 + cols * W, len(rows) * H), "white"); d = ImageDraw.Draw(sheet)
for i, (m, tag, files) in enumerate(rows):
    d.text((4, i * H + H // 2 - 10), f"{m.split('_')[-1]}\n{tag}", fill="black")
    for k, f in enumerate(files):
        im = Image.open(f).convert("RGB"); w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h))).resize((W, H))
        ImageDraw.Draw(im).text((3, 3), "end-" + str(len(files) * step - k * step), fill="white")
        sheet.paste(im, (110 + k * W, i * H))
sheet.save(out, quality=84); print(out)
