"""tile RGBA renders side by side on a dark background.  python3.13 tile.py out.png in1.png in2.png ..."""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
from PIL import Image
out = sys.argv[1]; ims = [Image.open(p).convert('RGBA') for p in sys.argv[2:]]
H = max(i.height for i in ims); W = sum(i.width for i in ims)
S = Image.new('RGB', (W, H), (40, 40, 42)); x = 0
for i in ims:
    S.paste(i, (x, 0), i); x += i.width
S.save(out); print(S.size)
