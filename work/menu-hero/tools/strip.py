# chat G: side-by-side strip of plaza stills.  strip.py <out> <scale> <img...>
import sys
from PIL import Image
out, sc, files = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).convert('RGB') for f in files]
w, h = ims[0].size
s = Image.new('RGB', (w * len(ims), h))
for i, im in enumerate(ims): s.paste(im, (i * w, 0))
s.resize((int(w * len(ims) * sc), int(h * sc))).save(out)
