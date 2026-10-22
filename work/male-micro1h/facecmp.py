"""Plate | mesh | 50% overlay crops of the face region for the head-detail panels.  python3 facecmp.py <panels_dir> <tag> [views...]"""
import sys
from PIL import Image
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
plate = Image.open(R + 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
pdir = sys.argv[1]; tag = sys.argv[2]; views = sys.argv[3:] or ['front', 'q3L', 'q3R', 'left']
SPEC = {'front': ((5, 62, 433, 352), (150, 120, 310, 300)), 'q3L': ((5, 390, 433, 668), (130, 440, 315, 620)),
        'q3R': ((433, 390, 834, 668), (520, 440, 740, 620)), 'left': ((433, 62, 834, 352), (470, 100, 640, 300))}
for name in views:
    box, face = SPEC[name]
    p = plate.crop(box); p = p.resize((p.width * 2, p.height * 2), Image.LANCZOS)
    m = Image.open(R + 'work/male-micro1h/' + pdir + '/' + name + '.png').convert('RGBA').resize(p.size, Image.LANCZOS)
    bg = Image.new('RGBA', p.size, (56, 56, 60, 255)); mm = Image.alpha_composite(bg, m).convert('RGB')
    x0, y0, x1, y1 = [int((v - (box[0] if i % 2 == 0 else box[1])) * 2) for i, v in enumerate(face)]
    a = p.crop((x0, y0, x1, y1)); b = mm.crop((x0, y0, x1, y1)); ov = Image.blend(a, b, 0.5)
    w, h = a.size; s = Image.new('RGB', (w * 3 + 20, h)); s.paste(a, (0, 0)); s.paste(b, (w + 10, 0)); s.paste(ov, (2 * w + 20, 0))
    out = R + f'work/male-micro1h/r/zc_{tag}_{name}.png'; s.save(out); print(out, s.size)
