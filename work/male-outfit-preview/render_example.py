"""Renders for the male outfit example (run in the live Blender after build_example.py)."""
import sys, importlib
from pathlib import Path
import bpy

ROOT = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
W = ROOT / 'work/male-outfit-preview'
R = W / 'r'
if str(W) not in sys.path:
    sys.path.insert(0, str(W))
import render_setup as rs, scene_ops as so, outfit_parts as op, shader_zones as sz
for m in (rs, so, op):
    importlib.reload(m)

BODY_C = (0, -0.05, 0.86)
HEAD_C = (0, -0.06, 1.56)


def body_view(path, az=0, el=4, res=(700, 1000), dist=6.4, lens=105):
    rs.shot(path, BODY_C, az, el, dist=dist, lens=lens, res=res)


def head_view(path, az=0, el=2, res=(700, 700), dist=1.25, lens=85):
    rs.shot(path, HEAD_C, az, el, dist=dist, lens=lens, res=res)


def turnaround(tag, res=(640, 920), samples=64):
    bpy.context.scene.eevee.taa_render_samples = samples
    for nm, az, el in (('front', 0, 3), ('q3', 38, 4), ('side', 90, 3), ('back', 180, 3), ('q3b', 218, 4)):
        body_view(str(R / f'{tag}_{nm}.png'), az=az, el=el, res=res)


def expressions(tag, res=(640, 640)):
    out = []
    for ex in so.EXPRS:
        so.show_expression(ex)
        p = str(R / f'{tag}_{ex}.png')
        head_view(p, az=0, el=1, res=res)
        out.append(p)
    so.show_expression('happy')
    return out


def final_set(out_dir, samples=96):
    """Everything the example sheets need.  Returns dict of written paths."""
    import json
    sc = bpy.context.scene
    sc.eevee.taa_render_samples = samples
    D = Path(out_dir)
    D.mkdir(parents=True, exist_ok=True)
    made = {}
    # hero (cheer face, 3/4)
    so.show_expression('cheer')
    p = str(D / 'hero_q3.png')
    body_view(p, az=30, el=4, res=(1400, 2000), dist=5.9)
    made['hero_q3'] = p
    # turnaround in the happy face
    so.show_expression('happy')
    for nm, az in (('front', 0), ('q3', 38), ('side', 90), ('back', 180), ('q3b', 218)):
        p = str(D / f'turn_{nm}.png')
        body_view(p, az=az, el=3, res=(800, 1150), dist=6.3)
        made['turn_' + nm] = p
    # expressions (head close-ups)
    for ex in so.EXPRS:
        so.show_expression(ex)
        p = str(D / f'expr_{ex}.png')
        head_view(p, az=0, el=1, res=(900, 900), dist=1.15)
        made['expr_' + ex] = p
    so.show_expression('happy')
    # expression profile views for happy/cheer
    for ex in so.EXPRS:
        so.show_expression(ex)
        p = str(D / f'exprq3_{ex}.png')
        head_view(p, az=32, el=3, res=(900, 900), dist=1.15)
        made['exprq3_' + ex] = p
    so.show_expression('happy')
    # colourways
    for cw in op.COLORWAYS:
        op.recolor(cw)
        sz.set_colors('Outfit_HairCap', {'base': op.COLORWAYS[cw]['Hair']['base']})
        so.show_expression('cheer' if cw != 'coral_court' else 'happy')
        p = str(D / f'cw_{cw}.png')
        body_view(p, az=28, el=4, res=(800, 1150), dist=6.3)
        made['cw_' + cw] = p
    op.recolor('coral_court')
    sz.set_colors('Outfit_HairCap', {'base': op.COLORWAYS['coral_court']['Hair']['base']})
    so.show_expression('happy')
    return made
