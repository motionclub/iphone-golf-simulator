# tools/gate.py <dir>...: dark-pixel share (luma < 40) of each still, LOD1/LOD2 minus CHARACTER_LOD=0, per hero x view. Gate: excess <= 0.5 % of the frame.
import sys, numpy as np
from PIL import Image
for d in sys.argv[1:]:
    worst = 0; rows = []
    for h in ['BowlingM', 'BowlingF', 'TennisM', 'TennisF']:
        for v in ['face', 'body', 'side']:
            def dark(t):
                a = np.asarray(Image.open(f'{d}/{h}_{v}_{t}.jpg').convert('RGB')).astype(float)
                return ((.2126 * a[..., 0] + .7152 * a[..., 1] + .0722 * a[..., 2]) < 40).mean() * 100
            off = dark('off'); e1 = dark('L1') - off; e2 = dark('L2') - off; worst = max(worst, e1, e2)
            rows.append(f'  {h:9s} {v:5s} off {off:5.2f}%  L1 {e1:+6.2f}  L2 {e2:+6.2f}')
    print(d, f'worst excess {worst:.2f}% ->', 'PASS' if worst <= .5 else 'FAIL'); print('\n'.join(rows))
