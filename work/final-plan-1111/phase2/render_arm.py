"""render_arm.py (Blender, headless): the male hero's arm three ways, same camera and light: the base body, the 11-11 build,
and the muscle model (armfield.py). Bare and dressed (polo and shorts with the same field applied).
  Blender -b --factory-startup --python render_arm.py -- <out dir> [views] [variants]
"""
import bpy, bmesh, sys, os, math, importlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import armio, armfield as af, torsofield as tf, fit
importlib.reload(af); importlib.reload(tf); importlib.reload(fit)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.path.join(HERE, "renders"); os.makedirs(OUT, exist_ok=True)
VIEWS = argv[1].split(",") if len(argv) > 1 else ["front", "threeq", "side", "back", "armfront", "armback"]
VARIANTS = argv[2].split(",") if len(argv) > 2 else ["base", "build", "muscles"]
POSES = argv[3].split(",") if len(argv) > 3 else ["a"]      # "a" = the bind pose (arms out), "down" = arms hanging as in the target

SKIN = {n[:-5]: armio.read_skin(os.path.join(HERE, "export", "male_skin", n)) for n in sorted(os.listdir(os.path.join(HERE, "export", "male_skin"))) if n.endswith(".skin")}

def skins(tag):
    d = os.path.join(HERE, "export", tag)
    return {n[:-5]: armio.read_skin(os.path.join(d, n)) for n in sorted(os.listdir(d)) if n.endswith(".skin")} or SKIN

def arms_down(parts, B, deg=32.0, SKIN=SKIN):
    """The arms swung down about the shoulder joints with the game's own skin weights (armio.swing): the pose the tier 1 target
    stands in, so the shoulders and arms can be compared like for like."""
    out = {}
    for name, m in parts.items():
        p = armio.swing(m['pos'], SKIN[name], SKIN['Body'], B["LeftUpperArm"], "Left", deg)
        p = armio.swing(p, SKIN[name], SKIN['Body'], B["RightUpperArm"], "Right", -deg)
        out[name] = dict(m, pos=p)
    return out

def mirrored(mesh, B):
    m = dict(mesh); m['pos'] = mesh['pos'] * [-1, 1, 1]; w = mesh['w']; m['w'] = np.concatenate([w[:, 4:], w[:, :4]], 1)
    if 'armLeft' in mesh: m['armLeft'], m['armRight'] = mesh['armRight'], mesh['armLeft']
    Bm = {}
    for k, v in B.items():
        k2 = k.replace("Left", "#").replace("Right", "Left").replace("#", "Right")
        Bm[k2] = v * [-1, 1, 1]
    return m, Bm

def muscled(parts, B, P=None, chest=False):
    P = P or af.P
    body = dict(parts['Body'], armLeft=armio.membership(SKIN['Body'], SKIN['Body'], "Left"), armRight=armio.membership(SKIN['Body'], SKIN['Body'], "Right"))
    TL = af.field_tables(body, B, 'Left', P)
    bm_, Bm = mirrored(body, B); TR = af.field_tables(bm_, Bm, 'Left', P)
    TT = tf.tables(body) if chest else None
    out = {}
    for name, m in parts.items():
        p = af.apply(m['pos'], B, TL, 'Left', cloth=name != 'Body'); p = af.apply(p, B, TR, 'Right', cloth=name != 'Body')
        if chest: p = p + tf.apply(m['pos'], TT, cloth=name != 'Body', arms=(B, TL, TR)) - m['pos']
        out[name] = dict(m, pos=p)
    return out

def load(tag):
    d = os.path.join(HERE, "export", tag)
    parts = {n[:-4]: armio.read(os.path.join(d, n)) for n in sorted(os.listdir(d)) if n.endswith(".bin")}
    if os.path.exists(os.path.join(d, "BodyFull.tri")): parts['Body']['full'] = armio.full_tris(os.path.join(d, "BodyFull.tri"))
    return parts, armio.bones(os.path.join(d, "bones.json"))

