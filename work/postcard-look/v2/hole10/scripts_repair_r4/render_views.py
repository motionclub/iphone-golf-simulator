"""v2 (2026-10-04 continue, second round): the preview imitates the UNITY look more closely than v1 (v1 = tools/render_views_v1.py):
  * camera rays see Sky_Crater_C.png through the TennisSky mapping (v = 1.35 x elevation / 90 deg, heading folded with a triangle wave, arc 180,
    heading = tee->pin 57.7 deg), the LIGHTING comes from GolfAtmosphere.Holes[10]'s trilight (sky .34 .24 .40 / equator .55 .30 .22 / ground .60 .22 .08)
  * GolfLook.Table tints: every LK_ lit material x .94, LK_BASALT x (.52 .80 .92) matte (no specular) with emission x (1 .80 .50), LK_LAVA x .75 matte,
    emission x (1 .65 .50); HoleTint of hole 10 on LK_FAIRWAY / LK_GREEN (.90 1.15 .62) and LK_ROUGH (.90 1.10 .62)
  * linear fog 120 .. 1000 yd, colour (.42 .19 .14), mixed into every opaque material
  * --mask : category colour pass (lava red, rock/basalt blue, ground green, plants dark green, cone cyan, smoke yellow, sky black) for the
    lava-share / skyline measurements
  Still NOT the Game view: no GolfLava shader (the lava is the Principled stand-in), no per-object light limit, no LAVA_LIGHT point lights.

Blender EEVEE previews of a staged hole 10 blend from the SAME camera rigs the Game view uses (NOT Game-view proof).

  Blender -b STAGED.blend --python render_views.py -- --shots landmarks.json --out DIR [--only tee,approach] [--res 900x1600] [--samples 24] [--prefix p_]

shots JSON = the stills schema of work/postcard-look/RUNTIME.md v2.8 (address: ball/aim in course yards; landmark: pos/look in Unity WORLD
YARDS, fov vertical degrees) plus an optional "aerial" kind: {"kind": "aerial", "pos": [x, y, z], "look": [x, y, z], "fov": 40} in the same
world yards. Mapping (HoleView.BuildFromModel): course x = Blender x / 0.9144, course d (= Unity z) = Blender y / 0.9144, Unity y = Blender z x 1.0936.
CameraRig.FrameAddress: camera = ball - aim x 4.5 yd + 2.4 yd up, looks at ball + aim x 1.5 yd, fov 60 (vertical), 900 x 1600.
Lighting imitates GolfAtmosphere.Holes[10] (key 2.3 at az heading+40 / el 32, warm (1,.80,.58); trilight-ish dusk world); there is no fog and no
GolfLava shader here: the lava is the Principled preview of LK_LAVA. These are shape / scale previews only.
"""
import sys
import os
import json
import math

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

YD = 0.9144
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d=None):
    return args[args.index(n) + 1] if n in args else d


SHOTS = json.load(open(opt("--shots")))["shots"]
OUT = opt("--out")
ONLY = opt("--only")
PREFIX = opt("--prefix", "")
RES = tuple(int(v) for v in opt("--res", "900x1600").split("x"))
SAMPLES = int(opt("--samples", "24"))
EXPOSURE = float(opt("--exposure", "0.0"))
os.makedirs(OUT, exist_ok=True)
GROUND = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH")


def ground_bvh():
    V, F = [], []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not ob.name.startswith(GROUND):
            continue
        me = ob.data
        mw = ob.matrix_world
        base = len(V)
        V += [tuple(mw @ v.co) for v in me.vertices]
        for p in me.polygons:
            F.append(tuple(base + i for i in p.vertices))
    return BVHTree.FromPolygons(V, F)


BVH = ground_bvh()


def ground_z(x, y):
    hit = BVH.ray_cast(Vector((x, y, 60.0)), Vector((0, 0, -1)), 200.0)
    return None if hit[0] is None else hit[0].z


MASK = "--mask" in args
FLAT_GRASS = "--flat-grass" in args   # repair round 4: LK_FAIRWAY / LK_GREEN / LK_ROUGH = their MEAN albedo, flat normal (no mow bands, no sheen, no blade streaks): the tee-edge CONTRAST gate compares the ribbon with the grass material, not with a stripe
PLAIN = "--plain" in args            # the v1 look (no Unity tints / fog / painted sky)
LOOK_DIR = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look"


