"""Side-by-side: chosen-look reference racket (00_hero_pick, left racket) vs our ortho front render, same racket length.
python3 compare_ref.py <our_front_ortho.png> <out.png> [px_per_m_of_our_render]"""
import sys
from PIL import Image, ImageDraw

ref = Image.open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/kits/racket_classic/00_hero_pick.jpg').convert('RGB')
ours = Image.open(sys.argv[1]).convert('RGB')
out = sys.argv[2]
ppm = float(sys.argv[3]) if len(sys.argv) > 3 else 1750.0
# reference left racket: head top y=28, butt bottom y=678 (650 px) -> our racket length in px
L_px = 0.688 * ppm
k = L_px / 650.0
rc = ref.crop((200, 0, 600, 720))
rc = rc.resize((int(rc.width * k), int(rc.height * k)), Image.LANCZOS)
H = max(rc.height, ours.height)
canvas = Image.new('RGB', (rc.width + ours.width + 10, H), (30, 30, 30))
canvas.paste(rc, (0, 0))
canvas.paste(ours, (rc.width + 10, 0))
canvas.save(out)
print(canvas.size, 'ref top at', 28 * k, 'ref bottom at', 678 * k)
