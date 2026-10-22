"""Plate vs render close-up composites (system python3 + Pillow).
python3 cmpv.py <out.png> <plate:bald|sheet> <box x0,y0,x1,y1 in 1280x720 plate px> <outscale> <label=renderdir/view[@rp]> [label=...]...
Each render panel is the locked-camera render (view@rp = rp x resolution) cropped to the same box; the plate panel is first.
Contrast boost (--boost f) applies to every panel equally."""
import sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/'
def load_plate(kind):
    return Image.open(R + ('male_body_bald.jpg' if kind == 'bald' else 'male_multiangle_body.jpg')).convert('RGB')
def crop_panel(im, box, rp, outscale):
    b = tuple(int(round(v * rp)) for v in box); c = im.crop(b)
    return c.resize((int((box[2] - box[0]) * outscale), int((box[3] - box[1]) * outscale)), Image.LANCZOS)
import json
CAMS = {c['name']: c for c in json.load(open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-silhouette/reference-cameras.json'))['views']}
def draw_grid(sheet_panel, box, outscale, view, x0px, y0px):
    """draw z/x grid for 'bald_back','bald_front','left','right' on a panel pasted at (x0px,y0px)"""
    c = CAMS[view]; mpp = c['metres_per_pixel']; d = ImageDraw.Draw(sheet_panel)
    z = 0.0
    while z < 2.0:
        row = (c['sole_y'] - z / mpp - box[1]) * outscale
        if 0 <= row < (box[3] - box[1]) * outscale:
            d.line([(x0px, y0px + row), (x0px + (box[2] - box[0]) * outscale, y0px + row)], fill=(80, 160, 255) if abs(z * 100 % 10) < 1e-6 else (60, 100, 150), width=1)
            d.text((x0px + 2, y0px + row - 11), f'z{z:.2f}', fill=(120, 200, 255))
        z += 0.05
    k = -0.30
    while k <= 0.30001:
        sgn = -1 if view == 'bald_back' or view == 'right' else 1
        col = (c['centre_x'] + sgn * k / mpp - box[0]) * outscale
        if 0 <= col < (box[2] - box[0]) * outscale:
            d.line([(x0px + col, y0px), (x0px + col, y0px + (box[3] - box[1]) * outscale)], fill=(255, 120, 80) if abs(k) < 1e-6 else (150, 80, 60), width=1)
            d.text((x0px + col + 2, y0px + 2), f'{k:+.2f}', fill=(255, 170, 120))
        k += 0.05
def main():
    a = sys.argv[1:]; boost = 1.0; grid = None; direct = False
    if '--direct' in a: a.remove('--direct'); direct = True
    if '--grid' in a: i = a.index('--grid'); grid = a[i + 1]; del a[i:i + 2]
    if '--boost' in a: i = a.index('--boost'); boost = float(a[i + 1]); del a[i:i + 2]
    out, kind, box, outscale = a[0], a[1], [int(x) for x in a[2].split(',')], float(a[3]); panels = a[4:]
    plate = load_plate(kind); pan = [('PLATE', crop_panel(plate, box, 1, outscale))]
    for p in panels:
        lab, _, spec = p.partition('=')
        if direct:
            im = Image.open(spec + '.png').convert('RGB'); sz = pan[0][1].size; pan.append((lab, im.resize(sz, Image.LANCZOS))); continue
        path, _, rp = spec.partition('@'); rp = int(rp) if rp else 1
        pan.append((lab, crop_panel(Image.open(path + ('@%d' % rp if rp > 1 else '') + '.png').convert('RGB'), box, rp, outscale)))
    if boost != 1.0: pan = [(l, ImageEnhance.Contrast(im).enhance(boost)) for l, im in pan]
    w, h = pan[0][1].size; pad = 8; top = 22
    sheet = Image.new('RGB', (len(pan) * (w + pad) + pad, h + top + pad), (20, 20, 20)); d = ImageDraw.Draw(sheet)
    for i, (l, im) in enumerate(pan):
        x = pad + i * (w + pad); sheet.paste(im, (x, top)); d.text((x + 4, 5), l, fill=(255, 200, 80))
        if grid: draw_grid(sheet, box, outscale, grid, x, top)
    sheet.save(out); print(out, sheet.size)
main()
