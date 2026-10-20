"""Compose the outfit-example sheets (PIL).  python3 compose_sheets.py"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
F = ROOT / 'work/male-outfit-preview/final'
O = ROOT / 'ArtDir/hero/base_lock/preview/outfit_example'
BG = (30, 31, 35)
FG = (238, 238, 242)
DIM = (170, 172, 182)
FONT = '/System/Library/Fonts/Helvetica.ttc'


def font(sz):
    return ImageFont.truetype(FONT, sz)


def pill(S, xy, s, sz=26):
    d = ImageDraw.Draw(S)
    f = font(sz)
    w = int(d.textlength(s, font=f)) + 22
    d.rounded_rectangle((xy[0], xy[1], xy[0] + w, xy[1] + sz + 16), radius=10, fill=(14, 14, 18))
    d.text((xy[0] + 11, xy[1] + 7), s, font=f, fill=FG)


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def swatches(S, x, y, items, sz=34, gap=10):
    d = ImageDraw.Draw(S)
    for name, hx in items:
        d.rounded_rectangle((x, y, x + sz, y + sz), radius=8, fill=hexrgb(hx), outline=(70, 72, 80), width=2)
        d.text((x + sz + 10, y + 4), name, font=font(22), fill=DIM)
        x += sz + 14 + int(d.textlength(name, font=font(22))) + gap + 14
    return x


def hero():
    im = Image.open(F / 'hero_q3.png').convert('RGB')
    S = Image.new('RGB', (im.width, im.height + 150), BG)
    S.paste(im, (0, 150))
    d = ImageDraw.Draw(S)
    d.text((40, 24), 'Male HeroBase — outfit & expression example', font=font(52), fill=FG)
    d.text((40, 92), 'Blender preview render · separate garment / face / hair layers on the unchanged Body_M · not a gate item', font=font(26), fill=DIM)
    S.save(O / '01_hero_cheer_q3.png')
    return S.size


def turnaround():
    names = [('turn_front', 'front'), ('turn_q3', '3/4 front'), ('turn_side', 'side'), ('turn_back', 'back'), ('turn_q3b', '3/4 back')]
    ims = [Image.open(F / f'{k}.png').convert('RGB') for k, _ in names]
    w, h = ims[0].size
    S = Image.new('RGB', (w * 5, h + 130), BG)
    d = ImageDraw.Draw(S)
    d.text((40, 20), 'Turnaround — "Coral Court" kit, happy face', font=font(46), fill=FG)
    d.text((40, 76), 'shirt · shorts · socks · sneakers · wristbands · hair  (all separate meshes with real thickness)', font=font(24), fill=DIM)
    for i, (im, (_, lab)) in enumerate(zip(ims, names)):
        S.paste(im, (i * w, 130))
        pill(S, (i * w + 18, 148), lab)
    S.save(O / '02_turnaround.png')
    return S.size


def expressions():
    ex = [('expr_happy', 'Happy'), ('expr_cheer', 'Cheer'), ('expr_focus', 'Focus'), ('expr_surprise', 'Surprise')]
    q3 = [('exprq3_happy', 'Happy · 3/4'), ('exprq3_cheer', 'Cheer · 3/4'), ('exprq3_focus', 'Focus · 3/4'), ('exprq3_surprise', 'Surprise · 3/4')]
    ims = [Image.open(F / f'{k}.png').convert('RGB') for k, _ in ex]
    w, h = ims[0].size
    cols = 4
    S = Image.new('RGB', (w * cols, h + 130 + h), BG)
    d = ImageDraw.Draw(S)
    d.text((40, 20), 'Facial expressions', font=font(46), fill=FG)
    d.text((40, 76), 'eyes, lids, brows, nostrils and mouth are separate layers sitting 1–3 mm proud of the head — one collection per expression', font=font(24), fill=DIM)
    for i, (im, (_, lab)) in enumerate(zip(ims, ex)):
        S.paste(im, (i * w, 130))
        pill(S, (i * w + 18, 148), lab)
    # second row: 3/4 views
    for i, (k, lab) in enumerate(q3):
        im = Image.open(F / f'{k}.png').convert('RGB')
        S.paste(im, (i * w, 130 + h))
        pill(S, (i * w + 18, 148 + h), lab)
    d.text((40, 100), 'face shape (nose, cheeks, ears) is still the blank blockout — the layers add features, they do not reshape the head', font=font(22), fill=DIM)
    S.save(O / '03_expressions.png')
    return S.size


def colorways():
    cws = [('cw_coral_court', 'Coral Court', [('shirt', '#FF5B4A'), ('trim', '#F7F4EC'), ('stripe', '#0E2A47'), ('shorts', '#0E2A47'), ('accent', '#FFD21F')]),
           ('cw_sky_doubles', 'Sky Doubles', [('shirt', '#38C6FF'), ('trim', '#FFFFFF'), ('stripe', '#0E2A47'), ('shorts', '#F7F4EC'), ('accent', '#D3F34B')]),
           ('cw_violet_smash', 'Violet Smash', [('shirt', '#5B2BD9'), ('trim', '#F7F4EC'), ('stripe', '#FFD21F'), ('shorts', '#16123A'), ('accent', '#FFD21F')])]
    ims = [Image.open(F / f'{k}.png').convert('RGB') for k, _, _ in cws]
    w, h = ims[0].size
    S = Image.new('RGB', (w * 3, h + 130 + 90), BG)
    d = ImageDraw.Draw(S)
    d.text((40, 20), 'Colourways — same meshes, only the material colours change', font=font(46), fill=FG)
    d.text((40, 76), 'palette from the app brand colours (coral, sky, violet, sun, lime, navy, cream)', font=font(24), fill=DIM)
    for i, (im, (_, name, sw)) in enumerate(zip(ims, cws)):
        S.paste(im, (i * w, 130))
        pill(S, (i * w + 18, 148), name, 30)
        swatches(S, i * w + 24, 130 + h + 22, sw[:5], sz=30, gap=0)
    S.save(O / '04_colorways.png')
    return S.size


if __name__ == '__main__':
    O.mkdir(parents=True, exist_ok=True)
    print('hero', hero())
    print('turnaround', turnaround())
    print('expressions', expressions())
    print('colorways', colorways())
