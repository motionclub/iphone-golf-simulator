"""integration preview (UNOFFICIAL): FORM3 torso delta merged onto the arms chat's candidate (torso+limbs+arms, limbs vertex order).
Renders full-body views and the armpit seam, FORM2-preview vs FORM3-preview, soft(plate-fit light) + mirror stripes."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from board3 import *
HERE_ = HERE
A = HERE_ + '/../female-arms-form2/export/HeroBase_Female_arms_candidate.blend'
F2P = HERE_ + '/../female-torso-form2/export/PREVIEW_form2_torso_plus_limbs_plus_arms_UNOFFICIAL.blend'
F3P = HERE_ + '/export/PREVIEW_form3_torso_plus_limbs_plus_arms_UNOFFICIAL.blend'
MC = 'matcap:' + HERE_ + '/tools/matcap_platefit_g22.png'


def rend(blend, tag, look, shots):
    spec = {"coords": None, "out": f"{HERE_}/proof/scratch/{tag}", "shots": shots, "look": look}
    r = subprocess.run([BL, '-b', blend, '--python', HERE_ + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
    assert 'RENDER_OK' in r.stdout, r.stdout[-500:]
    return {s['name']: f"{HERE_}/proof/scratch/{tag}_{s['name']}.png" for s in shots}


full = [dict(name=n, yaw=y, xc=0.0, zc=1.10, w=0.95, res=[520, 700]) for n, y in (('front', 0), ('q3F', -22), ('side', -90), ('q3B', -158), ('back', 180))]
pit = [dict(name=n, yaw=y, xc=0.13, zc=1.20, w=0.26, res=[520, 520]) for n, y in (('front', 0), ('y25', -25), ('y-25', 25))]
rows = []
labs = []
for tag, bl, lab in (('p2', F2P, 'FORM2 torso + limbs + arms (preview)'), ('p3', F3P, 'FORM3 torso + limbs + arms (preview)')):
    f = rend(bl, tag + '_full', MC, full)
    rows.append(strip([bgcomp(f[s['name']]) for s in full], [lab if i == 0 else s['name'] for i, s in enumerate(full)], scale=0.8))
W = Image.new('RGB', (rows[0].width, rows[0].height * 2)); W.paste(rows[0], (0, 0)); W.paste(rows[1], (0, rows[0].height))
banner(W, 'INTEGRATION PREVIEW (UNOFFICIAL): FORM3 delta merged onto the arms chat candidate (torso + limbs + arms)', 'Preview only - nothing installed. Merge needs --force because the arms candidate still holds chat-7 torso positions (README_MERGE.md).').save(HERE_ + '/proof/09_merged_preview_torso_limbs_arms_UNOFFICIAL.png')
rows = []
for tag, bl, lab in (('p2', F2P, 'FORM2 preview'), ('p3', F3P, 'FORM3 preview')):
    soft = rend(bl, tag + '_pit', MC, pit)
    stripe = rend(bl, tag + '_pitS', 'matcap:check_reflection_vertical.exr', pit)
    rows.append(strip([bgcomp(soft[s['name']]) for s in pit] + [bgcomp(stripe[s['name']]) for s in pit], [f'{lab} R-armpit soft {s["name"]}' for s in pit] + [f'{lab} R-armpit stripes {s["name"]}' for s in pit], scale=0.55))
W = Image.new('RGB', (rows[0].width, rows[0].height * 2)); W.paste(rows[0], (0, 0)); W.paste(rows[1], (0, rows[0].height))
banner(W, 'ARMPIT SEAM CHECK (UNOFFICIAL merged preview): FORM2 vs FORM3 torso next to the arms chat arm', 'Soft = plate-fitted light, stripes = mirror matcap. A visible step/crease at the junction would show as a break in the stripes.').save(HERE_ + '/proof/10_armpit_seam_check_merged.png')
print('merged proofs written')
