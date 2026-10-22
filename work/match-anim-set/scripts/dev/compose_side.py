"""PIL: put the annotated behind-court frame and the racket-side frame next to each other:  python3 compose_side.py <hero> <side_frames_dir> <out_dir>"""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, '..', '..'))
tag, side_dir, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out_dir, exist_ok=True)
CLIPS = ['ReadyIdle', 'SplitToForehand', 'SplitToBackhand', 'RecoverCenter', 'Forehand', 'ForehandOpen', 'ForehandWide', 'ForehandShort',
         'Backhand', 'BackhandWide', 'SliceApproach', 'Serve', 'Return', 'VolleyForehand', 'VolleyBackhand', 'Overhead']
meta = json.load(open(f'{WORK}/data/bake_{tag}.json'))['clips']
n = 0
for c in CLIPS:
    for fr in range(meta[c]['frames']):
        a = Image.open(f'{WORK}/proof/_frames_annotated/{tag}/{n:04d}.png').convert('RGB')
        b = Image.open(f'{side_dir}/{c}_{fr:03d}.png').convert('RGB').resize(a.size)
        d = ImageDraw.Draw(b)
        d.rectangle([0, 0, b.size[0], 30], fill=(20, 22, 26))
        d.text((8, 8), 'racket-hand side', fill=(235, 235, 235))
        im = Image.new('RGB', (a.size[0] * 2, a.size[1]))
        im.paste(a, (0, 0)); im.paste(b, (a.size[0], 0))
        im.save(f'{out_dir}/{n:04d}.png')
        n += 1
print('COMPOSED', tag, n)