def srgb_to_lin(c):
    return tuple(((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c)


def _mult_input(nt, bsdf, name, rgb_lin):
    """Multiply whatever feeds Principled input `name` (or its default colour) by a linear RGB."""
    inp = bsdf.inputs[name]
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 1.0
    if inp.is_linked:
        lk = inp.links[0]
        src = lk.from_socket
        nt.links.remove(lk)
        nt.links.new(src, mix.inputs[6])
    else:
        mix.inputs[6].default_value = tuple(inp.default_value)
    mix.inputs[7].default_value = (rgb_lin[0], rgb_lin[1], rgb_lin[2], 1.0)
    nt.links.new(mix.outputs[2], inp)


def _principled(m):
    for n in m.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeBsdfPrincipled':
            return n
    return None


def _add_fog(m, start_m=120 * YD, end_m=1000 * YD, color=(.42, .19, .14)):
    nt = m.node_tree
    out = next((n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial'), None)
    if out is None or not out.inputs['Surface'].is_linked:
        return
    lk = out.inputs['Surface'].links[0]
    src = lk.from_socket
    cam = nt.nodes.new("ShaderNodeCameraData")
    mp = nt.nodes.new("ShaderNodeMapRange")
    mp.clamp = True
    mp.inputs[1].default_value, mp.inputs[2].default_value = start_m, end_m
    mp.inputs[3].default_value, mp.inputs[4].default_value = 0.0, 1.0
    nt.links.new(cam.outputs["View Distance"], mp.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*srgb_to_lin(color), 1.0)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.remove(lk)
    nt.links.new(mp.outputs[0], mx.inputs[0])
    nt.links.new(src, mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])


def lava_standin(m):
    """GolfArcade/GolfLava replica: self-lit, heat = saturate(((lum(C) x 1.5 + lum(E) x 1.5 - .15) - .5) x 1.4 + .5), 4-stop ramp Deep/Crust/Flow/Hot (sRGB stops as GolfLook.Table)."""
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
    uvn = nt.nodes.new("ShaderNodeUVMap")
    imgs = []
    for stem in ("Lava_C", "Lava_E"):
        im = bpy.data.images.load(os.path.join(LOOK_DIR, stem + ".png"), check_existing=False)
        im.colorspace_settings.name = 'Non-Color'
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = im
        nt.links.new(uvn.outputs[0], n.inputs[0])
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(n.outputs[0], bw.inputs[0])
        imgs.append(bw)
    a = nt.nodes.new("ShaderNodeMath"); a.operation = 'MULTIPLY'; a.inputs[1].default_value = 1.5
    nt.links.new(imgs[0].outputs[0], a.inputs[0])
    b = nt.nodes.new("ShaderNodeMath"); b.operation = 'MULTIPLY_ADD'; b.inputs[1].default_value = 1.5; b.inputs[2].default_value = -0.15
    nt.links.new(imgs[1].outputs[0], b.inputs[0])
    c = nt.nodes.new("ShaderNodeMath"); c.operation = 'ADD'
    nt.links.new(a.outputs[0], c.inputs[0]); nt.links.new(b.outputs[0], c.inputs[1])
    d = nt.nodes.new("ShaderNodeMath"); d.operation = 'SUBTRACT'; d.inputs[1].default_value = 0.5
    nt.links.new(c.outputs[0], d.inputs[0])
    e = nt.nodes.new("ShaderNodeMath"); e.operation = 'MULTIPLY_ADD'; e.inputs[1].default_value = 1.4; e.inputs[2].default_value = 0.5; e.use_clamp = True
    nt.links.new(d.outputs[0], e.inputs[0])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    ramp = cr.color_ramp
    ramp.color_mode = 'RGB'
    ramp.interpolation = 'LINEAR'
    stops = [(0.0, (150, 33, 10)), (0.2, (186, 43, 13)), (0.6, (224, 79, 17)), (1.0, (255, 128, 28))]
    while len(ramp.elements) < 4:
        ramp.elements.new(0.5)
    for el, (p, rgb) in zip(ramp.elements, stops):
        el.position = p
        el.color = (*srgb_to_lin(tuple(v / 255.0 for v in rgb)), 1.0)
    nt.links.new(e.outputs[0], cr.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(cr.outputs[0], em.inputs[0])
    old = out.inputs['Surface'].links[0]
    nt.links.remove(old)
    nt.links.new(em.outputs[0], out.inputs['Surface'])


HOLE_TINT = {"LK_FAIRWAY": (.90, 1.15, .62), "LK_GREEN": (.90, 1.15, .62), "LK_ROUGH": (.90, 1.10, .62)}


def unity_materials():
    for m in bpy.data.materials:
        if not m.use_nodes or m.node_tree is None:
            continue
        if m.name.split(".")[0] == "LK_LAVA":
            lava_standin(m)
            _add_fog(m)
            continue
        b = _principled(m)
        nm = m.name.split(".")[0]
        if b is not None and nm.startswith("LK_") and nm not in ("LK_SMOKE", "LK_SURF", "LK_FALL"):
            tint = (.94, .94, .94)
            if nm == "LK_BASALT":
                tint = (.52, .80, .92)
            elif nm == "LK_LAVA":
                tint = (.75, .75, .75)
            elif nm == "LK_ROCK_WET":
                tint = (.68, .70, .70)
            elif nm == "LK_SAND":
                tint = (.80, .80, .80)
            if nm in HOLE_TINT:
                tint = HOLE_TINT[nm]
            if FLAT_GRASS and nm in ("LK_FAIRWAY", "LK_GREEN", "LK_ROUGH"):
                bc = b.inputs["Base Color"]
                if bc.is_linked:
                    img = next((n_.image for n_ in m.node_tree.nodes if n_.bl_idname == 'ShaderNodeTexImage' and n_.image is not None and n_.image.name.endswith("_C.png")), None)   # the colour map (a Gamma node sits between it and the BSDF)
                    if img is not None:
                        w_, h_ = img.size
                        px_ = np.empty(w_ * h_ * 4, np.float32)
                        img.pixels.foreach_get(px_)
                        rgb_ = px_.reshape(-1, 4)[:, :3].astype(np.float64)
                        lin_ = np.where(rgb_ <= 0.04045, rgb_ / 12.92, ((rgb_ + 0.055) / 1.055) ** 2.4)          # Image.pixels of an sRGB PNG are the encoded values
                        m.node_tree.links.remove(bc.links[0])
                        bc.default_value = (*[float(v) for v in lin_.mean(axis=0)], 1.0)
                nin = b.inputs["Normal"]
                while nin.is_linked:
                    m.node_tree.links.remove(nin.links[0])
                b.inputs["Roughness"].default_value = 0.85
            _mult_input(m.node_tree, b, "Base Color", srgb_to_lin(tint))
            if nm in ("LK_BASALT", "LK_LAVA"):
                for sk in ("Specular IOR Level",):
                    if sk in b.inputs:
                        b.inputs[sk].default_value = 0.0
                b.inputs["Roughness"].default_value = 1.0
                if "Emission Strength" in b.inputs:
                    b.inputs["Emission Strength"].default_value = 1.0
                em = (1.0, .80, .50) if nm == "LK_BASALT" else (1.0, .65, .50)
                _mult_input(m.node_tree, b, "Emission Color", em)
        if not (nm in ("LK_SMOKE", "LK_SURF", "LK_FALL")):
            _add_fog(m)


def mask_materials():
    cols = {"lava": (1, 0, 0), "rock": (0, 0, 1), "ground": (0, 1, 0), "plant": (0, .4, 0), "tuft": (0, .8, .2), "cone": (0, 1, 1), "smoke": (1, 1, 0), "other": (.5, .5, .5)}      # round 4: + "tuft" (PLANT_TUFT_*, the grass fringe)
    mats = {}
    for k, c in cols.items():
        m = bpy.data.materials.new("MASK_" + k)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = (*c, 1.0)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs[0], out.inputs[0])
        mats[k] = m
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        n = ob.name
        if n.startswith("WATER_LAVA"):
            k = "lava"
        elif n.startswith("DRESS_CONE"):
            k = "cone"
        elif n.startswith("DRESS_SMOKE"):
            ob.hide_render = True            # alpha cards: not part of the geometry shares
            continue
        elif n.startswith("PLANT_TUFT"):
            k = "tuft"
        elif n.startswith("PLANT_"):
            k = "plant"
        elif n.startswith("ROCK_"):
            k = "rock"
        elif n.startswith(GROUND):
            k = "ground"
        else:
            k = "other"
        me = ob.data
        if me.users > 1 and getattr(me, "_mask_done", False):
            continue
        me.materials.clear()
        me.materials.append(mats[k])
        for p in me.polygons:
            p.material_index = 0
    return mats


def lava_lights():
    """GolfLook.DressModel: one point light per LAVA_LIGHT_nn empty, colour (1, .45, .12), range 52 yd, intensity 600 (URP: 1/d^2, d in yards), lifted 4 yd.
    Blender power for the same irradiance as the key (2.3 <-> sun strength 2.3 x pi x .9): P = 4 pi^2 x .9 pi x 600 / .9144^2 = ~80 kW."""
    sc = bpy.context.scene
    n = 0
    for ob in list(bpy.data.objects):
        if ob.name.startswith("LAVA_LIGHT"):
            ld = bpy.data.lights.new("PV_" + ob.name, 'POINT')
            ld.energy = 4 * math.pi ** 2 * 0.9 * math.pi * 600.0 / (YD * YD)
            ld.color = (1.0, 0.45, 0.12)
            ld.shadow_soft_size = 0.5
            ld.use_custom_distance = True
            ld.cutoff_distance = 52.0 * YD
            lo = bpy.data.objects.new("PV_" + ob.name, ld)
            sc.collection.objects.link(lo)
            p = ob.matrix_world.translation
            lo.location = (p.x, p.y, p.z + 4.0 * YD)
            n += 1
    print(f"[render_views] {n} lava point lights", flush=True)


def setup_light(heading_deg=57.7):
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)
    az, el = math.radians(heading_deg + 40.0), math.radians(32.0)
    to_sun = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    ld = bpy.data.lights.new("PV_SUN", 'SUN')
    ld.energy = 2.3 * math.pi * 0.9
    ld.color = (1.0, 0.80, 0.58)
    ld.angle = math.radians(3.0)
    so = bpy.data.objects.new("PV_SUN", ld)
    sc.collection.objects.link(so)
    so.rotation_euler = to_sun.to_track_quat('Z', 'Y').to_euler()
    w = bpy.data.worlds.new("PV_WORLD")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    outn = nt.nodes.new("ShaderNodeOutputWorld")
    if MASK:
        bg = nt.nodes.new("ShaderNodeBackground")
        bg.inputs[0].default_value = (0, 0, 0, 1)
        nt.links.new(bg.outputs[0], outn.inputs[0])
    elif PLAIN:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        bg = nt.nodes.new("ShaderNodeBackground")
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        mp = nt.nodes.new("ShaderNodeMapRange")
        mp.inputs[1].default_value, mp.inputs[2].default_value = 0.45, 0.95
        nt.links.new(sep.outputs["Z"], mp.inputs[0])
        nt.links.new(mp.outputs[0], ramp.inputs[0])
        cr = ramp.color_ramp
        cr.elements[0].position, cr.elements[0].color = 0.0, (0.80, 0.30, 0.10, 1)
        cr.elements[1].position, cr.elements[1].color = 1.0, (0.10, 0.06, 0.12, 1)
        nt.links.new(ramp.outputs[0], bg.inputs[0])
        bg.inputs[1].default_value = 1.0
        nt.links.new(bg.outputs[0], outn.inputs[0])
    else:
        N = nt.nodes
        L = nt.links
        tc = N.new("ShaderNodeTexCoord")
        nrm = N.new("ShaderNodeVectorMath"); nrm.operation = 'NORMALIZE'
        L.new(tc.outputs["Generated"], nrm.inputs[0])
        sep = N.new("ShaderNodeSeparateXYZ")
        L.new(nrm.outputs[0], sep.inputs[0])
        # elevation 0..1 -> v = saturate(1.35 x elevation)
        asn = N.new("ShaderNodeMath"); asn.operation = 'ARCSINE'; asn.use_clamp = True
        L.new(sep.outputs["Z"], asn.inputs[0])
        el = N.new("ShaderNodeMath"); el.operation = 'MULTIPLY'; el.inputs[1].default_value = 1.35 / (math.pi / 2)
        L.new(asn.outputs[0], el.inputs[0])
        vcl = N.new("ShaderNodeMath"); vcl.operation = 'MAXIMUM'; vcl.inputs[1].default_value = 0.0
        L.new(el.outputs[0], vcl.inputs[0])
        vcl2 = N.new("ShaderNodeMath"); vcl2.operation = 'MINIMUM'; vcl2.inputs[1].default_value = 1.0
        L.new(vcl.outputs[0], vcl2.inputs[0])
        # heading (deg, from +D toward +X) relative to the painting centre: rel = az - H + 90, u = |wrap(rel, -180, 180)| / 180
        at2 = N.new("ShaderNodeMath"); at2.operation = 'ARCTAN2'
        L.new(sep.outputs["X"], at2.inputs[0]); L.new(sep.outputs["Y"], at2.inputs[1])
        dg = N.new("ShaderNodeMath"); dg.operation = 'MULTIPLY'; dg.inputs[1].default_value = 180.0 / math.pi
        L.new(at2.outputs[0], dg.inputs[0])
        rel = N.new("ShaderNodeMath"); rel.operation = 'ADD'; rel.inputs[1].default_value = 90.0 - heading_deg
        L.new(dg.outputs[0], rel.inputs[0])
        wr = N.new("ShaderNodeMath"); wr.operation = 'WRAP'; wr.inputs[1].default_value = 180.0; wr.inputs[2].default_value = -180.0
        L.new(rel.outputs[0], wr.inputs[0])
        ab = N.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'
        L.new(wr.outputs[0], ab.inputs[0])
        uu = N.new("ShaderNodeMath"); uu.operation = 'DIVIDE'; uu.inputs[1].default_value = 180.0
        L.new(ab.outputs[0], uu.inputs[0])
        comb = N.new("ShaderNodeCombineXYZ")
        L.new(uu.outputs[0], comb.inputs[0]); L.new(vcl2.outputs[0], comb.inputs[1])
        img = N.new("ShaderNodeTexImage")
        img.image = bpy.data.images.load(os.path.join(LOOK_DIR, "Sky_Crater_C.png"), check_existing=True)
        img.image.colorspace_settings.name = 'sRGB'
        img.extension = 'EXTEND'
        img.interpolation = 'Linear'
        L.new(comb.outputs[0], img.inputs[0])
        sky_bg = N.new("ShaderNodeBackground"); sky_bg.inputs[1].default_value = 0.9       # SkyExposure
        L.new(img.outputs[0], sky_bg.inputs[0])
        # below the horizon: the sea colour (.30 .12 .08) over smoothstep(0, .1, -dir.z)
        neg = N.new("ShaderNodeMapRange"); neg.interpolation_type = 'SMOOTHSTEP'; neg.clamp = True
        neg.inputs[1].default_value, neg.inputs[2].default_value = 0.0, 0.1
        zneg = N.new("ShaderNodeMath"); zneg.operation = 'MULTIPLY'; zneg.inputs[1].default_value = -1.0
        L.new(sep.outputs["Z"], zneg.inputs[0]); L.new(zneg.outputs[0], neg.inputs[0])
        sea = N.new("ShaderNodeRGB"); sea.outputs[0].default_value = (*srgb_to_lin((.30, .12, .08)), 1.0)
        mixsea = N.new("ShaderNodeMix"); mixsea.data_type = 'RGBA'
        L.new(neg.outputs[0], mixsea.inputs[0]); L.new(img.outputs[0], mixsea.inputs[6]); L.new(sea.outputs[0], mixsea.inputs[7])
        L.new(mixsea.outputs[2], sky_bg.inputs[0])
        # ambient (everything that is not a camera ray): GolfAtmosphere trilight sky / equator / ground by dir.z
        zc = N.new("ShaderNodeMath"); zc.operation = 'ABSOLUTE'
        L.new(sep.outputs["Z"], zc.inputs[0])
        cols = {"sky": srgb_to_lin((.34, .24, .40)), "eq": srgb_to_lin((.55, .30, .22)), "gr": srgb_to_lin((.60, .22, .08))}
        mk = {}
        for k, c in cols.items():
            n_ = N.new("ShaderNodeRGB"); n_.outputs[0].default_value = (*c, 1.0); mk[k] = n_
        up = N.new("ShaderNodeMix"); up.data_type = 'RGBA'
        L.new(zc.outputs[0], up.inputs[0]); L.new(mk["eq"].outputs[0], up.inputs[6]); L.new(mk["sky"].outputs[0], up.inputs[7])
        dn = N.new("ShaderNodeMix"); dn.data_type = 'RGBA'
        L.new(zc.outputs[0], dn.inputs[0]); L.new(mk["eq"].outputs[0], dn.inputs[6]); L.new(mk["gr"].outputs[0], dn.inputs[7])
        isup = N.new("ShaderNodeMath"); isup.operation = 'GREATER_THAN'; isup.inputs[1].default_value = 0.0
        L.new(sep.outputs["Z"], isup.inputs[0])
        pick = N.new("ShaderNodeMix"); pick.data_type = 'RGBA'
        L.new(isup.outputs[0], pick.inputs[0]); L.new(dn.outputs[2], pick.inputs[6]); L.new(up.outputs[2], pick.inputs[7])
        amb_bg = N.new("ShaderNodeBackground"); amb_bg.inputs[1].default_value = 1.0
        L.new(pick.outputs[2], amb_bg.inputs[0])
        lp = N.new("ShaderNodeLightPath")
        mx = N.new("ShaderNodeMixShader")
        L.new(lp.outputs["Is Camera Ray"], mx.inputs[0]); L.new(amb_bg.outputs[0], mx.inputs[1]); L.new(sky_bg.outputs[0], mx.inputs[2])
        L.new(mx.outputs[0], outn.inputs[0])
    sc.world = w
    try:
        sc.view_settings.view_transform = 'Standard'
        sc.view_settings.exposure = EXPOSURE
        if MASK:
            sc.view_settings.look = 'None'
            sc.render.filter_size = 0.5
    except Exception:
        pass
    sc.render.engine = 'BLENDER_EEVEE'
    for nm in ("BALL_START", "HOLE_CUP", "MARKER_TEE", "MARKER_PIN", "MARKER_UP"):
        o = bpy.data.objects.get(nm)
        if o is not None:
            o.hide_render = True
    if MASK:
        mask_materials()
    elif not PLAIN:
        unity_materials()
        lava_lights()


def make_cam(name, loc, look, fov_deg):
    cd = bpy.data.cameras.new(name)
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(fov_deg)
    cd.clip_start = 0.27
    cd.clip_end = 3000.0
    return ob


def world_to_blender(p):
    return Vector((p[0] * YD, p[2] * YD, p[1] / 1.0936))


def render(cam, path):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = 100
    sc.render.filepath = path
    sc.render.image_settings.file_format = 'PNG'
    try:
        sc.eevee.taa_render_samples = SAMPLES
    except Exception:
        pass
    bpy.ops.render.render(write_still=True)


setup_light()
for sh in SHOTS:
    if sh.get("hole", 10) != 10:
        continue
    if ONLY and sh["name"].split("_")[-1] not in ONLY.split(",") and sh["name"] not in ONLY.split(","):
        continue
    kind = sh.get("kind", "landmark" if "pos" in sh else "address")
    ball_obj = None
    if kind == "address":
        bx, by = sh["ball"][0] * YD, sh["ball"][1] * YD
        gz = ground_z(bx, by)
        ball = Vector((bx, by, gz + 0.055))
        ax, ay = sh["aim"][0] * YD - bx, sh["aim"][1] * YD - by
        aim = Vector((ax, ay, 0)).normalized()
        back, up, ahead = (3.2, 1.4, 2.5) if sh.get("putting") else (4.5, 2.4, 1.5)
        loc = ball - aim * back * YD + Vector((0, 0, up * YD))
        look = ball + aim * ahead * YD
        fov = 60.0
    elif kind == "ortho":                      # plan view: centre (x yd, d yd), ortho_scale_m, looking straight down (course +D = image up)
        cxm, cym = sh["center"][0] * YD, sh["center"][1] * YD
        loc = Vector((cxm, cym, 900.0))
        look = Vector((cxm, cym, 0.0))
        fov = 60.0
        ball = None
    else:
        loc, look = world_to_blender(sh["pos"]), world_to_blender(sh["look"])
        fov = float(sh.get("fov", 60.0))
        ball = None
        if "ball" in sh:
            bx, by = sh["ball"][0] * YD, sh["ball"][1] * YD
            ball = Vector((bx, by, ground_z(bx, by) + 0.055))
    if ball is not None:
        me = bpy.data.meshes.new("PV_BALL")
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.055)
        bm.to_mesh(me)
        bm.free()
        ball_obj = bpy.data.objects.new("PV_BALL", me)
        bpy.context.scene.collection.objects.link(ball_obj)
        ball_obj.location = ball
        m = bpy.data.materials.new("PV_BALLMAT")
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1, 1, 1, 1)
        me.materials.append(m)
        for p in me.polygons:
            p.use_smooth = True
    cam = make_cam("PV_" + sh["name"], loc, look, fov)
    if kind == "ortho":
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = float(sh.get("ortho_scale_m", 900.0))
        cam.rotation_euler = (0.0, 0.0, 0.0)
    path = os.path.join(OUT, f"{PREFIX}{sh['name']}.png")
    render(cam, path)
    print(f"[render_views] {sh['name']} cam ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) m look ({look.x:.1f}, {look.y:.1f}, {look.z:.1f}) fov {fov} -> {path}", flush=True)
    if ball_obj is not None:
        bpy.data.objects.remove(ball_obj, do_unlink=True)
