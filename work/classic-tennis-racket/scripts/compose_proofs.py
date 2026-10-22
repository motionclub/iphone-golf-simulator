"""Compose the proof sheets (PIL, system python3) from proof/raw renders + measured numbers.
python3 compose_proofs.py"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket')
RAW, OUT = W / 'proof' / 'raw', W / 'proof'
BG, FG, MUTED, ACC, OK = (34, 36, 41), (238, 238, 238), (170, 176, 188), (120, 200, 255), (130, 220, 150)
HEL = '/System/Library/Fonts/Helvetica.ttc'
MEN = '/System/Library/Fonts/Menlo.ttc'


def font(sz, bold=False):
    return ImageFont.truetype(HEL, sz, index=1 if bold else 0)


def mono(sz):
    return ImageFont.truetype(MEN, sz)


m = json.load(open(W / 'data' / 'measure_final.json'))
oh = {t: json.load(open(W / 'data' / 'onhand_run' / f'onhand_{t}.json')) for t in ('male', 'female')}
mm = lambda x: f'{x * 1000:.1f} mm'


def load(name, size=None, crop=None):
    im = Image.open(RAW / name).convert('RGB')
    if crop:
        im = im.crop(crop)
    if size:
        im = im.resize(size, Image.LANCZOS)
    return im


def header(draw, width, title, lines, y=18):
    draw.text((28, y), title, font=font(34, True), fill=FG)
    y += 50
    for ln in lines:
        draw.text((28, y), ln, font=mono(17), fill=MUTED)
        y += 25
    return y + 8


def chip(im, label, color=ACC):
    d = ImageDraw.Draw(im)
    f = font(20, True)
    w = d.textlength(label, font=f)
    d.rounded_rectangle((10, 10, 10 + w + 20, 44), radius=8, fill=(20, 22, 26, 255))
    d.text((20, 15), label, font=f, fill=color)
    return im


def grid_sheet(out, title, lines, panels, cols, cell, gut=14, top_pad=0):
    rows = (len(panels) + cols - 1) // cols
    n_lines = len(lines)
    head_h = 18 + 50 + 25 * n_lines + 16
    W_ = cols * cell[0] + (cols + 1) * gut
    H_ = head_h + rows * (cell[1] + gut) + gut
    sheet = Image.new('RGB', (W_, H_), BG)
    d = ImageDraw.Draw(sheet)
    header(d, W_, title, lines)
    for i, (img, label) in enumerate(panels):
        im = img.copy().resize(cell, Image.LANCZOS)
        chip(im, label)
        r, c = divmod(i, cols)
        sheet.paste(im, (gut + c * (cell[0] + gut), head_h + r * (cell[1] + gut)))
    sheet.save(out)
    print('wrote', out)


# ------------------------------------------------------------------ 01 turnaround
dims = (f"L {m['length_m']:.3f} m | head {m['head_outer_height_m']:.3f} x {m['head_outer_width_m']:.3f} m | grip dia {m['grip_diameter_mean_m']:.4f} m "
        f"x {m['grip_usable_length_m']:.3f} m | butt cap dia {m['butt_cap_diameter_max_m']:.3f} m | frame depth {m['depth_m']:.3f} m")
tr = m['tris']
trl = (f"tris: frame {tr['Racket_Classic']:,} + strings/grommets {tr['StringBed']:,} + grip {tr['Grip']:,} + butt cap {tr['ButtCap']:,} = {m['tris_visual']:,} visual "
       f"(+ {tr['Collider_Racket']} collision proxy, separate FBX)")
crop_full = (150, 150, 750, 1260)
top = [(load(f'racket_{v}.png', crop=crop_full), lab) for v, lab in (('front', 'front (hitting face)'), ('back', 'back'), ('side', 'side'), ('q3', '3/4'))]
bot = [(load('racket_throat.png'), 'throat / open Y window'), (load('racket_throat_q3.png'), 'throat 3/4 (smooth fillets)'),
       (load('racket_grip_q3.png'), 'wrapped grip + butt cap'), (load('racket_strings.png'), 'string bed + grommets')]
cw = 440
cell_top = (cw, int(cw * 1110 / 600))
cell_bot = (cw, cw)
head_lines = [dims, trl, 'materials: White_Frame (matte) | White_Strings | Black_Grip - flat colours, opaque, no textures / text / logos']
gut = 14
rows_h = cell_top[1] + gut + cell_bot[1] + gut
head_h = 18 + 50 + 25 * len(head_lines) + 16
sheet = Image.new('RGB', (4 * cw + 5 * gut, head_h + rows_h + gut), BG)
d = ImageDraw.Draw(sheet)
header(d, sheet.width, 'Racket_Classic - turnaround (staged prop, origin = grip centre, +Y shaft to head, +Z face normal)', head_lines)
for i, (img, lab) in enumerate(top):
    im = img.resize(cell_top, Image.LANCZOS)
    chip(im, lab)
    sheet.paste(im, (gut + i * (cw + gut), head_h))
for i, (img, lab) in enumerate(bot):
    im = img.resize(cell_bot, Image.LANCZOS)
    chip(im, lab)
    sheet.paste(im, (gut + i * (cw + gut), head_h + cell_top[1] + gut))
sheet.save(OUT / '01_turnaround.png')
print('wrote 01')

# ------------------------------------------------------------------ 02 look vs chosen reference
cmp = Image.open(RAW / 'cmp_ref_raw.png').convert('RGB')
lines = ['left: ArtDir/hero/kits/racket_classic/00_hero_pick.jpg (chosen look, scaled to the same racket length)   right: Racket_Classic (this build)',
         'differences are spec-driven: grip dia 0.034 m (ref toy grip is fatter), head 0.348 m tall (ref ~0.38 m); same diamond string lattice, Y throat window, wrapped black grip, flared butt cap']
head_h = 18 + 50 + 25 * len(lines) + 16
sheet = Image.new('RGB', (cmp.width, head_h + cmp.height), BG)
d = ImageDraw.Draw(sheet)
header(d, sheet.width, 'LOOK_CLASSIC - chosen reference vs Racket_Classic (front, same length)', lines)
sheet.paste(cmp, (0, head_h))
chip(sheet, 'chosen reference') if False else None
d.text((20, head_h + 12), 'CHOSEN LOOK', font=font(24, True), fill=ACC)
d.text((cmp.width // 2 + 40, head_h + 12), 'RACKET_CLASSIC (Blender, ortho front)', font=font(24, True), fill=OK)
sheet.save(OUT / '02_look_vs_chosen_ref.png')
print('wrote 02')


# ------------------------------------------------------------------ on-hand sheets
def onhand_sheet(out, tag, pose, title, lines, full_names, close_names):
    pre = f'{tag}_{pose}'
    panels = [(load(f'{pre}_{n}.png'), lab) for n, lab in full_names]
    panels += [(load(f'{pre}_{n}.png'), lab) for n, lab in close_names]
    grid_sheet(out, title, lines, panels, 3, (560, 560))


mo, fo = oh['male'], oh['female']
a = mo['apose']
onhand_sheet(OUT / '03_male_apose.png', 'male', 'apose', 'Male - A-pose grip test (unposed locked hero hand)',
             [f"copy of HeroBase_Male_Silhouette (SHA fd04bc28...), racket vs hand: {sum(a['tri_overlaps_hand'].values())} overlapping triangles | racket vs whole body: {sum(a['tri_overlaps_body'].values())} | min clearance {a['min_clearance_body_mm']:.2f} mm (exact BVH tri-tri test)",
              f"socket: handle axis = cos({mo['phi']:.0f})*v + sin({mo['phi']:.0f})*u in the palm plane (v thumb, u fingers), face normal = palm normal rolled {mo['roll']:.0f} deg, lift {a['W_g'] * 1000:.1f} mm above the palm plane",
              'fingers are straight in the locked hero pose (no finger rig yet): the grip rests across the palm; wrapped fingers are in the ready-stance proof'],
             [('crop_front', 'front (22 deg off-axis)'), ('crop_side', 'side'), ('crop_q3', '3/4')],
             [('grip_close_a', 'grip in palm (outside)'), ('grip_close_b', 'grip in palm (above)'), ('grip_close_c', 'grip in palm (front-below)')])
r_ = mo['ready']
onhand_sheet(OUT / '04_male_ready.png', 'male', 'ready', 'Male - ready stance (proof-only pose on a duplicate)',
             [f"elbow 95 deg + shoulder adduction 16 deg on a COPY, fingers wrapped | racket vs whole posed body: {sum(r_['tri_overlaps_body'].values())} overlapping triangles | min clearance {r_['min_clearance_body_mm']:.2f} mm | finger-to-grip gaps "
              + ', '.join(f"{k} {v:.1f}" for k, v in r_['finger_vs_cylinder_min_mm'].items()) + ' mm',
              'same Hand_Racket socket as the A-pose; fingers bent along a path hugging the grip (copy of the mesh), arm skinned on the copy; hero blend untouched',
              'thumb left in its locked pose'],
             [('crop_front', 'front (22 deg off-axis)'), ('crop_side', 'side'), ('crop_q3', '3/4')],
             [('grip_close_a', 'fingers wrap the grip (a)'), ('grip_close_b', 'fingers wrap the grip (b)'), ('grip_close_c', 'fingers wrap the grip (c)')])
r2 = fo['ready']
onhand_sheet(OUT / '05_female_ready.png', 'female', 'ready', 'Female - ready stance (proof-only pose on a duplicate)',
             [f"elbow 95 deg + forearm supinated 90 deg on a COPY | racket vs whole posed body: {sum(r2['tri_overlaps_body'].values())} overlapping triangles | min clearance {r2['min_clearance_body_mm']:.2f} mm | racket vs hand pieces: {sum(r2['tri_overlaps_hand'].values())}",
              f"ArtDir female hand is a placeholder (palm ball + sausage fingers, pronated, ~45% of the male hand): same socket convention; A-pose bind: racket vs hand {sum(fo['apose']['tri_overlaps_hand'].values())} overlaps,",
              "but the arm hangs flush to the thigh there, so the static A-pose racket crosses the thigh (disclosed); grip diameter is unchanged (0.034 m)"],
             [('crop_front', 'front (22 deg off-axis)'), ('crop_side', 'side'), ('crop_q3', '3/4')],
             [('grip_close_a', 'placeholder fingers on the grip (a)'), ('grip_close_b', 'placeholder fingers on the grip (b)'), ('grip_close_c', 'placeholder fingers on the grip (c)')])

# ------------------------------------------------------------------ 06 socket diagram
def gizmo(name):
    base = Image.open(RAW / f'{name}_base.png').convert('RGBA')
    g = Image.open(RAW / f'{name}_gizmo.png').convert('RGBA')
    return Image.alpha_composite(base, g).convert('RGB')


def gizmo_empty(name):
    base = Image.open(RAW / f'{name}_empty_only.png').convert('RGBA')
    g = Image.open(RAW / f'{name}_gizmo.png').convert('RGBA')
    return Image.alpha_composite(base, g).convert('RGB')


cell = 640
gut = 14
text_w = 600
head_lines = ['Hand_Racket = EMPTY at the palm hold point; axes X red (across face, Y x Z) | Y green (shaft to head) | Z blue (hitting-face normal / palm side)',
              'racket parents to Hand_Racket with an IDENTITY local transform; Hand_Racket parents to the hand (here: the body copy). Unparent / delete leaves the body mesh bit-identical.']
head_h = 18 + 50 + 25 * len(head_lines) + 16
canvas = Image.new('RGB', (3 * cell + text_w + 5 * gut, head_h + 2 * (cell + gut) + gut), BG)
d = ImageDraw.Draw(canvas)
header(d, canvas.width, 'SOCKET_HAND_RACKET - Hand_Racket empty and racket parenting (male above, female below)', head_lines)
panels = [
    (gizmo('socket_male_apose_close'), 'male A-pose bind: racket in palm'), (gizmo_empty('socket_male_apose_close'), 'male A-pose bind: empty only'), (gizmo('socket_male_ready_close'), 'male ready stance (proof pose)'),
    (gizmo('socket_female_apose_close'), 'female A-pose bind: racket'), (gizmo_empty('socket_female_apose_close'), 'female A-pose bind: empty only'), (gizmo('socket_female_ready_close'), 'female ready stance (proof pose)'),
]
for i, (img, lab) in enumerate(panels):
    im = img.resize((cell, cell), Image.LANCZOS)
    chip(im, lab)
    r, c = divmod(i, 3)
    canvas.paste(im, (gut + c * (cell + gut), head_h + r * (cell + gut)))
# text panel
tx = 3 * cell + 4 * gut
ty = head_h
d.rounded_rectangle((tx, ty, tx + text_w, ty + 2 * cell + gut), radius=12, fill=(24, 26, 30))
f1, f2 = mono(17), mono(16)
y = ty + 16
sm, sf = oh['male']['socket'], oh['female']['socket']
tree = ['Hierarchy (staged on-hero blends)',
        '',
        'Body_M  (copy of HeroBase_Male_Silhouette)',
        ' └─ Hand_Racket        EMPTY, bind-pose pose',
        '     └─ Racket_Classic  local = identity',
        '         ├─ StringBed',
        '         ├─ Grip',
        '         ├─ ButtCap',
        '         └─ Collider_Racket (hidden)',
        '',
        'Body_F  (copy of HeroBase_Female) - same tree',
        '',
        'Bind-pose pose of Hand_Racket (m)',
        ' male  Blender ' + ' '.join(f'{x:+.4f}' for x in sm['apose_world_blender']['position']),
        '       Unity   ' + ' '.join(f'{x:+.4f}' for x in sm['apose_world_unity']['position']),
        ' female Blender ' + ' '.join(f'{x:+.4f}' for x in sf['apose_world_blender']['position']),
        '       Unity   ' + ' '.join(f'{x:+.4f}' for x in sf['apose_world_unity']['position']),
        '',
        'Grip in the hand frame (u, v, w)',
        ' u fingers, v thumb, w palm normal',
        f" phi {sm['grip_in_hand_frame']['phi_deg']:.0f} deg, roll {sm['grip_in_hand_frame']['roll_deg']:.0f} deg",
        f" male  centre ({sm['grip_in_hand_frame']['U_g']:+.3f}, {sm['grip_in_hand_frame']['V_g']:+.3f}, {sm['grip_in_hand_frame']['W_g']:+.4f})",
        f" female centre ({sf['grip_in_hand_frame']['U_g']:+.3f}, {sf['grip_in_hand_frame']['V_g']:+.3f}, {sf['grip_in_hand_frame']['W_g']:+.4f})",
        '',
        'Unity: (x,y,z)_B -> (-x, z, -y); verified: racket FBX under',
        'Hand_Racket reproduces the Blender placement to <0.01 mm',
        '(see CLASSIC_RACKET_RESULTS.md).']
for ln in tree:
    d.text((tx + 18, y), ln, font=f1 if not ln.startswith(('Hierarchy', 'Bind', 'Grip')) else mono(18), fill=(ACC if ln.startswith(('Hierarchy', 'Bind', 'Grip')) else FG))
    y += 27
canvas.save(OUT / '06_socket_diagram.png')
print('wrote 06')

# ------------------------------------------------------------------ 07 scale line-up with ruler
lj = json.load(open(RAW / 'scale_lineup.png.json'))
im = Image.open(RAW / 'scale_lineup.png').convert('RGB')
pxm, cz, H = lj['px_per_m'], lj['center_z'], lj['image_h']
d = ImageDraw.Draw(im)
zpx = lambda z: H / 2 - (z - cz) * pxm
fl = font(22)
for k in range(0, 19):
    z = k * 0.1
    y = zpx(z)
    L = 26 if k % 5 == 0 else 14
    d.line([(740, y), (740 + L, y)], fill=(255, 220, 90), width=2)
    if k % 5 == 0:
        d.text((670, y - 12), f'{z:.1f} m', font=fl, fill=(255, 220, 90))
x0 = 740
d.line([(x0, zpx(0)), (x0, zpx(1.8))], fill=(255, 220, 90), width=2)
for z, lab, col, xr in ((lj['body_heights_m']['male'], f"male {lj['body_heights_m']['male']:.3f} m", (130, 200, 255), 20), (lj['body_heights_m']['female'], f"female {lj['body_heights_m']['female']:.3f} m", (255, 170, 210), 1500)):
    d.line([(0, zpx(z)), (1900, zpx(z))], fill=col, width=1)
    d.text((xr, zpx(z) - 28), lab, font=fl, fill=col)
d.line([(0, zpx(m['length_m'])), (1900, zpx(m['length_m']))], fill=(130, 220, 150), width=1)
d.text((20, zpx(m['length_m']) - 28), f"racket {m['length_m']:.3f} m = {m['length_m'] / lj['body_heights_m']['male'] * 100:.0f}% of hero height", font=fl, fill=(130, 220, 150))
head_lines = [f"Racket_Classic standing upright (butt on the floor) between the two locked bald bases (copies, A-pose, FBX scale 1): racket {m['length_m']:.3f} m vs hero {lj['body_heights_m']['male']:.3f} / {lj['body_heights_m']['female']:.3f} m",
              f"ratio {m['length_m'] / lj['body_heights_m']['male']:.3f} (real adult racket 0.686 m / 1.75 m = 0.392) | head {m['head_outer_height_m']:.3f} m | grip dia {m['grip_diameter_mean_m']:.4f} m | ruler 0.1 m ticks (ortho, {pxm:.1f} px/m)"]
head_h = 18 + 50 + 25 * len(head_lines) + 16
sheet = Image.new('RGB', (im.width, head_h + im.height), BG)
header(ImageDraw.Draw(sheet), sheet.width, 'SCALE_HERO - racket vs hero height', head_lines)
sheet.paste(im, (0, head_h))
sheet.save(OUT / '07_scale_lineup.png')
print('wrote 07')
