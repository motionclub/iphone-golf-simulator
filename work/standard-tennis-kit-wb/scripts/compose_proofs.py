"""Compose the proof sheets from proof/raw cells (system python + Pillow).  python3 compose_proofs.py"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/'
RAW = W + 'proof/raw/'
OUT = W + 'proof/'


def font(sz):
    for p in ('/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/Supplemental/Arial.ttf', '/Library/Fonts/Arial.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def label(img, text, xy, sz=22, fill=(20, 20, 20), bg=None):
    d = ImageDraw.Draw(img)
    f = font(sz)
    if bg:
        tw = d.textlength(text, font=f)
        d.rectangle([xy[0] - 4, xy[1] - 2, xy[0] + tw + 4, xy[1] + sz + 4], fill=bg)
    d.text(xy, text, font=f, fill=fill)


def onbody(tag, title):
    views = (('front', 'FRONT'), ('back', 'BACK'), ('left', 'LEFT'), ('right', 'RIGHT'), ('q3', '3/4'))
    cells = {cw: [Image.open(f'{RAW}onbody_{tag}_{cw}_{v}.png').convert('RGB') for v, _ in views] for cw in ('White', 'Black')}
    cw0 = cells['White'][0]
    w, h = cw0.size
    pad = 46
    sheet = Image.new('RGB', (w * 5, (h + pad) * 2 + 54), (30, 31, 34))
    label(sheet, title, (14, 12), 28, (240, 240, 240))
    for r, cw in enumerate(('White', 'Black')):
        y0 = 54 + r * (h + pad)
        label(sheet, f'{cw.upper()}', (14, y0 + 4), 24, (240, 200, 120))
        for c, (v, lab) in enumerate(views):
            sheet.paste(cells[cw][c], (c * w, y0 + pad - 20))
            label(sheet, lab, (c * w + w // 2 - 30, y0 + 2), 20, (200, 200, 200))
    return sheet


def pieces(gender):
    rows = {'male': ['Polo', 'Shorts', 'Socks', 'Shoes'], 'female': ['Polo', 'Skort', 'Socks', 'Shoes', 'Socks_ArmsCand', 'Shoes_ArmsCand']}[gender]
    views = ['front', 'back', 'left', 'right', 'top', 'bottom', 'q3f', 'q3b']
    vlab = {'front': 'FRONT', 'back': 'BACK', 'left': 'LEFT', 'right': 'RIGHT', 'top': 'TOP-DOWN', 'bottom': 'BOTTOM', 'q3f': '3/4 FRONT', 'q3b': '3/4 BACK'}
    sheets = {}
    for cw in ('White', 'Black'):
        im0 = Image.open(f'{RAW}piece_{gender}_{cw}_{rows[0]}_front.png')
        w, h = im0.size
        bgc = (102, 104, 110) if cw == 'White' else (205, 207, 211)
        sheet = Image.new('RGB', (w * 8, h * len(rows) + 50 + 30 * len(rows)), bgc)
        label(sheet, f'{gender.upper()} - {cw.upper()} - piece views (ortho)', (14, 10), 26, (240, 240, 240) if cw == 'White' else (20, 20, 20))
        for r, row in enumerate(rows):
            y0 = 50 + r * (h + 30)
            label(sheet, row.replace('_', ' '), (14, y0 + 2), 20, (235, 235, 235) if cw == 'White' else (60, 60, 60))
            for c, v in enumerate(views):
                im = Image.open(f'{RAW}piece_{gender}_{cw}_{row}_{v}.png').convert('RGB')
                sheet.paste(im, (c * w, y0 + 26))
                if r == 0:
                    label(sheet, vlab[v], (c * w + w // 2 - 40, y0 + 2), 18, (225, 225, 225) if cw == 'White' else (80, 80, 80))
        sheets[cw] = sheet
    return sheets


def closeups(gender):
    names = {'male': ['collar', 'placket', 'cuff', 'hem_waist', 'shorts_hem', 'shoe_side', 'shoe_front', 'sock_cuff'],
             'female': ['collar', 'placket', 'cuff', 'hem_waist', 'skort_hem', 'shoe_side', 'shoe_front', 'sock_cuff']}[gender]
    sheets = {}
    for cw in ('White', 'Black'):
        im0 = Image.open(f'{RAW}close_{gender}_{cw}_{names[0]}.png')
        w, h = im0.size
        sheet = Image.new('RGB', (w * 4, (h + 28) * 2 + 40), (30, 31, 34))
        label(sheet, f'{gender.upper()} - {cw.upper()} - no-logo close-ups', (14, 8), 24, (240, 240, 240))
        for i, n in enumerate(names):
            x, y = (i % 4) * w, 40 + (i // 4) * (h + 28)
            label(sheet, n.replace('_', ' '), (x + 8, y + 2), 18, (200, 200, 200))
            sheet.paste(Image.open(f'{RAW}close_{gender}_{cw}_{n}.png').convert('RGB'), (x, y + 24))
        sheets[cw] = sheet
    return sheets


def clearance(gender):
    views = ['front', 'back', 'right', 'q3']
    cells = [Image.open(f'{RAW}clear_{gender}_{v}.png').convert('RGB') for v in views]
    w, h = cells[0].size
    sheet = Image.new('RGB', (w * 4, h + 120), (30, 31, 34))
    label(sheet, f'{gender.upper()} - clearance heat map (kit on authority body; garment colour = distance to skin)', (14, 10), 24, (240, 240, 240))
    for i, c in enumerate(cells):
        sheet.paste(c, (i * w, 50))
    # legend
    y = 50 + h + 16
    for k, (txt, col) in enumerate((('< 1.5 mm', (242, 26, 26)), ('1.5 - 3 mm', (250, 140, 26)), ('3 - 6 mm', (250, 224, 51)), ('>= 6 mm', (64, 199, 89)))):
        x = 20 + k * 230
        ImageDraw.Draw(sheet).rectangle([x, y, x + 34, y + 26], fill=col)
        label(sheet, txt, (x + 44, y), 22, (230, 230, 230))
    st = json.load(open(f'{RAW}clear_{gender}.json'))
    msg = '   '.join(f"{k.replace('_White', '').replace('Kit_', '')}: min {v['min_mm']:+.1f} mm" for k, v in st.items())
    label(sheet, msg, (14, y + 40), 18, (190, 190, 190))
    return sheet


def sections(gender):
    data = json.load(open(f'{RAW}sections_{gender}.json'))
    levels = data['levels']
    cols = {'body': (210, 160, 125), 'polo': (80, 140, 255), 'bottom': (70, 200, 120), 'sock': (250, 190, 60), 'shoe': (200, 90, 220)}
    cw, ch = 520, 360
    sheet = Image.new('RGB', (cw * 4, ch * 2 + 80), (24, 25, 28))
    label(sheet, f'{gender.upper()} - horizontal sections: body (tan) vs garment layers (polo blue, bottom green, sock gold, shoe violet)', (14, 8), 22, (235, 235, 235))
    for i, z in enumerate(levels):
        x0, y0 = (i % 4) * cw, 44 + (i // 4) * (ch + 18)
        d = ImageDraw.Draw(sheet)
        d.rectangle([x0 + 4, y0, x0 + cw - 4, y0 + ch], outline=(70, 72, 78))
        # bounds from everything in this slice
        pts = [p for layer in data['layers'].values() for loop in layer[i] for p in loop['p']]
        if not pts:
            continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        s = min((cw - 40) / max(maxx - minx, 1e-3), (ch - 50) / max(maxy - miny, 1e-3))
        def tf(p):
            return (x0 + 20 + (p[0] - minx) * s, y0 + 20 + (maxy - p[1]) * s)     # +y (back) down? keep front (-y) at the bottom
        for name in ('body', 'bottom', 'polo', 'sock', 'shoe'):
            for loop in data['layers'][name][i]:
                q = [tf(p) for p in loop['p']]
                if len(q) > 2:
                    d.line(q + ([q[0]] if loop['closed'] else []), fill=cols[name], width=2 if name != 'body' else 3)
        label(sheet, f'z = {z:.2f} m', (x0 + 12, y0 + ch - 28), 18, (210, 210, 210))
    return sheet


def main():
    os.makedirs(OUT, exist_ok=True)
    onbody('male_authority', 'MALE - HeroBase_Male_Silhouette.blend (sha fd04bc28...) - standard kit, on body').save(OUT + 'ONBODY_Male.png')
    onbody('female_authority', 'FEMALE - HeroBase_Female.blend (sha 200dc3b9...) - polo + skort + authority-fit socks/sneakers').save(OUT + 'ONBODY_Female_Authority.png')
    onbody('female_arms_candidate', 'FEMALE - arms candidate (573ab443...) fit ref - polo + skort + arms-candidate-fit socks/sneakers').save(OUT + 'ONBODY_Female_ArmsCandidate.png')
    for g in ('male', 'female'):
        for cw, sh in pieces(g).items():
            sh.save(OUT + f'PIECES_{g.capitalize()}_{cw}.png')
        for cw, sh in closeups(g).items():
            sh.save(OUT + f'CLOSEUPS_NoLogo_{g.capitalize()}_{cw}.png')
        if os.path.exists(f'{RAW}clear_{g}_front.png'):
            clearance(g).save(OUT + f'CLEARANCE_{g.capitalize()}.png')
        if os.path.exists(f'{RAW}sections_{g}.json'):
            sections(g).save(OUT + f'SECTIONS_{g.capitalize()}.png')
    print(sorted(os.listdir(OUT)))


main()
