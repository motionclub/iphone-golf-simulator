#!/bin/bash
# GATE LIB_PILLAR_COURSES_NOT_STACKED: the pillar wall of hole 10 at the approach camera must not read as stacked horizontal courses (Blender EEVEE crop at 3x, NOT Game view).
# measure = std / max of the first difference of the per-row mean luminance over the wall body (a horizontal seam = a row-to-row step); control = the hole fixer's stage (built on the old lib).
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; H=$R/work/postcard-look/v2/libs_r2; B=/Applications/Blender.app/Contents/MacOS/Blender
cd $R
$B -b --factory-startup --python $H/tools/crop_render.py -- $R/work/postcard-look/v2/hole10/stage/hole_10.blend $R/work/postcard-look/v2/hole10/landmarks.json hole10_approach $H/img/pillar_ctrl.png 230 250 670 380 3 16 > /dev/null 2>&1
$B -b --factory-startup --python $H/tools/crop_render.py -- $H/h10/hole_10.blend $R/work/postcard-look/v2/hole10/landmarks.json hole10_approach $H/img/pillar_new.png 230 250 670 380 3 16 > /dev/null 2>&1
python3 - <<PY
from PIL import Image
import numpy as np
def m(p):
    im = np.array(Image.open(p).convert('L')).astype(float)[100:320, 150:1180]
    d = np.abs(np.diff(im.mean(1)))
    return float(d.std()), float(d.max()), float(np.abs(np.diff(im, axis=1)).mean() / np.abs(np.diff(im, axis=0)).mean())
c, n = m("$H/img/pillar_ctrl.png"), m("$H/img/pillar_new.png")
ok = n[0] <= 0.6 and n[1] <= 4.0 and c[0] > 0.6
print("GATE: LIB_PILLAR_COURSES_NOT_STACKED %s - row-to-row luminance step of the pillar wall (3x Blender crop, approach camera): new std %.3f max %.2f (limits 0.6 / 4.0), vertical-streak ratio dI/dx : dI/dy %.2f; CONTROL (stage built on the start-of-round lib): std %.3f max %.2f ratio %.2f -> %s" % ("PASS" if ok else "FAIL", n[0], n[1], n[2], c[0], c[1], c[2], "detected" if c[0] > 0.6 else "BLIND"))
PY
