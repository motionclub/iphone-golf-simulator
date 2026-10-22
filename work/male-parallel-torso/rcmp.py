"""stack raking renders of several tags per view: python3.13 rcmp.py out.png view tag1,tag2,... [light a|b]"""
import sys
from PIL import Image
out, view, tags = sys.argv[1], sys.argv[2], sys.argv[3].split(','); lt = sys.argv[4] if len(sys.argv) > 4 else 'a'
ims = [Image.open(f'r/rake_{t}/{view}_{lt}.png').convert('RGB') for t in tags]
box = tuple(int(v) for v in sys.argv[5].split(',')) if len(sys.argv) > 5 else (0, 0, 1000, 1000)
ims = [i.crop(box) for i in ims]
s = Image.new('RGB', (sum(i.width for i in ims) + 6 * (len(ims) - 1), ims[0].height))
x = 0
for i in ims: s.paste(i, (x, 0)); x += i.width + 6
s.save(out); print(out, s.size)
