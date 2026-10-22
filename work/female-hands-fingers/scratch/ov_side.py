from PIL import Image, ImageDraw, ImageChops
import numpy as np, sys
B = '../../ArtDir/hero/base_lock/'
multi = Image.open(B + 'female_multiangle_body.jpg').convert('RGB')
K = 8
plate = multi.crop((750, 95, 850, 250)).resize((100*K, 155*K), Image.LANCZOS)
mdl = Image.open(sys.argv[1]).convert('RGBA')
bg = Image.new('RGBA', mdl.size, (225,225,228,255)); bg.alpha_composite(mdl); mdl = bg.convert('RGB')
S2 = 1.7039/288.5
# hand ROI in plate px: x 770..825, y 170..235  -> in K-scaled crop coords
x0, x1, y0, y1 = 770, 830, 165, 235
box = ((x0-750)*K, (y0-95)*K, (x1-750)*K, (y1-95)*K)
p = plate.crop(box); m = mdl.crop(box)
W = p.width; H = p.height
S = Image.new('RGB', (W*3+12, H), (20,20,24))
S.paste(p, (0,0)); S.paste(m, (W+6, 0))
ov = Image.blend(p, m, 0.5); S.paste(ov, (2*W+12, 0))
d = ImageDraw.Draw(S)
# grid lines every 2 cm in y (vertical) and z (horizontal), labelled; y=0 at px 791.5
for t in range(3):
    for panel in range(3):
        ox = panel*(W+6)
        # y lines
        for ycm in range(-8, 7, 2):
            xp = (791.5 + ycm/100/S2 - x0)*K
            if 0 <= xp < W: d.line([(ox+xp,0),(ox+xp,H)], fill=(255,160,0) if ycm else (255,0,0), width=1); d.text((ox+xp+2,2), f'{ycm}', fill=(255,160,0))
        for zm in (0.70, 0.75, 0.80, 0.85, 0.90):
            yp = (338.5 - zm/S2 - y0)*K
            if 0 <= yp < H: d.line([(ox,yp),(ox+W,yp)], fill=(0,170,255), width=1); d.text((ox+2,yp-12), f'z{zm:.2f}', fill=(0,170,255))
S.save(sys.argv[2]); print(S.size)
