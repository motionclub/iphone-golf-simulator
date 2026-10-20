from PIL import Image, ImageDraw, ImageOps, ImageEnhance
B = '../../ArtDir/hero/base_lock/'
multi = Image.open(B + 'female_multiangle_body.jpg').convert('RGB')
S2 = 1.7039/288.5
def prof(anchor_x, x0, x1, y0, y1, K, name, flip=False):
    im = multi.crop((x0, y0, x1, y1)).resize(((x1-x0)*K, (y1-y0)*K), Image.BICUBIC)
    im = ImageOps.autocontrast(im.convert('L'), cutoff=1).convert('RGB')
    im = ImageEnhance.Contrast(im).enhance(1.6)
    d = ImageDraw.Draw(im)
    for ycm in range(-10, 11):
        xp = (anchor_x + (ycm/100/S2) * (-1 if flip else 1) - x0)*K
        if 0 <= xp < im.width:
            d.line([(xp,0),(xp,im.height)], fill=(255,0,0) if ycm==0 else (255,170,0), width=1)
            d.text((xp+2,2), str(ycm), fill=(255,60,60))
    for zm in [0.66,0.68,0.70,0.72,0.74,0.76,0.78,0.80,0.82,0.84,0.86,0.88,0.90]:
        yp = (338.5 - zm/S2 - y0)*K
        if 0 <= yp < im.height:
            d.line([(0,yp),(im.width,yp)], fill=(0,170,255), width=1); d.text((2,yp-11), f'{zm:.2f}', fill=(0,120,255))
    im.save(name); print(name, im.size)
prof(791.5, 758, 830, 168, 240, 14, 'proof/ref_prof_left_zoom.png')
