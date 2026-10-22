import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import lab
gl = lab.gl
mult = float(sys.argv[1]) if len(sys.argv) > 1 else 1.1
ss = int(sys.argv[2]) if len(sys.argv) > 2 else 1
if len(sys.argv) > 3:
    gl.LAVA_P.update(json.loads(sys.argv[3]))
d = gl.mat_lava(1024, 1201, ss)
C = lab.u8(d['C']); E = lab.u8(d['E'])
game = lab.lava_game(C, E, (mult,) * 3)
st = lab.lava_stats(game)
print('GAME  ', {k: (tuple(int(x) for x in v) if isinstance(v, tuple) else round(v, 3)) for k, v in st.items()})
print('STILL ', lab.STILL_LAVA)
Ef = E.astype(np.float32) / 255
print('E max texel', E.reshape(-1, 3).max(0), 'E mean lum %.3f' % gl.lum(Ef).mean())
