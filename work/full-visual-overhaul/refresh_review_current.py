import json
import pathlib

repo = pathlib.Path(__file__).resolve().parents[2]
path = repo / 'work/full-visual-overhaul/review-package/manifest-draft.json'
m = json.loads(path.read_text())
m['status'] = 'In progress · character appearance and final motion remain open; phone testing deferred'
m['films'] = []
for item in m['comparisons']:
    if 'golf-pass-18' in item.get('actual', ''):
        item['actual'] = item['actual'].replace('golf-pass-18', 'golf-pass-final')
    if item['title'] == 'Tennis resort showcase':
        item['actual'] = 'proof/full-visual-overhaul/tennis-worlds-pass-17/resort_9_hero_postcard.png'
        item['note'] = 'Actual runtime with rebuilt furnishings, hero-derived crowd and grounded shoes. Walking crowd knees and far footwear are rejected and under repair. Concept parity remains partial.'
    if item['title'] in ('Male character', 'Female character'):
        sex = 'male' if item['title'] == 'Male character' else 'female'
        item['actual'] = f'proof/full-visual-overhaul/character-current-starter-2/{sex}_intro.png'
        item['note'] = 'Fresh production render with the actual starter palette and approved wave animation. Appearance gate remains FAIL: facial finish and clothing shape still fall short of the reference; repairs and a stronger art pass are underway.'
    if item['title'] == 'Four-player lobby':
        item['note'] = 'Actual four-character golf lobby. Complete morph rendering and equipped clubs are verified. Simulator rendering measured about 59.6 FPS; final character assets still require a refresh.'
for item in m['catalog']:
    item['path'] = item['path'].replace('golf-pass-18', 'golf-pass-final').replace('tennis-worlds-pass-11', 'tennis-worlds-pass-17')
m['verification'] = [
    'Character appearance remains FAIL against the intended transformation. New palette, cloth detail and materials are installed; facial finish, clothing shape and deformation still require further work.',
    'Final motion films are pending. Earlier locomotion and dive movies were removed from this review because their capture cadence was not verified against actual Unity frames; real-frame harnesses are now repaired for final recapture.',
    'Golf FINAL: 19/19 exact collision, ground and obstacle invariance checks pass. All routes have actual rendered coverage. Concept material and planting parity remains partial.',
    'Golf completed sole-camera Editor Metal counters: maximum 214 draw calls and 2,000,738 shadow-inclusive triangles. These are Editor measurements, not device FPS.',
    'Actual native four-player Simulator rendering: 59.4 FPS tennis / 59.6 FPS golf with complete characters and equipment. Final character assets require a repeat.',
    'Native live-graph and bundled XCTest pass: 1,073,922 independent Unity vertices across six provisional exports, worst error 0.04 mm. Final accepted assets require fresh exports.',
    'Tennis 17 actual render measurement: resort 2,018,265 triangles / 531 draws; rooftop 1,117,629 / 362; crater 1,267,901 / 303. Measurements are valid; performance acceptance remains open.',
    'Tennis NPC4 inventory PASS: 36 seated + 6 visitors, zero legacy drawable actors. Walking art FAIL: knee gaps, shirt flap and angular far shoes. Source5 is installed; actual review is underway.',
    'Gallery4: all 7 actual seated golf figures reviewed near, mid and far, cheering and in face plates. Solid fitted garments and bounded distant meshes accepted.',
    'Hand diagnostic matches independent source positions/normals, but the authored closed-fist surface remains rejected. It has not been promoted into the main production body.',
    'Per-shoe contact occlusion passes measured-floor and frozen ON/OFF image checks for both bodies in all 3 tennis venues; actual grounding views accepted.',
    'Interim iOS export, local integrated build, signing and installation succeeded. Physical-phone testing is deferred at the user’s request; no valid device performance result has been collected.'
]
m['reports'] = [
    {'title':'Native graph parity · independent 1,073,922-vertex XCTest', 'path':'proof/full-visual-overhaul/native-golden-provisional-2/native-live-graph-parity.txt'},
    {'title':'Golf · final completed frame counters, all 19 routes', 'path':'proof/full-visual-overhaul/golf/catalog-frame-costs-final.json'},
    {'title':'Golf · final exact world physics, all 19 routes', 'path':'proof/full-visual-overhaul/golf/catalog-runtime-physics-final.json'},
    {'title':'Tennis resort · actual measured rendering and NPC inventory; budget open', 'path':'proof/full-visual-overhaul/tennis-costs-17/resort_instancing_on.frame_costs.json'}
]
path.write_text(json.dumps(m, indent=2)+'\n')
