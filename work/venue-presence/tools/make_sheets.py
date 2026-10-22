"""Before/after comparison sheets, one per map.

    make_sheets.py <old_dir> <new_dir> <out_dir> [venue ...]

Each row is one view: the shipped capture on the left, the new capture on the right. Views are the shipped set:
gameplay, postcard, edge, below, one drone frame, side. A footer carries the measured numbers the sheet is about.
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont

VIEWS = [('1_gameplay', 'gameplay camera'), ('2_postcard', 'postcard'), ('6_edge', 'edge'), ('5_below', 'below'), ('3_drone2', 'drone, frame 2 of 5'), ('3_drone5', 'drone, landing'), ('4_side', 'side')]
W, H = 960, 540
PAD, HEAD, LABEL = 12, 86, 30

def font(size):
    for p in ['/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/SFNS.ttf', '/Library/Fonts/Arial.ttf']:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def sheet(venue, old_dir, new_dir, out_dir, title, notes):
    rows = [v for v in VIEWS if os.path.exists(f'{old_dir}/{venue}_{v[0]}.png') and os.path.exists(f'{new_dir}/{venue}_{v[0]}.png')]
    foot = 24 * (len(notes) + 1) + 16
    img = Image.new('RGB', (PAD * 3 + W * 2, HEAD + (H + LABEL + PAD) * len(rows) + foot), (18, 18, 22))
    d = ImageDraw.Draw(img)
    d.text((PAD, 14), title, fill=(255, 255, 255), font=font(30))
    d.text((PAD, 52), 'left: shipped capture (ArtDir/screenshots/venues)    right: after this work (same views, same capture tool)', fill=(190, 190, 200), font=font(17))
    y = HEAD
    for key, label in rows:
        for i, (src, tag) in enumerate([(old_dir, 'BEFORE'), (new_dir, 'AFTER')]):
            im = Image.open(f'{src}/{venue}_{key}.png').convert('RGB').resize((W, H), Image.LANCZOS)
            x = PAD + i * (W + PAD)
            img.paste(im, (x, y + LABEL))
            d.text((x + 4, y + 5), f'{tag}  ·  {label}', fill=(255, 255, 255) if tag == 'AFTER' else (200, 200, 210), font=font(18))
        y += H + LABEL + PAD
    d.text((PAD, y + 4), 'Measured:', fill=(255, 255, 255), font=font(18))
    for k, n in enumerate(notes):
        d.text((PAD + 8, y + 28 + k * 24), n, fill=(210, 210, 220), font=font(16))
    os.makedirs(out_dir, exist_ok=True)
    path = f'{out_dir}/sheet_{venue}.png'
    img.save(path)
    print('wrote', path, img.size)

if __name__ == '__main__':
    old_dir, new_dir, out_dir = sys.argv[1:4]
    venues = sys.argv[4:] or ['skyscraper', 'volcano']
    notes_file = os.path.join(out_dir, 'sheet_notes.txt')
    notes = {}
    if os.path.exists(notes_file):                       # lines: venue|text
        for line in open(notes_file):
            if '|' in line:
                v, t = line.rstrip('\n').split('|', 1); notes.setdefault(v, []).append(t)
    titles = {'skyscraper': 'SKY OPEN (Skyscraper): before / after', 'volcano': 'MAGMA OPEN (Volcano): before / after'}
    for v in venues:
        sheet(v, old_dir, new_dir, out_dir, titles.get(v, v), notes.get(v, []))
