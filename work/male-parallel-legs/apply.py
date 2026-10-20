"""blender -b --factory-startup --python apply.py -- <V.npy> <out.blend>"""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-legs')
from leglib import *
a=sys.argv[sys.argv.index('--')+1:]
write_blend(np.load(a[0]),a[1]); print('APPLIED',a[1])