def to_blender(p): return np.stack([p[:, 0], -p[:, 2], p[:, 1]], 1)     # Unity (x right, y up, z forward) -> Blender (z up, facing -y)

def material(name, colour, rough, sss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*colour, 1); b.inputs["Roughness"].default_value = rough
    if sss and "Subsurface Weight" in b.inputs: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (.012, .006, .004)
    return m

def add(name, mesh, mat, full=False):
    me = bpy.data.meshes.new(name)
    tri = mesh['full'] if full and 'full' in mesh else mesh['tri']
    me.from_pydata(to_blender(mesh['pos']).tolist(), [], tri[:, ::-1].tolist())
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-5); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.data.materials.append(mat)
    return ob

def scene_setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    engines = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else engines[0]
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = 760, 1000; sc.render.film_transparent = False
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (.55, .56, .58, 1); w.node_tree.nodes["Background"].inputs[1].default_value = .42
    def sun(name, rot, strength, colour=(1, 1, 1)):
        l = bpy.data.lights.new(name, "SUN"); l.energy = strength; l.color = colour; l.angle = math.radians(12)
        o = bpy.data.objects.new(name, l); o.rotation_euler = [math.radians(a) for a in rot]; sc.collection.objects.link(o)
    sun("key", (62, 0, -68), 4.2, (1, .96, .90))        # from the side and above: it rakes across the arm's forms (plan Phase 2 step 3)
    sun("fill", (70, 0, 60), .45, (.80, .88, 1))
    sun("rim", (60, 0, 165), 2.0)
    cam = bpy.data.cameras.new("cam"); co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
    return sc, co

VIEW = {  # azimuth deg (0 = front), look-at height, distance, lens, side offset x
    "front": (0, 1.12, 4.3, 70, 0), "threeq": (38, 1.12, 4.3, 70, 0), "side": (90, 1.12, 4.3, 70, 0), "back": (180, 1.12, 4.3, 70, 0),
    "armfront": (20, 1.17, 2.6, 85, -.33), "armback": (160, 1.17, 2.6, 85, -.33), "armside": (90, 1.17, 2.6, 85, -.33),
    "fullfront": (0, 0.88, 5.3, 70, 0), "full3q": (38, 0.88, 5.3, 70, 0), "fullside": (90, 0.88, 5.3, 70, 0), "fullback": (180, 0.88, 5.3, 70, 0),   # head to toe
    "shoesfront": (0, 0.06, 1.5, 70, 0, 0.16), "shoes3q": (40, 0.06, 1.5, 70, 0, 0.30), "shoestop": (0, 0.05, 1.6, 70, 0, 2.4),   # (6th value: how high the camera sits, as a share of its distance)
    "chestfront": (0, 1.22, 1.9, 70, 0), "chest3q": (40, 1.22, 1.9, 70, 0), "chestside": (90, 1.22, 1.9, 70, 0),
    "shfront": (28, 1.28, 1.55, 85, -.20), "shback": (152, 1.28, 1.55, 85, -.20), "upper": (0, 1.22, 2.5, 70, 0), "upperback": (180, 1.22, 2.5, 70, 0), "upperside": (90, 1.22, 2.5, 70, 0),
}
def aim(co, view):
    from mathutils import Vector
    az, h, dist, lens, ox = VIEW[view][:5]; a = math.radians(az); el = VIEW[view][5] if len(VIEW[view]) > 5 else 0.04
    # az 0: the camera in front of the hero (blender -y), swinging round toward the hero's left side (blender -x) as az grows
    target = Vector((ox, 0, h)); pos = target + dist * Vector((-math.sin(a), -math.cos(a), el))
    co.location = pos; co.data.lens = lens
    co.rotation_euler = (target - pos).to_track_quat('-Z', 'Y').to_euler()

