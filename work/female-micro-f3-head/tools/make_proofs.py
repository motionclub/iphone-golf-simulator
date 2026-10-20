"""MicroF2 proof images + numeric tables from the final blend / mesh.  python3 make_proofs.py   (needs: renders/f1pl (F1 plate-camera renders), export/HeroBase_Female_MicroF2_head_STAGED.blend,
data/var_final.npz, data/var_A_asbuilt.npz).  Writes proof/*.png and data/final_tables.json"""
import sys, json, subprocess, shutil
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import fl, meshlib as ml, slices as sl, phi2, exp, geo
import make_final as mf
from plot2d import plot2d
ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
W2 = ROOT + 'work/female-micro-f3-head/'
B = '/Applications/Blender.app/Contents/MacOS/Blender'
STAGED = W2 + 'export/HeroBase_Female_MicroF2_head_STAGED.blend'
try: font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 26)
except Exception: font = ImageFont.load_default()
tables = {}


def run(*a): subprocess.run(list(a), check=True, capture_output=True)


# ------------------------------------------------------------------------------------------------ 1. plate | F1 | F2 lower-face BA at the plate cameras
(W2 + 'renders/final').__str__()
import os
os.makedirs(W2 + 'renders/final', exist_ok=True)
run(B, '-b', '--factory-startup', '--python', W2 + 'tools/ul.py', '--', STAGED, W2 + 'renders/final', 'front,left,right,q3L,q3R', 'F2')
run('python3', W2 + 'tools/ba_sheet.py', W2 + 'renders/f1pl', W2 + 'renders/final', W2 + 'proof/F2_lowerface_BA_plate_F1_F2.png', 'F1', 'F2')
# ------------------------------------------------------------------------------------------------ 2. chin close-ups (front, slightly from below, 3/4 from below, profile, under-chin)
os.makedirs(W2 + 'renders/chin', exist_ok=True)
VIEWS = 'c:0:0:0:-0.06:1.45:0.15:1000,c:0:-18:0:-0.06:1.445:0.15:1000,c:35:-14:-0.01:-0.06:1.45:0.15:1000,c:-35:-14:0.01:-0.06:1.45:0.15:1000,c:90:0:0:-0.05:1.45:0.15:1000,c:0:-38:0:-0.06:1.43:0.15:1000'
for T, blend in (('F1', W2 + 'start/F1_STAGED.blend'), ('F2', STAGED)):
    run(B, '-b', '--factory-startup', '--python', W2 + 'tools/ul.py', '--', blend, W2 + 'renders/chin', VIEWS, T)
src = Image.open(ROOT + 'ArtDir/hero/base_lock/female_head_detail.jpg').convert('RGB')
def plate_window(view, y0, z, half_m=0.075):
    h = half_m / fl.K; r = float(fl.rowz(z)); c = fl.CXF if view == 'front' else 653 + (y0 - fl.Y0) / fl.K
    return src.crop((int(c - h), int(r - h), int(c + h), int(r + h))).resize((1000, 1000), Image.LANCZOS)
