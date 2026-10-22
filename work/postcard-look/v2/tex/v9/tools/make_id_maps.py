"""make_id_maps.py <var_A dir> <out dir> : band-id albedo (white light band / black dark band, flat alpha .10) + flat normals for Fairway and Green, from the alpha of a sheen variant (Blender python)."""
import sys, os
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import numpy as np
import golf_look_textures as G
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
for nm in ('Fairway', 'Green'):
    c = G.read_png(os.path.join(src, nm + '_C.png'))
    band = (c[..., 3] > 0.17 * 255)
    rgb = np.where(band[..., None], np.uint8(235), np.uint8(20)) * np.ones((1, 1, 3), np.uint8)
    rgba = np.concatenate([rgb.astype(np.uint8), np.full(band.shape + (1,), int(0.10 * 255), np.uint8)], -1)
    G.write_png(os.path.join(out, nm + '_C.png'), rgba)
    flat = np.zeros(band.shape + (3,), np.uint8); flat[...] = (128, 128, 255)
    G.write_png(os.path.join(out, nm + '_N.png'), flat)
    print(nm, 'light share %.3f' % band.mean())
