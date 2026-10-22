"""plate vs mesh local-contrast 'relief' comparison.  python3.13 relief.py out.png <clay renderdir tags...>   (needs r/<tag>c/{front,back}.png clay renders)"""
import sys
from PIL import Image, ImageFilter
import numpy as np
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
PL = Image.open(R + 'ArtDir/hero/base_lock/male_body_plain.jpg').convert('L')
BOX = {'front': (250, 150, 460, 400), 'back': (820, 150, 1015, 400)}
def enh(im, box, z=3, k=5, blur=14):
    c = im.crop(box); a = np.asarray(c).astype(float); b = np.asarray(c.filter(ImageFilter.GaussianBlur(blur))).astype(float)
    d = np.clip((a - b) * k + 128, 0, 255).astype('uint8'); return Image.fromarray(d).resize((c.width * z, c.height * z), Image.LANCZOS)
def sheet(out, view, tags):
    box = BOX[view]; cols = [enh(PL, box)]
    for t in tags: cols.append(enh(Image.open(f'r/{t}/{view}.png').convert('L'), box))
    s = Image.new('L', (sum(c.width for c in cols) + 6 * (len(cols) - 1), cols[0].height)); x = 0
    for c in cols: s.paste(c, (x, 0)); x += c.width + 6
    s.save(out); print(out, s.size)
if __name__ == '__main__':
    out = sys.argv[1]; view = sys.argv[2]; sheet(out, view, sys.argv[3:])