names = ['c_0_0_0_-0.06_1.45_0.15_1000', 'c_0_-18_0_-0.06_1.445_0.15_1000', 'c_35_-14_-0.01_-0.06_1.45_0.15_1000', 'c_-35_-14_0.01_-0.06_1.45_0.15_1000', 'c_90_0_0_-0.05_1.45_0.15_1000', 'c_0_-38_0_-0.06_1.43_0.15_1000']
labels = ['front', 'front, slightly from below (up 18 deg)', '3/4 right, from below (14 deg)', '3/4 left, from below (14 deg)', 'profile', 'under-chin (up 38 deg)']
plate_for = {0: plate_window('front', 0, 1.45), 4: plate_window('left', -0.05, 1.45)}
Wt = 640; rows = []
for i, n in enumerate(names):
    tiles = []
    if i in plate_for: tiles.append(plate_for[i].resize((Wt, Wt), Image.LANCZOS))
    else:
        t = Image.new('RGB', (Wt, Wt), (36, 36, 40)); ImageDraw.Draw(t).text((20, Wt // 2 - 14), 'no plate view at this angle', fill=(150, 150, 160), font=font); tiles.append(t)
    for T in ('F1', 'F2'):
        im = Image.open(W2 + f'renders/chin/{T}_{n}.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (224, 224, 226, 255)); bg.alpha_composite(im)
        tiles.append(bg.convert('RGB').resize((Wt, Wt), Image.LANCZOS))
    row = Image.new('RGB', (Wt * 3, Wt))
    for k, t in enumerate(tiles): row.paste(t, (k * Wt, 0))
    ImageDraw.Draw(row).rectangle([0, 0, 520, 34], fill=(0, 0, 0)); ImageDraw.Draw(row).text((8, 4), labels[i], fill=(255, 255, 255), font=font)
    rows.append(row)
sheet = Image.new('RGB', (Wt * 3, Wt * len(rows) + 44), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for k, lab in enumerate(('PLATE (nearest calibrated view)', 'F1 (MicroF1 staged)', 'F2 (MicroF2)')): d.text((k * Wt + 12, 8), lab, fill=(255, 255, 255), font=font)
for i, r in enumerate(rows): sheet.paste(r, (0, 44 + i * Wt))
sheet.save(W2 + 'proof/F2_chin_closeups_plate_F1_F2.png')
# ------------------------------------------------------------------------------------------------ 3. shading high-pass / curvature / sections / sagittal
run('python3', W2 + 'tools/hp_views.py', W2 + 'proof/F2_highpass_shading_F1_vs_F2.png', 'F1=data/var_A_asbuilt.npz', 'F2=data/var_final.npz')
run('python3', W2 + 'tools/curv_run.py', W2 + 'data/var_final.npz', W2 + 'data/final_curv.npz')
for N, M, C in (('F1', 'var_A_asbuilt', 'F1_curv'), ('F2', 'var_final', 'final_curv')):
    run(B, '-b', '--factory-startup', '--python', W2 + 'tools/scalar_render.py', '--', W2 + f'data/{M}.npz', W2 + f'data/{C}.npz', 'k1', '50', W2 + 'renders/curv',
        'c:0:0:0:-0.06:1.455:0.19:900,c:35:0:-0.01:-0.06:1.455:0.19:900,c:90:0:0:-0.05:1.455:0.19:900,c:0:-32:0:-0.06:1.44:0.19:900', f'P_{N}_k1')
import glob
rws = []
for N in ('F1', 'F2'):
    fs = sorted(glob.glob(W2 + f'renders/curv/P_{N}_k1_*.png'))
    order = [f for f in fs if '_0_0_0_' in f] + [f for f in fs if '_35_0_' in f] + [f for f in fs if '_90_0_' in f] + [f for f in fs if '_0_-32_' in f]
    ims = []
    for f in order:
        im = Image.open(f).convert('RGBA'); bg = Image.new('RGBA', im.size, (60, 60, 62, 255)); bg.alpha_composite(im); ims.append(bg.convert('RGB'))
    row = Image.new('RGB', (900 * len(ims), 900))
    for k, im in enumerate(ims): row.paste(im, (k * 900, 0))
    ImageDraw.Draw(row).rectangle([0, 0, 520, 36], fill=(0, 0, 0)); ImageDraw.Draw(row).text((8, 5), f'{N}  max principal curvature k1 (red = convex, 50 1/m = full)', fill=(255, 255, 255), font=font)
    rws.append(row)
sh = Image.new('RGB', (rws[0].width, 1800)); sh.paste(rws[0], (0, 0)); sh.paste(rws[1], (0, 900)); sh.thumbnail((3200, 1600)); sh.save(W2 + 'proof/F2_curvature_k1_F1_vs_F2.png')
def sag(path):
    V, F, d_ = ml.load(path); T = ml.tri_fan(F)
    p = sorted(sl.chain(sl.slice_axis(V, T, 0, 0.0)), key=len, reverse=True)[0]; return np.stack([p[:, 1] * 1000, p[:, 2] * 1000], 1)
pl, pr = phi2.plate_profile()
plot2d([(sag(W2 + 'data/var_A_asbuilt.npz'), (255, 90, 60), 2, 'F1 mesh x=0'), (sag(W2 + 'data/var_final.npz'), (255, 235, 90), 2, 'F2 mesh x=0'), (pl, (80, 220, 120), 2, 'plate left'), (pr, (80, 160, 255), 2, 'plate right')],
       (-135, 25, 1418, 1500), 9.0, W2 + 'proof/F2_sagittal_profile_vs_plate.png', grid=2.0, label_every=10, title='sagittal x=0: y(mm) vs z(mm); plate profile = pixel staircase')
run('python3', W2 + 'tools/sections.py', W2 + 'renders/sec_final', 'F1=data/var_A_asbuilt.npz', 'F2=data/var_final.npz')
def sheet_of(files, out, cols=2):
    ims = [Image.open(f) for f in files]; w, h = ims[0].size
    s = Image.new('RGB', (w * cols, h * ((len(ims) + cols - 1) // cols)))
    for k, im in enumerate(ims): s.paste(im, ((k % cols) * w, (k // cols) * h))
    s.thumbnail((2600, 2600)); s.save(out)
sheet_of([W2 + 'renders/sec_final_plan_z%d.png' % z for z in (1436, 1442, 1448, 1456, 1470, 1430)], W2 + 'proof/F2_sections_plan_F1_vs_F2.png')
sheet_of([W2 + 'renders/sec_final_coronal_y%d.png' % y for y in (105, 85, 65, 50)], W2 + 'proof/F2_sections_coronal_F1_vs_F2.png')
# ------------------------------------------------------------------------------------------------ 4. analytic surface, old vs new (dense grid) -> shows the F1 construction defects themselves
Hn = exp.build(under=mf.PARAMS['under'], prof=exp.prof_nochin(mf.PARAMS['prof_zcut'])); exp.apply_a_smooth(Hn, sig=mf.PARAMS['rows_smooth']['sig'], rows=tuple(mf.PARAMS['rows_smooth']['rows'])); Hn.bumps = mf.PARAMS['bumps']
Ho = geo.Head()
az = np.radians(np.linspace(-100, 100, 400)); th = np.radians(np.linspace(55, 165, 330)); A, T = np.meshgrid(az, th)
u = np.stack([np.sin(T) * np.sin(A), -np.sin(T) * np.cos(A), np.cos(T)], -1).reshape(-1, 3)
def grid_mesh(H, name):
    P = H.phi(u).reshape(len(th), len(az), 3); V = P.reshape(-1, 3); F = []
    for i in range(len(th) - 1):
        for j in range(len(az) - 1):
            a = i * len(az) + j; F.append([a, a + 1, a + 1 + len(az), a + len(az)])
    off = np.concatenate([[0], np.cumsum([len(f) for f in F])]); flat = np.concatenate([np.asarray(f, np.int64) for f in F])
    np.savez(W2 + f'data/grid_{name}.npz', V=V, F=flat, Foff=off)
grid_mesh(Hn, 'new_final'); grid_mesh(Ho, 'old')
run('python3', W2 + 'tools/hp_views.py', W2 + 'proof/F2_analytic_surface_old_vs_new.png', 'OLD_analytic=data/grid_old.npz', 'NEW_analytic=data/grid_new_final.npz')
# ------------------------------------------------------------------------------------------------ 5. numeric tables
sil = json.load(open(W2 + 'data/sil.json'))
def under_sil(V, Tt, ys):
    best = {y: 9 for y in ys}
    for x in np.arange(-0.06, 0.0601, 0.002):
        for p, q in sl.slice_axis(V, Tt, 0, x):
            for y in ys:
                y0, y1 = p[1], q[1]
                if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
                    t = (y - y0) / (y1 - y0); z = p[2] + t * (q[2] - p[2])
                    if 1.41 < z < best[y]: best[y] = z
    return best
ys = [-0.115, -0.110, -0.100, -0.090, -0.080, -0.070, -0.060, -0.055, -0.050]
res = {}
for nm, pth in (('F1', 'data/var_A_asbuilt.npz'), ('F2', 'data/var_final.npz')):
    V, F, d_ = ml.load(W2 + pth); res[nm] = under_sil(V, ml.tri_fan(F), ys)
uc = []
for y in ys:
    zs = [fl.zrow(r) for r in range(225, 253) if sil['left'].get(str(r)) and fl.ycolL(sil['left'][str(r)][0]) <= y]
    uc.append(dict(y_mm=y * 1000, plate=min(zs) * 1000, F1=res['F1'][y] * 1000, F2=res['F2'][y] * 1000))
tables['under_chin_line_mm'] = uc
def zone_stats(path):
    V, F, d_ = ml.load(W2 + path); dh = ml.dihedral(V, F)
    keys = np.array(list(dh.keys())); ang = np.array(list(dh.values())); mid = 0.5 * (V[keys[:, 0]] + V[keys[:, 1]])
    zs = {'chin + jaw underside (z 1.4225-1.45, |x|<60, y<-50)': (mid[:, 2] > 1.4225) & (mid[:, 2] < 1.45) & (mid[:, 1] < -0.05) & (np.abs(mid[:, 0]) < 0.06),
          'lower cheek band (z 1.45-1.50, |x| 40-80, y<-20)': (mid[:, 2] > 1.45) & (mid[:, 2] < 1.50) & (np.abs(mid[:, 0]) > 0.040) & (np.abs(mid[:, 0]) < 0.080) & (mid[:, 1] < -0.02),
          'chin front (z 1.43-1.455, |x|<40, y<-90)': (mid[:, 2] > 1.43) & (mid[:, 2] < 1.455) & (mid[:, 1] < -0.09) & (np.abs(mid[:, 0]) < 0.04)}
    return {k: dict(n=int(m.sum()), mean=float(ang[m].mean()), p90=float(np.percentile(ang[m], 90)), p99=float(np.percentile(ang[m], 99)), max=float(ang[m].max())) for k, m in zs.items()}
tables['dihedral_deg'] = dict(F1=zone_stats('data/var_A_asbuilt.npz'), F2=zone_stats('data/var_final.npz'))
json.dump(tables, open(W2 + 'data/final_tables.json', 'w'), indent=1)
print('proofs written')
for k, v in tables['dihedral_deg']['F1'].items(): print(f'  {k:58s} mean F1 {v["mean"]:.2f} -> F2 {tables["dihedral_deg"]["F2"][k]["mean"]:.2f}  p99 {v["p99"]:.1f} -> {tables["dihedral_deg"]["F2"][k]["p99"]:.1f}')
