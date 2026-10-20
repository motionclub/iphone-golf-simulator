"""Reference-vs-build comparison sheets (system python + Pillow).  python3 compose_refs.py"""
import os
from PIL import Image, ImageDraw, ImageFont

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/'
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/kits/standard_wb/'
RAW = W + 'proof/raw/'
OUT = W + 'proof/'


def font(sz):
    for p in ('/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/Supplemental/Arial.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def label(img, text, xy, sz=20, fill=(235, 235, 235)):
    ImageDraw.Draw(img).text(xy, text, font=font(sz), fill=fill)


def fit_h(im, h):
    return im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)


def fit_w(im, w):
    return im.resize((w, max(1, int(im.height * w / im.width))), Image.LANCZOS)


REF = {k: Image.open(R + k).convert('RGB') for k in ('01_white_full_turnaround.jpg', '02_black_full_turnaround.jpg', '03_white_pieces_ortho.jpg',
                                                      '04_black_pieces_ortho.jpg', '05_shoes_socks_wb.jpg')}

# crops (x0, y0, x1, y1) in the 1280x720 reference sheets: male / female front, side, back
FULL = {
    ('White', 'male'): [('01_white_full_turnaround.jpg', (28, 10, 200, 285)), ('01_white_full_turnaround.jpg', (425, 10, 525, 285)), ('01_white_full_turnaround.jpg', (555, 10, 725, 285))],
    ('White', 'female'): [('01_white_full_turnaround.jpg', (28, 298, 200, 565)), ('01_white_full_turnaround.jpg', (425, 298, 525, 565)), ('01_white_full_turnaround.jpg', (555, 298, 725, 565))],
    ('Black', 'male'): [('02_black_full_turnaround.jpg', (68, 5, 268, 310)), ('02_black_full_turnaround.jpg', (590, 5, 700, 310)), ('02_black_full_turnaround.jpg', (305, 5, 505, 310))],
    ('Black', 'female'): [('02_black_full_turnaround.jpg', (72, 312, 262, 610)), ('02_black_full_turnaround.jpg', (590, 312, 700, 610)), ('02_black_full_turnaround.jpg', (312, 312, 502, 610))],
}


def full_sheet(gender, tag_body):
    H = 560
    rows = []
    for cw in ('White', 'Black'):
        cells = []
        for (fn, box), vname in zip(FULL[(cw, gender)], ('front', 'left', 'back')):
            ref = fit_h(REF[fn].crop(box), H)
            mine = fit_h(Image.open(f'{RAW}onbody_{tag_body}_{cw}_{vname}.png').convert('RGB'), H)
            cells += [(ref, f'REF {cw} {vname}'), (mine, f'BUILD {cw} {vname}')]
        rows.append(cells)
    wmax = max(sum(c[0].width for c in r) for r in rows)
    sheet = Image.new('RGB', (wmax, (H + 36) * 2 + 50), (30, 31, 34))
    label(sheet, f'{gender.upper()} - reference turnaround (01/02) vs staged build, same views', (14, 10), 24)
    for ri, cells in enumerate(rows):
        x, y = 0, 50 + ri * (H + 36)
        for im, lab in cells:
            sheet.paste(im, (x, y + 30))
            label(sheet, lab, (x + 8, y + 4), 18, (230, 200, 120) if lab.startswith('REF') else (180, 220, 255))
            x += im.width
    return sheet


