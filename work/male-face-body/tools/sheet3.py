"""python3 tools/sheet3.py <out.jpg> <unity_out tag> [...]: rows = ref sheet 07 + each tag (front, 3/4 315, profile 90) + lower close-ups."""
import sys
from PIL import Image, ImageDraw
r = Image.open('../../ArtDir/style/alive/male-reference-pack-2026-10-17/sheets/07-head-skin-neutral.png').convert('RGB')
rows = [[r.crop(b).resize((420, 420)) for b in ((120, 120, 600, 600), (770, 120, 1250, 600), (1450, 120, 1930, 600))]]
labels = ['REFERENCE sheet 07']
for t in sys.argv[2:]:
    rows.append([Image.open(f'unity_out/{t}/{v}.png').convert('RGB').resize((420, 420)) for v in ('front', 'tq315', 'right90')]); labels.append(t)
out = Image.new('RGB', (1260, 420 * len(rows)))
for i, row in enumerate(rows):
    for j, im in enumerate(row): out.paste(im, (420 * j, 420 * i))
    d = ImageDraw.Draw(out); d.rectangle((0, 420 * i, 200, 420 * i + 20), fill=(255, 255, 255)); d.text((5, 420 * i + 4), labels[i], fill=(0, 0, 0))
out.save(sys.argv[1], quality=86)
