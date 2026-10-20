"""contact sheet: python3 sheet.py out.png cols img1 img2 ..."""
import sys
from PIL import Image
out, cols = sys.argv[1], int(sys.argv[2])
ims = [Image.open(p).convert('RGB') for p in sys.argv[3:]]
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (cols * w, rows * h))
for i, im in enumerate(ims):
    S.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
S.save(out)
print(out, S.size)
