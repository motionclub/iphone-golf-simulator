import sys, json
from PIL import Image, ImageDraw
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3'
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
sys.path.insert(0, W)
from sheetlib import font
F = W + '/proof/final/'; I = W + '/proof/it/'
a = json.load(open(W + '/data/allmetrics_FORM2.json')); b = json.load(open(W + '/data/allmetrics_final.json'))
sn = json.load(open(W + '/data/sil_native.json')); k = list(sn.keys()); sb = sn[[x for x in k if 'before' in x][0]]; sa = sn[[x for x in k if 'after' in x][0]]
bald = Image.open(R + '/ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB'); multi = Image.open(R + '/ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
ROIS = [('bald front, char R hand', bald, 'bald_front', (100, 300, 205, 395)), ('bald front, char L hand', bald, 'bald_front', (500, 300, 605, 395)),
        ('bald back, char L hand', bald, 'bald_back', (670, 300, 775, 395)), ('bald back, char R hand', bald, 'bald_back', (1060, 300, 1165, 395)),
        ('multi front, R hand', multi, 'sheet_front', (45, 160, 125, 225)), ('multi front, L hand', multi, 'sheet_front', (250, 160, 330, 225)),
        ('multi back, L hand', multi, 'sheet_back', (355, 160, 435, 225)), ('multi back, R hand', multi, 'sheet_back', (545, 160, 625, 225))]
sc = 4; tiles = []
for name, plate, view, roi in ROIS:
    ims = [plate.crop(roi), Image.open(f'{I}/base_plate/{view}.png').convert('RGB').crop(roi), Image.open(f'{I}/final_plate/{view}.png').convert('RGB').crop(roi)]
    ims = [i.resize((i.width * sc, i.height * sc), Image.LANCZOS) for i in ims]
    w = ims[0].width; h = ims[0].height
    t = Image.new('RGB', (w * 3 + 12, h + 22), (20, 20, 22))
    for k_, i in enumerate(ims): t.paste(i, (k_ * (w + 6), 22))
    ImageDraw.Draw(t).text((4, 3), name + '   |  PLATE  |  FORM2  |  FORM3', fill=(255, 230, 120), font=font(13)); tiles.append(t)
cw = max(t.width for t in tiles); ch = max(t.height for t in tiles)
S3 = Image.new('RGB', (2 * cw, 4 * ch), (20, 20, 22))
for i, t in enumerate(tiles): S3.paste(t, ((i % 2) * cw, (i // 2) * ch))
def header(width, lines):
    im = Image.new('RGB', (width, 16 + 30 * len(lines)), (14, 14, 16)); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines): d.text((12, 10 + i * 30), l, fill=(255, 230, 120) if i == 0 else (225, 225, 225), font=font(24 if i == 0 else 17))
    return im
def fit(im, w): return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
sb_ = Image.open(I + 'base_silov.png').convert('RGB'); sa_ = Image.open(I + 'final_silov.png').convert('RGB')
lines = ['PLATE | FORM2 | FORM3 at the locked plate cameras (8 hand ROIs), then silhouette overlays (pink = mesh only, green = plate only, grey = both)',
         'hand-ROI XOR (8 ROIs, my rasteriser): FORM2 %d -> FORM3 %d px (gate: not worse than FORM2).  Blender-native bald silhouette XOR/union (gate <= 5.0%%): front %.2f%% -> %.2f%%, back %.2f%% -> %.2f%%' % (
            a['roi_xor_total'], b['roi_xor_total'], sb['bald_front']['pct'], sa['bald_front']['pct'], sb['bald_back']['pct'], sa['bald_back']['pct']),
         'the plates disagree front vs back on the thumb (front plate shows it, back plate hides it) and are edge-on to the palm, so breadth/length are judged on the profile + 3/4 sheets as well; Adnan eye is final']
W0 = S3.width
S = Image.new('RGB', (W0, 0))
parts = [header(W0, lines), S3, header(W0, ['FORM2 silhouette overlays']), fit(sb_, W0), header(W0, ['FORM3 silhouette overlays']), fit(sa_, W0)]
H = sum(p.height for p in parts); S = Image.new('RGB', (W0, H), (18, 18, 20)); y = 0
for p in parts: S.paste(p, (0, y)); y += p.height
S.save(F + '03d_hands_form3_plate_silhouette.png'); print(S.size)
