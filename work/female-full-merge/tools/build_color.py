"""Colour variant of the staged female (MATERIALS ONLY - geometry, UVs, normals, groups are not touched).
    blender -b --factory-startup export/HeroBase_Female_FULL_STAGED.blend --python tools/build_color.py -- color/HeroBase_Female_FULL_STAGED_colored.blend color/female_palette.json

Palette = the project's own female values (nothing invented):
  skin  : Unity `HeroBaseFemaleHeadProof.cs` SkinColor (.90,.70,.585), smoothness .40  (FACE_SPEC: 'light warm peach, lighter and pinker than the male tan', roughness .55-.70)
  face  : same file's FaceSlots (brow, sclera, iris, limbal, pupil, catch, lid lines, nostril) + MicroF3's lip palette (data/lip_palette_f3.json: Lip, LipUp, Seam)
  The whole body wears the skin material (head, neck, torso, arms, hands, legs, feet): both Body_F slots point to `Skin_F`; `Base_Grey_F` (the plate's grey mock-neck bodysuit tone) is kept in the file
  with a fake user, so the mannequin look is one slot assignment away.  Hair_F is untouched (hidden, optional asset)."""
import bpy, sys, json
argv = sys.argv[sys.argv.index('--') + 1:]
out_blend, out_json = argv[0], argv[1]
def lin(c): return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
def srgb(c): return tuple(lin(v) for v in c)
SKIN = dict(rgb=(0.90, 0.70, 0.585), smooth=0.40)
FACE = {'Brow': ((.20, .135, .095), .34), 'BrowSoft': ((.33, .23, .17), .30), 'Sclera': ((.86, .85, .84), .62), 'IrisIn': ((.37, .21, .105), .20), 'Iris': ((.30, .17, .085), .20),
        'Limbal': ((.12, .06, .03), .22), 'Pupil': ((.02, .015, .012), .25), 'Catch': ((1.0, 1.0, 1.0), .90), 'LidLine': ((.07, .05, .04), .40), 'LidLower': ((.30, .17, .13), .35),
        'Lip': ((.88, .59, .49), .45), 'LipUp': ((.82, .53, .42), .40), 'Seam': ((.48, .24, .18), .30), 'Nostril': ((.33, .15, .11), .15)}     # last 3 lip entries = MicroF3 palette
SCLERA_EMISSION = (.10, .095, .085)                                                                                                             # Unity: EnableKeyword _EMISSION on the sclera only
import os
# Blender-only preview setting (NOT part of the Unity palette): Principled 'Specular IOR Level' on the very dark paint.  Default 0.5 puts a neutral sun-specular veil (+25..60 sRGB levels) on near-black albedo,
# which greys the brows / iris / pupil compared with the plate.  0.06 keeps the colours the palette defines.
DARK_PAINT = ('Brow', 'BrowSoft', 'LidLine', 'LidLower', 'Limbal', 'Pupil', 'Iris', 'IrisIn', 'Nostril')
SPEC_DARK = float(os.environ.get('SPEC_DARK', '0.06'))
def set_principled(m, rgb, smooth, emis=None, spec=0.5):
    m.use_nodes = True; nt = m.node_tree; b = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    for l in list(nt.links):
        if l.to_node == b and l.to_socket.name == 'Base Color': nt.links.remove(l)               # drop the albedo-atlas link on Skin_F (flat colour instead)
    b.inputs['Base Color'].default_value = srgb(rgb) + (1.0,); b.inputs['Roughness'].default_value = 1.0 - smooth; b.inputs['Metallic'].default_value = 0.0
    b.inputs['Specular IOR Level'].default_value = spec
    if emis is not None: b.inputs['Emission Color'].default_value = srgb(emis) + (1.0,); b.inputs['Emission Strength'].default_value = 1.0
    m.diffuse_color = srgb(rgb) + (1.0,)                                                          # viewport / Workbench colour follows
    for n in [n for n in nt.nodes if n.type == 'TEX_IMAGE' and not any(o.is_linked for o in n.outputs)]: nt.nodes.remove(n)
rep = {'skin': {'srgb': SKIN['rgb'], 'smoothness': SKIN['smooth'], 'roughness': 1 - SKIN['smooth']}, 'face': {}, 'slots_before': {}, 'slots_after': {}}
body = bpy.data.objects['Body_F']; face = bpy.data.objects['Face_F']
skin = bpy.data.materials['Skin_F']; grey = bpy.data.materials['Base_Grey_F']
rep['slots_before'] = {i: s.material.name for i, s in enumerate(body.material_slots)}
set_principled(skin, SKIN['rgb'], SKIN['smooth'])
grey.use_fake_user = True                                                                          # keep the plate's grey bodysuit tone available
for s in body.material_slots:
    if s.material and s.material.name == 'Base_Grey_F': s.material = skin
rep['slots_after'] = {i: s.material.name for i, s in enumerate(body.material_slots)}
for m in [s.material for s in face.material_slots]:
    key = m.name.replace('Face_', '')
    rgb, smooth = FACE[key]; spec = SPEC_DARK if key in DARK_PAINT else 0.5
    set_principled(m, rgb, smooth, emis=SCLERA_EMISSION if key == 'Sclera' else None, spec=spec)
    rep['face'][m.name] = {'srgb': rgb, 'smoothness': smooth, 'hex': '#%02X%02X%02X' % tuple(int(round(c * 255)) for c in rgb), 'blender_specular_ior_level': spec}
rep['skin']['hex'] = '#%02X%02X%02X' % tuple(int(round(c * 255)) for c in SKIN['rgb'])
rep['hair_material_untouched'] = [round(v, 4) for v in bpy.data.materials['Hair_F'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value]
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
json.dump(rep, open(out_json, 'w'), indent=1); print('COLOR_BUILD_OK', json.dumps(rep['slots_after']))
