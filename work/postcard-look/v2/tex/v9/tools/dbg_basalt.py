import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import numpy as np
import golf_look_textures as G
d = G.mat_basalt(1024, 1101)
print('net stats', G._NET_STATS)
E = d['E']; print('E max', E.max(0).max(0), 'E>0.2 share', (E.max(2) > 0.2).mean())
