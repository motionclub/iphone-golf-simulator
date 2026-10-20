"""plate | FORM2 | candidates in the plate profile cameras (palm face-on).  python3 profcmp.py out.png tag1 [tag2 ...]"""
import sys, subprocess, os
from PIL import Image, ImageDraw
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3'
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
sys.path.insert(0, W)
from sheetlib import font
out = sys.argv[1]; tags = sys.argv[2:]
def render(t):
    cand = 'base' if t == 'base' else f'{W}/data/cand_{t}.npz'
    od = f'{W}/proof/it/{t}_plate'
    subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', f'{W}/baseline/HeroBase_Male_Silhouette.blend', '--python', f'{W}/platerender.py', '--', cand, od, 'left', 'right'], capture_output=True, text=True)
procs = []
import threading
ths = [threading.Thread(target=render, args=(t,)) for t in tags if os.environ.get('NORENDER') != '1' and not (t == 'base' and os.path.exists(f'{W}/proof/it/base_plate/left.png'))]
for th in ths: th.start()
for th in ths: th.join()
pl = Image.open(R + '/ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
boxes = {'LEFT profile (char L hand)': ((745, 165, 835, 235), 'left'), 'RIGHT profile (char R hand)': ((1045, 165, 1135, 235), 'right')}
S0 = 7
tiles = []
for nm, (box, view) in boxes.items():
    ims = [pl.crop(box)] + [Image.open(f'{W}/proof/it/{t}_plate/{view}.png').convert('RGB').crop(box) for t in tags]
    ims = [i.resize((i.width * S0, i.height * S0), Image.LANCZOS) for i in ims]
    w, h = ims[0].size
    t_ = Image.new('RGB', (w * len(ims) + 6 * (len(ims) - 1), h + 24), (20, 20, 22))
    for k, i in enumerate(ims): t_.paste(i, (k * (w + 6), 24))
    ImageDraw.Draw(t_).text((6, 4), nm + '   PLATE | ' + ' | '.join(tags), fill=(255, 230, 120), font=font(15))
    tiles.append(t_)
S = Image.new('RGB', (max(t.width for t in tiles), sum(t.height for t in tiles)))
y = 0
for t in tiles: S.paste(t, (0, y)); y += t.height
S.save(out); print(out, S.size)
