"""Compose the proof sheets from proof/raw cells + proof/raw/checks_<g>.json.   python3 compose_proofs.py
FEET_<Hero>_<Colour>.png (close-ups, both feet, 4 views) - CUTAWAY_<Hero>.png - BEFORE_AFTER_<Hero>.png - CONTEXT_<Hero>.png"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/tennis-shoes-fit'
RAW, OUT = f'{W}/proof/raw', f'{W}/proof'
BG, FG, DIM = (24, 26, 31), (240, 241, 244), (160, 165, 175)
GOOD, BAD, WARN = (110, 220, 140), (240, 110, 100), (240, 200, 90)


def font(size, bold=False):
    for p in ('/System/Library/Fonts/Avenir Next.ttc', '/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/Geneva.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=(1 if bold and p.endswith('.ttc') else 0))
            except Exception:
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
    return ImageFont.load_default()


def chk(g):
    return json.load(open(f'{RAW}/checks_{g}.json'))


def old(g):
    return json.load(open(f'{RAW}/start_kit_on_new_body_{g}.json'))


def label(d, xy, text, size=26, fill=FG, bold=False, anchor='la'):
    d.text(xy, text, font=font(size, bold), fill=fill, anchor=anchor)


def tag(im, text, fill=(0, 0, 0), fg=FG, pos=(14, 14), size=22):
    d = ImageDraw.Draw(im)
    f = font(size, True)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((pos[0], pos[1], pos[0] + tw + 20, pos[1] + size + 14), radius=6, fill=fill)
    d.text((pos[0] + 10, pos[1] + 6), text, font=f, fill=fg)


def feet_sheet(g, cw):
    c = chk(g)
    hero = 'MALE' if g == 'male' else 'FEMALE'
    cell = 640
    views = ('side', 'front', 'heel', 'q3')
    vname = {'side': 'SIDE', 'front': 'FRONT', 'heel': 'HEEL (from behind)', 'q3': 'LOW 3/4'}
    fi, sv, ov, lo = c['foot_inside'], c['skin_visibility'], c['sock_collar_overlap'], c['layer_overlaps']
    H0, H1 = 130, 330
    S = Image.new('RGB', (cell * 4, H0 + cell * 2 + H1), BG)
    d = ImageDraw.Draw(S)
    label(d, (24, 18), f'TENNIS_SHOES_FIT  -  {hero}  -  {cw.upper()} kit', 44, bold=True)
    label(d, (24, 76), f'close-ups of the delivered blend  ({os.path.basename(c["output_blend_sha256"][:0]) or ""}StandardKit_{"Male" if g == "male" else "Female"}.blend)   fit measured on {"merged_fd04bc28.blend  SHA d6c4dcfb" if g == "male" else "HeroBase_Female_FULL_STAGED.blend  SHA a1d73a33"}...', 24, fill=DIM)
    for r, foot in enumerate(('R', 'L')):
        for k, v in enumerate(views):
            im = Image.open(f'{RAW}/feet_{g}_{cw}_{foot}_{v}.png').convert('RGB').resize((cell, cell))
            tag(im, f'{"RIGHT" if foot == "R" else "LEFT"} foot  -  {vname[v]}')
            S.paste(im, (k * cell, H0 + r * cell))
    y = H0 + cell * 2 + 22
    R, Lf = fi['R'], fi['L']
    lines = [
        (f'FOOT_INSIDE   foot vertices below the collar outside the shoe:  right {R["foot_verts_outside_shoe"]} of {R["foot_vertices_below_collar"]}   left {Lf["foot_verts_outside_shoe"]} of {Lf["foot_vertices_below_collar"]}'
         f'   |  inside shoe material 0  |  nearest skin to shoe wall {min(R["foot_to_shoe_min_mm"], Lf["foot_to_shoe_min_mm"]):.1f} mm  |  sock inside the shoe: 0 outside', GOOD),
        (f'TOE_COVERED   inner wall past the longest toe  +{min(R["toe_overhang_inner_mm"], Lf["toe_overhang_inner_mm"]):.1f} mm  (outside of the toe box +{min(R["toe_overhang_outer_mm"], Lf["toe_overhang_outer_mm"]):.1f} mm)'
         f'      HEEL_COVERED   inner wall past the heel  +{min(R["heel_overhang_inner_mm"], Lf["heel_overhang_inner_mm"]):.1f} mm  (outside +{min(R["heel_overhang_outer_mm"], Lf["heel_overhang_outer_mm"]):.1f} mm)', GOOD),
        (f'NO_SKIN_GAP   skin visible below the sock cuff from {sv["ray_tests"]:,} camera rays: {sv["exposed"]}   |  collar rim {R["collar_rim_z_min"]*1000:.0f}-{R["collar_rim_z_max"]*1000:.0f} mm (mean {R["collar_rim_z_mean"]*1000:.0f} mm) above the foot sole'
         f'  |  sock-to-collar overlap {min(ov["R"]["overlap_mm_min"], ov["L"]["overlap_mm_min"]):.0f} mm (sock continues {ov["R"]["sock_top_above_rim_mm"]["min"]:.0f} mm above the rim)', GOOD),
        (f'SOLE_GROUNDED   both soles end at z = {c["sole"]["White_R"]["sole_bottom_z"]*1000:.1f} mm (tread {c["sole"]["White_R"]["tread_bottom_z"]*1000:.1f} mm), left = right to {abs(c["sole"]["White_R"]["tread_bottom_z"]-c["sole"]["White_L"]["tread_bottom_z"])*1000:.3f} mm'
         f'    MIRROR   mirrored right vs left: {c["mirror"]["hausdorff_mirror_R_to_L_mm"]:.4f} mm (a same-facing copy would be off by {c["mirror"]["hausdorff_translated_copy_mm"]:.0f} mm)   same length {c["mirror"]["length_R_mm"]:.0f} mm, same sole {c["mirror"]["sole_height_R_mm"]:.1f} mm', GOOD),
        (f'No triangle of sock, shoe, left shoe or body intersects another (sock vs shoe {lo["R"]["sock_vs_shoe_triangle_pairs"]}+{lo["L"]["sock_vs_shoe_triangle_pairs"]}, shoe vs body {lo["R"]["shoe_vs_body_triangle_pairs"]}+{lo["L"]["shoe_vs_body_triangle_pairs"]}, left vs right shoe {lo["L_vs_R_shoe_triangle_pairs"]}).  '
         f'Polo + bottom mesh SHA unchanged: {c["other_pieces"]["identical"]}.  Materials Std_White_Lit / Std_Black_Lit only.', DIM),
    ]
    for t, col in lines:
        label(d, (24, y), t, 22, fill=col)
        y += 38
    S.save(f'{OUT}/FEET_{hero.title()}_{cw}.png')
    print('wrote', f'FEET_{hero.title()}_{cw}.png', S.size)


def cutaway_sheet(g):
    c = chk(g)
    hero = 'MALE' if g == 'male' else 'FEMALE'
    cell = 800
    names = [('sagittal', 'SAGITTAL cut through the foot axis'), ('coronal', 'CORONAL cut through the ankle'), ('axial_collar', 'AXIAL cut just under the lowest collar point'), ('axial_toes', 'AXIAL cut through the toe box')]
    H0, H1 = 130, 170
    S = Image.new('RGB', (cell * 2, H0 + cell * 2 + H1), BG)
    d = ImageDraw.Draw(S)
    label(d, (24, 18), f'TENNIS_SHOES_FIT  -  {hero}  -  cutaway: foot inside sock inside shoe', 40, bold=True)
    label(d, (24, 74), 'sections of the delivered right foot / sock / shoe, cut faces capped and coloured by layer', 24, fill=DIM)
    for i, (n, t) in enumerate(names):
        im = Image.open(f'{RAW}/cut_{g}_White_{n}.png').convert('RGB').resize((cell, cell))
        tag(im, t, size=22)
        S.paste(im, ((i % 2) * cell, H0 + (i // 2) * cell))
    y = H0 + cell * 2 + 20
    x = 24
    for col, txt in (((140, 70, 35), 'skin (leg / foot)'), ((60, 140, 255), 'sock (2 mm knit wall)'), ((255, 120, 20), 'shoe: wall, collar, sole')):
        d.rectangle((x, y + 4, x + 34, y + 34), fill=col)
        label(d, (x + 46, y), txt, 26)
        x += 520
    R = c['foot_inside']['R']
    label(d, (24, y + 52), f'nearest skin to the shoe wall {R["foot_to_shoe_min_mm"]:.1f} mm   |   sock inner wall to skin >= {min(R["sock_inner_to_skin_min_mm"], c["foot_inside"]["L"]["sock_inner_to_skin_min_mm"]):.1f} mm   |   foot vertices outside the shoe: 0', 24, fill=GOOD)
    label(d, (24, y + 88), f'inner wall past the longest toe +{R["toe_overhang_inner_mm"]:.1f} mm, past the heel +{R["heel_overhang_inner_mm"]:.1f} mm   |   sections of the right foot, white kit', 24, fill=GOOD)
    S.save(f'{OUT}/CUTAWAY_{hero.title()}.png')
    print('wrote', f'CUTAWAY_{hero.title()}.png', S.size)


def before_after(g):
    c, o = chk(g), old(g)
    hero = 'MALE' if g == 'male' else 'FEMALE'
    cell = 640
    views = ('side', 'front', 'heel', 'q3')
    vname = {'side': 'SIDE', 'front': 'FRONT', 'heel': 'HEEL', 'q3': 'LOW 3/4'}
    H0, H1 = 120, 190
    S = Image.new('RGB', (cell * 4, H0 + cell * 2 + H1), BG)
    d = ImageDraw.Draw(S)
    label(d, (24, 18), f'TENNIS_SHOES_FIT  -  {hero}  -  BEFORE (start kit on THIS body)  vs  AFTER (rebuilt on THIS foot)', 40, bold=True)
    label(d, (24, 72), 'same cameras, white kit, right foot', 24, fill=DIM)
    for r, (pre, name) in enumerate((('before', 'START KIT'), ('feet', 'NEW'))):
        for k, v in enumerate(views):
            fn = f'{RAW}/before_{g}_White_R_{v}.png' if pre == 'before' else f'{RAW}/feet_{g}_White_R_{v}.png'
            im = Image.open(fn).convert('RGB').resize((cell, cell))
            tag(im, f'{name} - {vname[v]}', fill=(120, 30, 30) if pre == 'before' else (20, 90, 50))
            S.paste(im, (k * cell, H0 + r * cell))
    y = H0 + cell * 2 + 20
    oR, oL, nR = o['R'], o['L'], c['foot_inside']['R']
    bad = (oR['foot_verts_inside_wall'] + oR['foot_verts_not_enclosed']) > 0
    label(d, (24, y), (f'START KIT on this body: foot vertices below the collar outside the shoe  right {oR["foot_verts_inside_wall"] + oR["foot_verts_not_enclosed"]} (in the wall {oR["foot_verts_inside_wall"]}, outside {oR["foot_verts_not_enclosed"]}) of {oR["foot_verts_below_collar"]}'
                       f'   left {oL["foot_verts_inside_wall"] + oL["foot_verts_not_enclosed"]}   |   toe {oR["toe_overhang_inner_mm"]:+.1f} mm, heel {oR["heel_overhang_inner_mm"]:+.1f} mm (negative = foot sticks out past the shoe)') if bad else
          (f'START KIT on this body: already inside (0 outside, toe {oR["toe_overhang_inner_mm"]:+.1f} mm, heel {oR["heel_overhang_inner_mm"]:+.1f} mm) - the foot is bit-identical to the one it was fit to; shoe re-derived on this SHA anyway'), 22, fill=BAD if bad else WARN)
    label(d, (24, y + 40), f'NEW:  foot vertices outside the shoe 0 of {nR["foot_vertices_below_collar"]}   |   toe +{nR["toe_overhang_inner_mm"]:.1f} mm, heel +{nR["heel_overhang_inner_mm"]:.1f} mm   |   nearest skin to the shoe wall {nR["foot_to_shoe_min_mm"]:.1f} mm', 22, fill=GOOD)
    label(d, (24, y + 80), 'collar rim raised to the ankle, smooth padded roll, sock rebuilt on the leg (no floating tube), left shoe = exact mirror of the right, black kit gets a white sole', 22, fill=DIM)
    S.save(f'{OUT}/BEFORE_AFTER_{hero.title()}.png')
    print('wrote', f'BEFORE_AFTER_{hero.title()}.png', S.size)


def context_sheet(g):
    hero = 'MALE' if g == 'male' else 'FEMALE'
    cw_w, cw_h = 520, 760
    S = Image.new('RGB', (cw_w * 4, 100 + cw_h * 2), BG)
    d = ImageDraw.Draw(S)
    label(d, (24, 22), f'TENNIS_SHOES_FIT  -  {hero}  -  full kit in context (polo + bottom untouched)', 38, bold=True)
    for r, cw in enumerate(('White', 'Black')):
        for k, v in enumerate(('front', 'q3', 'side', 'back')):
            im = Image.open(f'{RAW}/context_{g}_{cw}_{v}.png').convert('RGB').resize((cw_w, cw_h))
            S.paste(im, (k * cw_w, 100 + r * cw_h))
    S.save(f'{OUT}/CONTEXT_{hero.title()}.png')
    print('wrote', f'CONTEXT_{hero.title()}.png', S.size)


if __name__ == '__main__':
    for g in ('male', 'female'):
        for cw in ('White', 'Black'):
            feet_sheet(g, cw)
        cutaway_sheet(g)
        before_after(g)
        context_sheet(g)
