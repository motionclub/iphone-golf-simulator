"""Quick review grid: target crop + match render (+ turn_030) per asset. python3 review.py out.jpg Name ..."""
import sys, json
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent))
from sheets import panel, fit, ROOT
out, names = sys.argv[1], sys.argv[2:]
T = 300
tiles = []
for n in names:
    m = json.loads((ROOT / 'proof/metrics' / f'{n}.json').read_text())
    t = Image.new('RGB', (T * 3, T + 18), '#222')
    tg = ROOT / 'targets' / f"{m.get('target') or n}.jpg"
    if m.get('target') and tg.exists():
        im = fit(Image.open(tg).convert('RGB'), T, T); t.paste(im, ((T - im.width) // 2, 18 + (T - im.height) // 2))
    t.paste(panel(ROOT / 'renders' / n / 'match.png', T, T, m['course']), (T, 18))
    t.paste(panel(ROOT / 'renders' / n / 'turn_210.png', T, T, m['course']), (2 * T, 18))
    ImageDraw.Draw(t).text((4, 3), n, fill='white')
    tiles.append(t)
cols = 2
rows = (len(tiles) + cols - 1) // cols
S = Image.new('RGB', (T * 3 * cols, (T + 18) * rows), 'black')
for k, t in enumerate(tiles):
    S.paste(t, ((k % cols) * T * 3, (k // cols) * (T + 18)))
S.save(out, quality=82)