def pieces_sheet(gender, cw, rows):
    """stack: reference piece row (03/04) above our piece views, same 8-view order."""
    ref = REF['03_white_pieces_ortho.jpg' if cw == 'White' else '04_black_pieces_ortho.jpg']
    ref_rows = {'polo': (0, 0, 1280, 255), 'shorts': (0, 258, 1280, 470), 'skort': (0, 474, 1280, 700)}
    names = {'polo': 'Polo', 'shorts': 'Shorts', 'skort': 'Skort'}
    views = ['front', 'back', 'left', 'right', 'top', 'bottom', 'q3f', 'q3b']
    out_w = 2880
    blocks = []
    for key in rows:
        r = fit_w(ref.crop(ref_rows[key]), out_w)
        im0 = Image.open(f'{RAW}piece_{gender}_{cw}_{names[key]}_front.png')
        cw_, ch_ = im0.size
        mine = Image.new('RGB', (cw_ * 8, ch_), (102, 104, 110) if cw == 'White' else (205, 207, 211))
        for i, v in enumerate(views):
            mine.paste(Image.open(f'{RAW}piece_{gender}_{cw}_{names[key]}_{v}.png').convert('RGB'), (i * cw_, 0))
        blocks.append((names[key], r, mine))
    h = sum(b[1].height + b[2].height + 70 for b in blocks) + 50
    sheet = Image.new('RGB', (out_w, h), (30, 31, 34))
    label(sheet, f'{gender.upper()} - {cw.upper()} - reference piece sheet ({"03" if cw == "White" else "04"}) over staged build (same view order)', (14, 10), 24)
    y = 50
    for nm, r, mine in blocks:
        label(sheet, f'{nm}: REFERENCE', (14, y + 2), 18, (230, 200, 120))
        sheet.paste(r, (0, y + 26))
        y += 26 + r.height
        label(sheet, f'{nm}: BUILD', (14, y + 2), 18, (180, 220, 255))
        sheet.paste(mine, (0, y + 26))
        y += 26 + mine.height + 18
    return sheet.crop((0, 0, out_w, y))


def shoes_sheet(gender, tag_set):
    """05 shoes/socks reference (white top half, black bottom half) over our sneaker + sock piece views."""
    ref = REF['05_shoes_socks_wb.jpg']
    views = ['front', 'back', 'left', 'right', 'top', 'bottom', 'q3f', 'q3b']
    out_w = 2880
    sheets = {}
    for cw, box in (('White', (0, 0, 1280, 355)), ('Black', (0, 360, 1280, 720))):
        r = fit_w(ref.crop(box), out_w)
        parts = [('Shoes' + tag_set, 'Sneakers'), ('Socks' + tag_set, 'Socks')]
        mine_rows = []
        for nm, lab in parts:
            im0 = Image.open(f'{RAW}piece_{gender}_{cw}_{nm}_front.png')
            cw_, ch_ = im0.size
            row = Image.new('RGB', (cw_ * 8, ch_), (102, 104, 110) if cw == 'White' else (205, 207, 211))
            for i, v in enumerate(views):
                row.paste(Image.open(f'{RAW}piece_{gender}_{cw}_{nm}_{v}.png').convert('RGB'), (i * cw_, 0))
            mine_rows.append((lab, row))
        h = r.height + sum(m[1].height + 30 for m in mine_rows) + 110
        sheet = Image.new('RGB', (out_w, h), (30, 31, 34))
        label(sheet, f'{gender.upper()} - {cw.upper()} - reference shoes + socks (05) vs staged build (three-stripe side detail of the ref intentionally NOT copied)', (14, 10), 24)
        label(sheet, 'REFERENCE', (14, 46), 18, (230, 200, 120))
        sheet.paste(r, (0, 70))
        y = 70 + r.height + 14
        for lab, row in mine_rows:
            label(sheet, f'BUILD: {lab}', (14, y), 18, (180, 220, 255))
            sheet.paste(row, (0, y + 24))
            y += 24 + row.height + 12
        sheets[cw] = sheet.crop((0, 0, out_w, y))
    return sheets


def main():
    full_sheet('male', 'male_authority').save(OUT + 'REF_VS_BUILD_Turnaround_Male.png')
    full_sheet('female', 'female_authority').save(OUT + 'REF_VS_BUILD_Turnaround_Female.png')
    for cw in ('White', 'Black'):
        pieces_sheet('male', cw, ['polo', 'shorts']).save(OUT + f'REF_VS_BUILD_Pieces_Male_{cw}.png')
        pieces_sheet('female', cw, ['polo', 'skort']).save(OUT + f'REF_VS_BUILD_Pieces_Female_{cw}.png')
    for g, tag in (('male', ''), ('female', '')):
        for cw, sh in shoes_sheet(g, tag).items():
            sh.save(OUT + f'REF_VS_BUILD_ShoesSocks_{g.capitalize()}_{cw}.png')
    print(sorted(f for f in os.listdir(OUT) if f.startswith('REF_VS')))


main()
