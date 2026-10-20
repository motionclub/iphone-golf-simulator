"""FORM3 proof pack (plate | FORM2 | FORM3, chat-9 where useful).  python3 proofs_f3.py [step ...]   (no args = everything)  ->  proof/P*.png
tags: start = chat-9 (9bfd788a/ArtDir geometry), FINAL6 = FORM2 candidate, FORM3 = this candidate (data/V_FORM3.npy)"""
import sys, os, json, subprocess, numpy as np
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont, ImageOps
W = os.path.dirname(os.path.abspath(__file__)); os.chdir(W); sys.path.insert(0, W)
B = '/Applications/Blender.app/Contents/MacOS/Blender'; ENV = dict(os.environ, PYTHONPATH='../male-micro1i/pylib'); ENVQ = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
F2, F3, ST = 'FINAL6', 'FORM3', 'start'
LAB3 = 'PLATE (ref),FORM2,FORM3'
def sh(cmd, env=None, **kw): return subprocess.run(cmd, shell=True, env=env or ENVQ, capture_output=True, text=True, **kw)
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
os.makedirs('proof', exist_ok=True)

def step_render():
    cmds = [f'python3 judge.py render {F2} {F3} {ST}', f'python3 quick.py render {F2} {F3} {ST}', f'python3 crop_cmp.py render {F2} manneq', f'python3 crop_cmp.py render {F3} manneq', f'python3 crop_cmp.py render {ST} manneq']
    for t in (F2, F3, ST): cmds.append(f'PANELS=q_bl,q_br python3 overlay.py render {t}')
    for t in (F2, F3, ST): cmds.append(f'./rv.sh {t} {t}_sil4 "left@4,right@4,back@4,front@4" sil')
    KH = 'yaw0_0.14_0.77_0_800_800_0,yaw30_0.14_0.77_0_800_800_0,yaw330_0.14_0.77_0_800_800_0,yaw180_0.14_0.77_0_800_800_0,yaw150_0.14_0.77_0_800_800_0,yaw210_0.14_0.77_0_800_800_0'
    LOW = 'yaw0_0.30_0.78_0_800_800_-40,yaw180_0.30_0.78_0_800_800_-40,yaw30_0.30_0.78_0_800_800_-35,yaw150_0.30_0.78_0_800_800_-35,yaw0_0.30_0.78_0_800_800_-65,yaw180_0.30_0.78_0_800_800_-65'
    for t in (F2, F3, ST): cmds.append(f'./rv.sh {t} kh_{t} "{KH}" clay'); cmds.append(f'./rv.sh {t} low_{t} "{LOW}" clay')
    SK = 'yaw180_0.5_0.9_0_700_600_0,yaw150_0.5_0.9_0_700_600_0,yaw210_0.5_0.9_0_700_600_0,yaw90_0.5_0.9_0_700_600_0,yaw0_0.5_0.85_0_700_600_0'
    for t in (F2, F3, ST): cmds.append(f'./rv.sh {t} skf_{t} "{SK}" skin')
    with ThreadPoolExecutor(8) as ex: list(ex.map(sh, cmds))
    print('renders done')

def sheet3(out, script, extra='', env=''):
    r = sh(f'{env} {script} {extra}'); print(out, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:])

def step_sheets():
    L = f'LABELS="{LAB3}" '
    sheet3('P01', f'{L} NOSTART=1 VIEWS=front,q_fl,q_fr ZOOM=3 python3 judge.py sheet proof/P01_front_groin_plate_F2_F3.png pelvis {F2} {F3}')
    sheet3('P02', f'{L} NOSTART=1 VIEWS=back,q_bl,q_br,left,right ZOOM=3 python3 judge.py sheet proof/P02_back_3q_side_plate_F2_F3.png pelvis {F2} {F3}')
    sheet3('P03', f'{L} python3 quick.py sheet proof/P03_front_closeups_plain.png front,fl,fr {F2} {F3}')
    sheet3('P03b', f'{L} python3 quick.py sheet proof/P03b_front_closeups_enhanced.png front,fl,fr {F2} {F3} --enh')
    sheet3('P04', f'LABELS="{LAB3}" python3 crop_cmp.py sheet proof/P04_back_closeup_plain.png back 0.68 1.06 0.20 {F2} {F3}')
    sheet3('P04b', f'LABELS="{LAB3}" python3 crop_cmp.py sheet proof/P04b_back_closeup_enhanced.png back 0.68 1.06 0.20 {F2} {F3} --enh')
    sheet3('P05', f'{L} python3 quick.py sheet proof/P05_3q_closeups_plain.png bl,br {F2} {F3}')
    sheet3('P05b', f'{L} python3 quick.py sheet proof/P05b_3q_closeups_enhanced.png bl,br {F2} {F3} --enh')
    sheet3('P06', f'{L} python3 quick.py sheet proof/P06_side_closeup.png left,right {F2} {F3}')
    sheet3('P07', f'{L} python3 quick.py sheet proof/P07_relit_back_3q_topligh.png backH,blH,brH {F2} {F3} --enh')
    sheet3('P08', f'LABELS="PLATE (ref),chat-9,FORM2,FORM3" VIEWS=back,q_bl,q_br ZOOM=2 python3 judge.py sheet proof/P16_fullbody_3q_back.png full {F2} {F3}')
    sheet3('P14', f'python3 overlay.py sheet proof/P14_3q_silhouette_overlay_F2_red_F3_green.png q_bl,q_br {F2} {F3}')

