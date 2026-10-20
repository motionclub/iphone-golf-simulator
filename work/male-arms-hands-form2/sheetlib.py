from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
def font(sz):
    for p in ('/System/Library/Fonts/Helvetica.ttc','/System/Library/Fonts/SFNS.ttf','/Library/Fonts/Arial.ttf'):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
def sheet(folder, names, out, cols=4, size=420, title=None, labels=True):
    folder = Path(folder); rows = (len(names)+cols-1)//cols
    top = 34 if title else 0
    S = Image.new('RGB', (cols*size, rows*size+top), (20,20,22)); d = ImageDraw.Draw(S)
    if title: d.text((8,6), title, fill=(255,230,120), font=font(20))
    for i, n in enumerate(names):
        im = Image.open(folder/f'{n}.png').convert('RGB').resize((size,size), Image.LANCZOS)
        S.paste(im, ((i%cols)*size, (i//cols)*size+top))
        if labels: d.text(((i%cols)*size+6, (i//cols)*size+top+4), n, fill=(255,255,255), font=font(15))
    S.save(out); return out
