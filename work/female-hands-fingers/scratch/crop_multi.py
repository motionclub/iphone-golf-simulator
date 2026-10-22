from PIL import Image, ImageDraw
B = '../../ArtDir/hero/base_lock/'
multi = Image.open(B + 'female_multiangle_body.jpg').convert('RGB')
# panels (each ~320 wide): front 0-320, back 320-640, left profile 640-960, right profile 960-1280; row1 y 0-370, row2 370-720
crops = {
 'front_vL': (112, 170, 152, 230),   # character right hand in front panel
 'front_vR': (190, 170, 230, 230),
 'back_vL':  (430, 170, 470, 230),
 'back_vR':  (505, 170, 545, 230),
 'profL':    (760, 150, 820, 240),   # left profile panel hands region
 'profR':    (1060, 150, 1120, 240),
 'q3FL_vL':  (112, 540, 152, 600),
 'q3FL_vR':  (190, 540, 230, 600),
 'q3FR_vL':  (425, 540, 465, 600),
 'q3FR_vR':  (505, 540, 545, 600),
 'q3BL_vL':  (735, 540, 775, 600),
 'q3BL_vR':  (810, 540, 850, 600),
 'q3BR_vL':  (1040, 540, 1080, 600),
 'q3BR_vR':  (1115, 540, 1155, 600),
}
sc = 8
tiles = []
for k, b in crops.items():
    c = multi.crop(b).resize(((b[2]-b[0])*sc, (b[3]-b[1])*sc), Image.LANCZOS)
    d = ImageDraw.Draw(c); d.text((4,4), k, fill=(255,220,0)); tiles.append(c)
# row layout: 7 per row
rows = [tiles[:5], tiles[5:10], tiles[10:]]
Wm = max(sum(t.width+6 for t in r) for r in rows); Hm = sum(max(t.height for t in r)+6 for r in rows)
S = Image.new('RGB', (Wm, Hm), (20,20,24)); y = 0
for r in rows:
    x = 0
    for t in r:
        S.paste(t, (x, y)); x += t.width + 6
    y += max(t.height for t in r) + 6
S.save('proof/ref_plate_hands_multi_8x.png'); print(S.size)
