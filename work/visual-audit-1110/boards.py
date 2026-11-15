#!/usr/bin/env python3
"""Evidence boards for AUDIT.md: panels side by side, red numbered circles (coords = fractions of each panel)."""
from PIL import Image, ImageDraw, ImageFont
F = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)
RED = (255, 40, 60)
def panel(src, box, marks, label, h):
    im = Image.open(src).convert('RGB')
    if box: im = im.crop(box)
    im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS); d = ImageDraw.Draw(im)
    for cx, cy, r, n in marks:
        x, y, R = cx * im.width, cy * im.height, r * im.width
        for k in range(4): d.ellipse([x - R - k, y - R - k, x + R + k, y + R + k], outline=RED)
        bx, by = x + R * .7, y - R * .7
        d.ellipse([bx - 15, by - 15, bx + 15, by + 15], fill=RED); d.text((bx, by), str(n), fill='white', font=F(20), anchor='mm')
    w = d.textlength(label, font=F(16)) + 12
    d.rectangle([0, h - 24, w, h], fill=(0, 0, 0)); d.text((6, h - 21), label, fill='white', font=F(16))
    return im
def strip(panels, h, maxw):
    ims = [panel(*p, h) for p in panels]; W = sum(i.width for i in ims) + 6 * (len(ims) - 1)
    b = Image.new('RGB', (W, h), (20, 20, 20)); x = 0
    for i in ims: b.paste(i, (x, 0)); x += i.width + 6
    return b.resize((maxw, round(h * maxw / W)), Image.LANCZOS)
def board(out, panels, h=560, maxw=2200):
    rows = panels if isinstance(panels[0], list) else [panels]
    strips = [strip(r, h, maxw) for r in rows]
    b = Image.new('RGB', (maxw, sum(s.height for s in strips) + 6 * (len(strips) - 1)), (20, 20, 20)); y = 0
    for st in strips: b.paste(st, (0, y)); y += st.height + 6
    b.save('evidence/' + out, quality=90); print(out, b.size)
S = 'shots/'
board('01_menu_hero.jpg', [
    (S+'menus/comp/01_home.jpg', (780,200,1180,700), [(.43,.2,.14,1),(.13,.72,.1,1),(.45,.52,.2,2)], 'Menu home (in game)'),
    (S+'hero_turnaround/MatchHero_Male/ready_face_front.jpg', None, [], 'Same hero, neutral studio light (blue shirt pick)'),
    (S+'hero_turnaround/MatchHero_Male/ready_full_front.jpg', (300,0,780,1080), [], 'Same hero, studio'),
    (S+'menus/comp/02_sport.jpg', (700,150,1300,560), [(.42,.37,.09,3)], 'Sport picker'),
])
board('02_golf_fog.jpg', [
    (S+'golf_courses/hole13_gameplay.jpg', None, [(.85,.115,.12,2),(.5,.33,.2,1)], 'Hole 13 tee, SEA FOG'),
    (S+'golf_courses/hole20_putting.jpg', None, [(.5,.62,.28,1)], 'Hole 20 green, SEA FOG'),
    (S+'golf_courses/hole10_gameplay.jpg', None, [(.85,.115,.12,2),(.55,.3,.2,1)], 'Hole 10 tee, VOLCANIC SMOKE'),
    (S+'golf_courses/hole07_gameplay.jpg', None, [(.85,.115,.12,2),(.5,.28,.2,1)], 'Hole 07 tee, SEA FOG'),
    (S+'golf_courses/hole08_gameplay.jpg', None, [], 'Hole 08, clear (for comparison)'),
], h=760)
board('03_character_lighting.jpg', [
    (S+'tennis_venue_volcano/volcano_7_rear.jpg', (648,560,1248,1080), [(.5,.6,.22,1)], 'Volcano: rival blown orange'),
    (S+'tennis_venue_volcano/volcano_9_hero_postcard.jpg', (750,480,1350,1000), [(.5,.55,.25,2)], 'Volcano: player in daylight'),
    (S+'golf_courses/hole22_gameplay.jpg', (0,500,900,1300), [(.3,.42,.25,2)], 'Golf lava hole: golfer in daylight'),
    (S+'golf_courses/hole07_character_face.jpg', None, [(.38,.42,.2,3)], 'Golf close-up: flat orange skin'),
    ('review/z_feet_tennis.jpg', None, [(.5,.72,.28,4)], 'Tennis: faint ground shadow, cream whites'),
])
board('04_tennis_vs_target.jpg', [[
    (S+'tennis_film/f_0178_hitPerfect_Rally.jpg', None, [(.365,.76,.06,1),(.5,.94,.09,2),(.07,.87,.07,3),(.862,.9,.045,4),(.5,.55,.1,5)], 'Game: PERFECT hit'),
    ('targets/tennis_video/f_004.jpg', None, [], 'Approved target: hit')], [
    (S+'tennis_film/f_1032_PointOver.jpg', None, [(.5,.5,.2,6)], 'Game: point won'),
    ('targets/tennis_video/f_014.jpg', None, [], 'Approved target: point won')]], h=420)
board('05_bowling.jpg', [[
    (S+'bowl_club/stills/setup.jpg', None, [(.12,.42,.09,1),(.9,.42,.09,1),(.5,.1,.13,2)], 'Club Lanes, bowling view'),
    (S+'bowl_club/stills/pins.jpg', None, [(.5,.45,.15,3)], 'Club Lanes, pin camera'),
    ('../bowling-look/refs/targets/club_setup_small.jpg', None, [], 'Target for Club Lanes')], [
    ('review/z_bowl_crowd.jpg', None, [(.4,.42,.16,4)], 'Crowd'),
    ('review/z_bowl_shirt.jpg', None, [(.37,.3,.14,5),(.37,.62,.11,6)], 'Bowler after the ball'),
    (S+'bowl_neon/stills/pins.jpg', None, [(.5,.45,.15,3)], 'Neon Nights, pin camera')]], h=420)
board('06_ui.jpg', [[
    (S+'golf_results_ui/res_roundcard.jpg', None, [(.5,.32,.16,1),(.5,.88,.15,2)], 'Golf round card'),
    (S+'golf_results_ui/res_shot_result.jpg', (1300,500,1920,1080), [(.47,.88,.2,3)], 'Golf shot result')], [
    (S+'golf_review/12-6-read.jpg', (0,1900,1080,2340), [(.4,.62,.2,4)], 'Golf putt, handheld'),
    (S+'golf_courses/hole07_gameplay.jpg', (0,1250,900,1600), [(.5,.65,.2,5)], 'Golf handheld controls'),
    (S+'tennis_film/f_0384_PlayerServeToss.jpg', None, [(.36,.94,.08,6),(.9,.45,.08,7)], 'Tennis serve')]], h=420)
board('07_hands_cloth.jpg', [
    ('review/z_hand_f.jpg', None, [(.45,.5,.3,1)], 'Female racket hand'),
    (S+'golf_courses/hole07_character_full.jpg', None, [(.62,.3,.13,2),(.63,.72,.13,3),(.3,.53,.09,4)], 'Golf address close-up'),
    (S+'golf_courses/hole07_character_face.jpg', None, [(.62,.72,.2,2)], 'Golf polo in sun'),
    (S+'hero_turnaround/MatchHero_Male/ready_hand_right_front.jpg', None, [], 'Male racket hand (for comparison)'),
])
