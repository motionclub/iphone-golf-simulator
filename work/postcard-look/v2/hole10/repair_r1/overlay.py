"""overlay.py PREVIEW.png GRID.ppm OUT.png : composite the verifier's smoke alpha grid (R = alpha*255) over a Blender preview (approximate look)."""
import sys
from PIL import Image
import numpy as np
prev = Image.open(sys.argv[1]).convert("RGB")
g = Image.open(sys.argv[2]).convert("RGB")
a = g.split()[0].resize(prev.size, Image.BICUBIC)
col = Image.new("RGB", prev.size, (205, 178, 168))
out = Image.composite(col, prev, a)
# mark >=0.3 contour lightly
g2 = g.split()[1].resize(prev.size, Image.NEAREST)
out.save(sys.argv[3])