base, B = load("male_build0"); build, _ = load("male_build1"); torso, _ = load("male_torso")
# "muscles" = the 11-11 build's chest, back and legs as installed, its arm term replaced by the muscle model
sets = {"base": lambda: base, "build": lambda: build, "muscles": lambda: muscled(torso, B), "v3": lambda: muscled(torso, B, af.V3), "chest": lambda: muscled(torso, B, chest=True), "whole": lambda: kit("tennis", False),
        "fit": lambda: fit.dress(torso, B, armio.membership(SKIN['Body'], SKIN['Body'], "Left"), armio.membership(SKIN['Body'], SKIN['Body'], "Right"))}   # arms + chest, tops refitted   # v3 = the first, lean version
# the same body in the other sports' kits: "<golf|bowl><loose|fit>" (loose = the garment as tailored, following the skin; fit = tops refitted)
KIT = {"golf": "male_golfkit_base", "bowl": "male_bowlingkit_base", "tennis": "male_build0",          # on the plain base body: the whole-body set (2026-11-12)
       "oldgolf": "male_golfkit", "oldbowl": "male_bowlingkit", "oldtennis": "male_torso",
       "hertennis": "female_tennis", "hergolf": "female_golfkit", "herbowl": "female_bowlingkit"}; SK = {}   # her: body untouched, tops refitted (her rest pose already has the arms down: pose "a")      # on the 11-11 build's torso, as first shown
def kit(sport, fitted):
    parts, Bk = load(KIT[sport]); SK[sport + ("fit" if fitted else "loose")] = skins(KIT[sport].replace("_base", "")) if "build0" not in KIT[sport] else SKIN
    if KIT[sport].startswith("female"):
        sk = SK[sport + ("fit" if fitted else "loose")]["Body"]
        return fit.dress(parts, Bk, armio.membership(sk, sk, "Left"), armio.membership(sk, sk, "Right"), fit=fitted, grow=False, under=("Kit_Bottom", "Kit_Belt"))
    return fit.dress(parts, B, armio.membership(SKIN['Body'], SKIN['Body'], "Left"), armio.membership(SKIN['Body'], SKIN['Body'], "Right"), fit=fitted, under=("Kit_Bottom", "Kit_Belt"))
for sport in KIT:
    sets[sport + "loose"] = (lambda s=sport: kit(s, False)); sets[sport + "fit"] = (lambda s=sport: kit(s, True))
ONLY = argv[4] if len(argv) > 4 else ""                     # "dressed" or "bare" to render just that
made = {}
for variant, pose in [(v, q) for v in VARIANTS for q in POSES]:
    for dressed in (False, True):
        if ONLY and ONLY != ('dressed' if dressed else 'bare'): continue
        sc, co = scene_setup()
        skin = material("skin", (.74, .47, .33), .42, .10); polo = material("polo", (.07, .22, .72), .78); white = material("white", (.86, .86, .85), .8); grey = material("grey", (.30, .31, .34), .8)
        if (variant, pose) not in made:
            q = sets[variant](); made[(variant, pose)] = q if pose == 'a' else arms_down(q, B, SKIN=SK.get(variant, SKIN))
        parts = made[(variant, pose)]
        add("Body", parts['Body'], skin, full=not dressed)
        if dressed:
            for n, m in parts.items():
                if n == "Body": continue
                add(n, m, polo if n == "Kit_Top" else grey if n == "Kit_Bottom" and not variant.startswith(("tennis", "fit", "chest", "muscles", "base", "build", "v3")) else white)
        for view in VIEWS:
            if dressed and view in ("armback", "armside", "shback"): continue
            aim(co, view)
            sc.render.filepath = os.path.join(OUT, f"{variant}{'' if pose == 'a' else '_' + pose}_{'dressed' if dressed else 'bare'}_{view}.png")
            bpy.ops.render.render(write_still=True)
print("RENDERS DONE", OUT)
