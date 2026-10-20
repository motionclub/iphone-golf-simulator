import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
exec(open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/clay_hard.py').read().split("for az, el, tag in")[0])
for az, el, tag in ((0, 0, 'f'), (35, 0, 'q'), (0, -35, 'under'), (60, 0, 'q60'), (0, 25, 'hi'), (90, 0, 's')):
    H.shot(out / f'{name}_{tag}.png', tgt, az, el, scale, (800, 800))
print('nose done')
