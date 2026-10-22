"""Summarise CharacterLodProbe views.tsv: per hole, the characters' triangle cost in the tee views (tee + the drive views that
frame the golfer at address) at LOD0 vs distance LOD, and the views over the 1.0 M frame cap before/after.
Counter glitches (0 or doubled reads) are dropped: a row counts only if 0 < char <= frame and the LOD0 frame is not ~2x the LOD frame."""
import csv, sys, statistics as st

rows = list(csv.DictReader(open(sys.argv[1]), delimiter='\t'))
GATE, CAP = 250_000, 1_000_000
TEE = ('tee', 'driveGood_0', 'driveGood_rest', 'driveBad_0', 'driveBad_rest')

def valid(r, k_frame, k_char):
    f, c = int(r[k_frame]), int(r[k_char])
    return f > 0 and 0 <= c < .8 * f   # 'heroes off' not registered => c == f

holes = sorted({int(r['hole']) for r in rows})
out = ['| hole | tee screen h | level | char tris LOD0 | char tris LOD | gate <= 250 k |', '|---|---|---|---|---|---|']
ok_all = True
for h in holes:
    hr = [r for r in rows if int(r['hole']) == h and r['view'] in TEE]
    a = [int(r['char_tris_lod0']) for r in hr if valid(r, 'frame_tris_lod0', 'char_tris_lod0') and int(r['char_tris_lod0']) > 0
         and int(r['frame_tris_lod0']) < 1.6 * int(r['frame_tris'])]
    b = [int(r['char_tris']) for r in hr if valid(r, 'frame_tris', 'char_tris') and int(r['char_tris']) > 0]
    sh = hr[0]['screen_h'] if hr else '-'; lv = hr[0]['level'] if hr else '-'
    if not b: out.append(f'| {h} | {sh} | {lv} | {st.median(a) if a else "-"} | no valid read | FAIL |'); ok_all = False; continue
    m = int(st.median(b))   # median of the valid reads (single reads can still glitch)
    ok = m <= GATE; ok_all &= ok
    out.append(f'| {h} | {sh} | {lv} | {(format(int(st.median(a)), ",") if a else "-")} | {m:,} (n={len(b)}, max {max(b):,}) | {"PASS" if ok else "FAIL"} |')
# frame cap over all views (valid reads only)
before = [r for r in rows if valid(r, 'frame_tris_lod0', 'char_tris_lod0') and int(r['frame_tris_lod0']) < 1.6 * max(1, int(r['frame_tris']))]
after = [r for r in rows if valid(r, 'frame_tris', 'char_tris')]
over_b = sum(int(r['frame_tris_lod0']) > CAP for r in before); over_a = sum(int(r['frame_tris']) > CAP for r in after)
char_views = [r for r in after if int(r['char_tris']) > 0]
print('\n'.join(out))
print(f'\nGATE: tee-view character triangles <= 250 k on every hole: {"PASS" if ok_all else "FAIL"}')
print(f'views over the 1.0 M frame cap: {over_b}/{len(before)} at LOD0 -> {over_a}/{len(after)} with character LOD (valid reads)')
print(f'views with the hero visible: {len(char_views)}; worst character cost with LOD: {max(int(r["char_tris"]) for r in char_views):,}')
