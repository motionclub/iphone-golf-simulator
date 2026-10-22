"""Render saved garment npz files on a body: python view_garment.py -- <gender> <names comma> <colorway> <preset> [outprefix]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy
from kitlib import *
import scene_utils as su

args = sys.argv[sys.argv.index('--') + 1:]
gender, names, colorway, preset = args[:4]
out = args[4] if len(args) > 4 else f'{WORK}/tmp/view_{gender}_{colorway}_{preset}'
bodyfile = {'male': MALE_BLEND, 'female': FEMALE_BLEND, 'female_auth': FEMALE_BLEND}[gender]
if len(args) > 5:
    bodyfile = args[5]
bpy.ops.wm.open_mainfile(filepath=bodyfile)
bo = [o for o in bpy.data.objects if o.name.startswith('Body')][0]
Vb, Fb = mesh_arrays(bo)
gs = []
for nm in names.split(','):
    d = np.load(f'{WORK}/data/{nm}_{gender}.npz')
    gs.append((nm, d['V'], d['F'], d['N'], d['M']))
PRESETS = {
    'full': dict(views=(('front', 0, 3), ('q3', 38, 4), ('side', 90, 3), ('back', 180, 3)), target=(0, -0.05, 0.86), dist=6.4, lens=105, res=(520, 760)),
    'collar': dict(views=(('front', 0, 8), ('q3', 35, 12), ('side', 90, 6), ('back', 180, 6)), target=(0, -0.04, 1.36), dist=1.5, lens=85, res=(640, 640)),
    'upper': dict(views=(('front', 0, 5), ('q3', 38, 8), ('side', 90, 4), ('back', 180, 5)), target=(0, -0.04, 1.2), dist=3.2, lens=85, res=(640, 760)),
    'lower': dict(views=(('front', 0, 3), ('q3', 38, 4), ('side', 90, 3), ('back', 180, 3)), target=(0, -0.05, 0.62), dist=3.6, lens=85, res=(640, 760)),
    'feet': dict(views=(('front', 0, 6), ('q3', 38, 10), ('side', 90, 5), ('back', 180, 6)), target=(0, -0.04, 0.18), dist=1.7, lens=85, res=(640, 640)),
    'hip': dict(views=(('front', 0, 8), ('q3', 35, 12), ('side', 90, 6), ('back', 180, 8)), target=(0, -0.0, 0.84), dist=2.2, lens=85, res=(640, 640)),
    'hand': dict(views=(('front', 0, 4), ('q3', 50, 8), ('side', 90, 4)), target=(0.2, 0.0, 0.76), dist=1.0, lens=85, res=(640, 640)),
    'sleeve': dict(views=(('q3', 55, 8), ('front', 0, 4)), target=(0.3, -0.04, 1.18), dist=1.6, lens=85, res=(640, 640)),
}
pr = PRESETS[preset]
lift = 0.0285 if gender == 'male' else (0.0235 if gender == 'female_auth' else 0.0245)
lift = lift if 'shoe' in names else 0.0
su.preview_garments((Vb, Fb), gs, out, colorway=colorway, views=pr['views'], res=pr['res'], target=pr['target'], dist=pr['dist'], lens=pr['lens'], samples=48, lift=lift)
