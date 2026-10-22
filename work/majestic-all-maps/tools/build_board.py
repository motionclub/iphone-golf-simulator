# build_board.py: writes board/index.html (the reference board) from the refs, captures and briefs.
import os, re, html
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.join(here, '..'); B = os.path.join(root, 'board')
brief = open(os.path.join(root, 'design', 'HOLE_BRIEFS.md')).read()
rows = {}
for line in brief.splitlines():
    c = [x.strip() for x in line.strip().strip('|').split('|')]
    if len(c) >= 7 and c[0].isdigit(): rows[int(c[0])] = c

courses = [
    ('cliffside', 'Cliffside', 'Morning on the Emerald Coast', 'Fresh morning sea light, a red-and-white lighthouse seen from every tee, shore bands and foam on every island edge.', [7, 8, 9, 12, 15]),
    ('wildisles', 'Wild Isles', 'An adventure archipelago, golden afternoon', 'Six biomes, one per isle, tied together by low golden light and a twin waterfall with a temple seen across the course.', [13, 14, 17, 18, 19, 20]),
    ('magma', 'Magma Open', 'Fire at dawn', 'Blue-violet pre-dawn warming to orange, the caldera volcano seen from every hole, caldera walls hiding the lava disc’s edge.', [10, 16, 21, 22, 23]),
]
par = {7: 4, 8: 4, 9: 5, 12: 3, 15: 3, 13: 5, 14: 4, 17: 5, 18: 3, 19: 4, 20: 4, 10: 4, 16: 4, 21: 3, 22: 4, 23: 5}
vlabel = {'tee': 'Tee', 'flyOpen': 'Intro flyover', 'mid': 'Mid-fairway', 'approach': 'Approach', 'greenBack': 'Green, looking back',
          'offL': 'Off-line, left', 'offR': 'Off-line, right'}
order = ['tee', 'flyOpen', 'mid', 'approach', 'greenBack', 'offL', 'offR']

def card(src_ref, src_now, label, sub, high):
    has_now = src_now and os.path.exists(os.path.join(B, src_now))
    btn = f'<button class="swap" type="button" aria-pressed="false">Show today</button>' if has_now else ''
    now = f'<img class="now" src="{src_now}" alt="Today: {html.escape(label)}" loading="lazy">' if has_now else ''
    q = '<span class="q hi">high</span>' if high else '<span class="q">medium</span>'
    return (f'<figure class="shot{" has-now" if has_now else ""}"><div class="frame"><img class="ref" src="{src_ref}" alt="Target: {html.escape(label)}" loading="lazy">{now}'
            f'<span class="tag">Target</span></div><figcaption><span class="vl">{html.escape(label)}</span>{q}{btn}'
            f'{f"<span class=sub>{html.escape(sub)}</span>" if sub else ""}</figcaption></figure>')

out = []
for key, name, mood, line, holes in courses:
    sec = [f'<section class="course {key}" id="{key}"><header class="ch"><p class="eyebrow">Course · {len(holes)} holes</p><h2>{name}</h2>'
           f'<p class="mood">“{mood}”</p><p class="lede">{line}</p></header>']
    for h in holes:
        r = rows[h]; nn = f'{h:02d}'
        views = [v for v in order if os.path.exists(os.path.join(B, 'img', f'h{nn}_{v}_ref.jpg'))]
        cards = ''.join(card(f'img/h{nn}_{v}_ref.jpg', f'img/h{nn}_{v}_now.jpg', vlabel[v], '', v in ('tee', 'flyOpen')) for v in views)
        sec.append(f'<article class="hole" id="h{nn}"><div class="hh"><p class="num">Hole {h}</p><h3>{html.escape(r[1])}</h3><p class="par">Par {par[h]}</p>'
                   f'<dl class="dirs"><div><dt>Toward the green</dt><dd>{html.escape(r[2])}</dd></div><div><dt>Looking back</dt><dd>{html.escape(r[3])}</dd></div>'
                   f'<div><dt>Left / right</dt><dd>{html.escape(r[4])}</dd></div></dl>'
                   f'<a class="design" href="img/h{nn}_design.jpg" target="_blank" rel="noopener">Design sheet: map, zones, 360°</a></div>'
                   f'<div class="shots">{cards}</div></article>')
    sec.append('</section>')
    out.append(''.join(sec))

weather = [
    ('W01', 'Rain', 'Golf · Cliffside 7', 'W01_golf_h07_rain.jpg', 'W01_now.jpg', 'today: hole 8 rain'),
    ('W02', 'Rain clearing + rainbow', 'Golf · Cliffside 8 (chat 9)', 'W02_golf_h08_rain_clearing_chat9.jpg', None, ''),
    ('W03', 'Thunderstorm', 'Golf · Wild Isles 13', 'W03_golf_h13_thunderstorm.jpg', 'W03_now.jpg', 'today: hole 8 storm'),
    ('W04', 'Sea fog', 'Golf · Cliffside 15', 'W04_golf_h15_seafog.jpg', 'W04_now.jpg', 'today: hole 8 fog'),
    ('W05', 'Gusty', 'Golf · Wild Isles 20', 'W05_golf_h20_gusty.jpg', 'W05_now.jpg', 'today: hole 8 gusty'),
    ('W06', 'Snow', 'Golf · Frostbite Fjord 17', 'W06_golf_h17_snow.jpg', 'W06_now.jpg', 'today: hole 17 blizzard'),
    ('W07', 'Blizzard', 'Golf · Frostbite Fjord 17', 'W07_golf_h17_blizzard.jpg', 'W07_now.jpg', 'today: hole 17 blizzard'),
    ('W08', 'Freezing fog', 'Golf · Frostbite Fjord 17', 'W08_golf_h17_freezingfog.jpg', 'W08_now.jpg', 'today: hole 17 blizzard'),
    ('W09', 'Ashfall', 'Golf · Magma 22', 'W09_golf_h22_ashfall.jpg', None, ''),
    ('W10', 'Eruption', 'Golf · Magma 23', 'W10_golf_h23_eruption.jpg', 'W10_now.jpg', 'today: hole 21 eruption'),
    ('W11', 'Volcanic smoke', 'Golf · Magma 21', 'W11_golf_h21_smoke.jpg', None, ''),
    ('W12', 'Rain', 'Tennis · Resort', 'W12_tennis_resort_rain.jpg', 'W12_now.jpg', 'today: resort rain'),
    ('W13', 'Sea fog', 'Tennis · Resort', 'W13_tennis_resort_seafog.jpg', 'W13_now.jpg', 'today: resort fog'),
    ('W14', 'Thunderstorm', 'Tennis · Skyscraper', 'W14_tennis_skyscraper_thunderstorm.jpg', None, ''),
    ('W15', 'Gusty', 'Tennis · Skyscraper', 'W15_tennis_skyscraper_gusty.jpg', None, ''),
    ('W16', 'Volcanic smoke', 'Tennis · Volcano', 'W16_tennis_volcano_smoke.jpg', None, ''),
]
wcards = ''.join(card(f'img/{f}', f'img/{n}' if n else None, f'{t}', f'{p}{" · " + nl if nl else ""}', True).replace('<figure class="shot', f'<figure data-id="{i}" class="shot') for i, t, p, f, n, nl in weather)

page = open(os.path.join(here, 'board_template.html')).read()
page = page.replace('{{COURSES}}', '\n'.join(out)).replace('{{WEATHER}}', wcards)
open(os.path.join(B, 'index.html'), 'w').write(page)
print('ok', len(page))