def grid(out, rows, cols, label_fn, scale=0.5, size=800, pad_top=24, extra_labels=None):
    w = int(size * scale); S = Image.new('RGB', (len(cols) * (w + 4) + 4, len(rows) * (w + pad_top + 4) + 4), (16, 16, 16)); d = ImageDraw.Draw(S); F = font(18)
    for r, (lab, dr) in enumerate(rows):
        for c, n in enumerate(cols):
            im = Image.open(f'r/{dr}/{n}.png').convert('RGB').resize((w, w), Image.LANCZOS); S.paste(im, (4 + c * (w + 4), 4 + r * (w + pad_top + 4) + pad_top))
            d.text((8 + c * (w + 4), 6 + r * (w + pad_top + 4)), lab + '  ' + label_fn(c), fill=(255, 200, 80), font=F)
    S.save(out); print(out, S.size)

def step_grids():
    KH = ['yaw0_0.14_0.77_0_800_800_0', 'yaw30_0.14_0.77_0_800_800_0', 'yaw330_0.14_0.77_0_800_800_0', 'yaw180_0.14_0.77_0_800_800_0', 'yaw150_0.14_0.77_0_800_800_0', 'yaw210_0.14_0.77_0_800_800_0']
    labs = ['front', '3/4 front L', '3/4 front R', 'back', '3/4 back L', '3/4 back R']
    grid('proof/P08_keyhole_closeups_F2_vs_F3.png', [('chat-9', f'kh_{ST}'), ('FORM2', f'kh_{F2}'), ('FORM3', f'kh_{F3}')], KH, lambda c: labs[c], 0.4)
    LOW = ['yaw0_0.30_0.78_0_800_800_-40', 'yaw180_0.30_0.78_0_800_800_-40', 'yaw30_0.30_0.78_0_800_800_-35', 'yaw150_0.30_0.78_0_800_800_-35', 'yaw0_0.30_0.78_0_800_800_-65', 'yaw180_0.30_0.78_0_800_800_-65']
    labs2 = ['front, below', 'back, below', '3/4 front, below', '3/4 back, below', 'front, steep below', 'back, steep below']
    grid('proof/P10_low_angle_orbit_F2_vs_F3.png', [('FORM2', f'low_{F2}'), ('FORM3', f'low_{F3}')], LOW, lambda c: labs2[c], 0.5)
    SK = ['yaw180_0.5_0.9_0_700_600_0', 'yaw150_0.5_0.9_0_700_600_0', 'yaw210_0.5_0.9_0_700_600_0', 'yaw90_0.5_0.9_0_700_600_0', 'yaw0_0.5_0.85_0_700_600_0']
    labs3 = ['back', '3/4 back L', '3/4 back R', 'side', 'front']
    w, h = 700, 600; F = font(20); rows = [('chat-9', f'skf_{ST}'), ('FORM2', f'skf_{F2}'), ('FORM3', f'skf_{F3}')]
    S = Image.new('RGB', (w * 5, (h + 30) * 3), (16, 16, 16)); d = ImageDraw.Draw(S)
    for r, (lab, dr) in enumerate(rows):
        for c, n in enumerate(SK): S.paste(Image.open(f'r/{dr}/{n}.png').convert('RGB'), (c * w, r * (h + 30) + 30)); d.text((c * w + 6, r * (h + 30) + 4), f'{lab}  {labs3[c]} (skin look)', fill=(255, 200, 80), font=F)
    S = S.resize((S.width * 2 // 3, S.height * 2 // 3)); S.save('proof/P19_skin_look_chat9_F2_F3.png'); print('P19', S.size)

def crops_center():
    import json as js
    R = os.path.abspath(os.path.join(W, '..', '..')); CAM = {c['name']: c for c in js.load(open(R + '/work/male-silhouette/reference-cameras.json'))['views']}
    c = CAM['bald_back']; mpp = c['metres_per_pixel']; cx = c['centre_x']; sy = c['sole_y']; X0, Y0 = 846, 283
    plate = Image.open(R + '/ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB'); box = (-0.08, 0.08, 0.72, 0.96)
    def pc(img, k, off=(0, 0)): return img.crop((int((cx + box[0] / mpp) * k - off[0] * k), int((sy - box[3] / mpp) * k - off[1] * k), int((cx + box[1] / mpp) * k - off[0] * k), int((sy - box[2] / mpp) * k - off[1] * k)))
    pl = pc(plate, 1).resize((int(0.16 / mpp * 4), int((0.96 - 0.72) / mpp * 4)), Image.LANCZOS); F = font(22)
    tags = [('chat-9', ST), ('FORM2', F2), ('FORM3', F3)]
    for kind, fn in (('plain', 'proof/P09_between_the_cheeks_normal_light.png'), ('relit', 'proof/P09b_between_the_cheeks_top_light.png')):
        ims = [('PLATE', pl)]
        for lab, t in tags:
            im = Image.open(f'r/{t}_c/back@4.png').convert('RGB') if kind == 'plain' else Image.open(f'r/{t}_qh/back@4:846_283_985_415.png').convert('RGB')
            ims.append((lab, pc(im, 4) if kind == 'plain' else pc(im, 4, (X0, Y0))))
        w_ = max(i.size[0] for _, i in ims); h_ = max(i.size[1] for _, i in ims)
        S = Image.new('RGB', (w_ * 4 + 20, (h_ + 28) * 2), (16, 16, 16)); d = ImageDraw.Draw(S)
        for row, enh in enumerate((False, True)):
            for i, (lab, im) in enumerate(ims):
                im = im.resize((w_, h_), Image.LANCZOS); im2 = ImageOps.autocontrast(im.convert('L'), cutoff=(1, 1)).convert('RGB') if enh else im
                S.paste(im2, (4 + i * (w_ + 4), row * (h_ + 28) + 26)); d.text((8 + i * (w_ + 4), row * (h_ + 28) + 3), lab + ('  (contrast x)' if enh else ''), fill=(255, 200, 80), font=F)
        S = S.resize((int(S.width * 1.6), int(S.height * 1.6)), Image.LANCZOS); S.save(fn); print(fn, S.size)

def step_sections():
    sh(f'python3 sagplot.py proof/P11_centerline_sagittal_sections.png {ST},{F2},{F3} 0.0039,0.0117,0.0200 -0.21 0.13 0.70 0.90')
    sh(f'python3 axplot.py tmp/ax_lobes.png {ST},{F2},{F3} 0.78,0.80,0.82,0.84,0.88 -0.13 0.13 0.03 0.12 3200')
    im = Image.open('tmp/ax_lobes.png'); n = 5; w = (im.width - 4 * (n - 1)) // n; S = Image.new('RGB', (w, im.height * n + 4 * (n - 1)), (10, 10, 10))
    for i in range(n): S.paste(im.crop((i * (w + 4), 0, i * (w + 4) + w, im.height)), (0, i * (im.height + 4)))
    S.save('proof/P12_lobe_axial_sections_chat9_blue_F2_green_F3_orange.png'); print('P12', S.size)
    sh(f'python3 axplot.py proof/P12b_tunnel_axial_sections.png {ST},{F2},{F3} 0.70,0.72,0.74,0.76 -0.09 0.09 -0.21 0.11 2400')
    r = sh(f'python3 profile_plot3.py proof/P13_side_contour_vs_plate_z076_095.png 0.76 0.96 {ST}:chat-9:110,190,255 {F2}:FORM2:255,120,120 {F3}:FORM3:110,255,150'); print(r.stdout.strip()[-200:])
    r = sh(f'python3 profile_plot3.py proof/P13b_side_contour_underbutt_z070_090.png 0.70 0.90 {ST}:chat-9:110,190,255 {F2}:FORM2:255,120,120 {F3}:FORM3:110,255,150'); print(r.stdout.strip()[-200:])

def step_wire():
    import wire
    from common import V0
    Vs = {'chat-9': V0, 'FORM2': np.load(f'data/V_{F2}.npy'), 'FORM3': np.load(f'data/V_{F3}.npy')}; tags = {'chat-9': ST, 'FORM2': F2, 'FORM3': F3}
    views = [(0, 'front'), (180, 'back'), (30, '3/4 front L'), (150, '3/4 back L')]; sc = 0.5; w = 400; F = font(18)
    S = Image.new('RGB', (len(views) * (w + 4) + 4, 3 * (w + 28) + 4), (16, 16, 16)); d = ImageDraw.Draw(S)
    for r, lab in enumerate(Vs):
        for c, (yaw, vl) in enumerate(views):
            base = f'r/kh_{tags[lab]}/yaw{yaw}_0.14_0.77_0_800_800_0.png'; im = wire.draw(Vs[lab], yaw, 0.14, 0.77, 800, 800, 0, base, width=1).resize((w, w), Image.LANCZOS)
            S.paste(im, (4 + c * (w + 4), 4 + r * (w + 28) + 26)); d.text((8 + c * (w + 4), 6 + r * (w + 28)), f'{lab}  {vl}  (mesh)', fill=(255, 200, 80), font=F)
    S.save('proof/P15_wireframe_keyhole_chat9_F2_F3.png'); print('P15', S.size)

STEPS = dict(render=step_render, sheets=step_sheets, grids=step_grids, center=crops_center, sections=step_sections, wire=step_wire)
if __name__ == '__main__':
    todo = sys.argv[1:] or list(STEPS)
    for s in todo: print('==', s); STEPS[s]()
