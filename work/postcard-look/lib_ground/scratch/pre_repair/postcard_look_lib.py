"""postcard_look_lib: the POSTCARD_LOOK ground / water / wall / path / lava pass on top of the verified flat build.

Owner: role A3 of the POSTCARD_LOOK job (brief ArtDir/environments/14_POSTCARD_LOOK.txt, interfaces
work/postcard-look/LOOK_CONTRACT.md, notes work/postcard-look/LIB_GROUND.md). postcard_lib.py stays the verified
geometry builder; everything here is a POST-PASS run after a hole's normal build (build_terrain, build_play_surfaces,
build_water ... are already done). It never moves a vertex of a TERRAIN / FAIRWAY / GREEN / TEE_BOX / BUNKER / CART_PATH
mesh: it only (a) swaps their materials to the LK_* names Unity's GolfLook knows, (b) writes their UV0, and (c) adds NEW
non-colliding meshes (ROCK_SKIN_*, WATER_SHELF, WATER_SURF_nn, a subdivided WATER_OCEAN / WATER_LAVA, DRESS_PATH_nn,
LAVA_LIGHT_nn empties). snapshot_ground / compare_ground measure that promise.

Copy-paste recipe for a hole build script (after the existing build, BEFORE render/save/export):

    import postcard_look_lib as L
    L.look_materials(D)                         # LK_* materials (early: props libs can then use L.look_material(name))
    snap = L.snapshot_ground(D)                 # optional: proof that the play surfaces do not move
    # ... the hole's own scenery (rocks, sea stacks, arch, plants) ...
    L.retarget_materials(D)                     # MAT_* -> LK_*, MAT_FOAM objects deleted, duplicate slots merged (idempotent:
                                                #   run it again after adding more MAT_* geometry)
    #   crater: L.retarget_materials(D, overrides=L.CRATER_OVERRIDES)     (cliff / dark rock -> LK_BASALT)
    #   Split : L.assign_region_material(D, L.spine_polygon(D.SCENERY["ridge"]["spine"], 33.0), "LK_SCRUB")
    L.build_cliff_skin(D, style="strata")       # Needle / Split: dark layered rock cladding every TERRAIN wall
    #   crater: rim = loops without the pin, pillar = the loop around the pin (see postcard_look_smoke.py):
    #           L.build_cliff_skin(D, "basalt", loops=rim); L.build_cliff_skin(D, "basalt", loops=pillar, follow_undercut=1.0, seed=1)
    L.build_sea(D)                              # ocean grid + WATER_SHELF + broken WATER_SURF_nn (deletes WATER_SHALLOW/FOAM)
    #   Needle (small pads): L.build_sea(D, shelf_m=(6.0, 14.0))
    #   crater: L.build_lava(D, lights=4)       # subdivided WATER_LAVA (LK_LAVA) + LAVA_LIGHT_nn empties; no ocean/shelf/surf
    #   Needle: L.build_path(D, [(-9, -6), (-8.5, 12), (-6, 28), (-3, 40)], width_m=2.6)   # course yards -> DRESS_PATH_nn
    #   waterfall foot: L.surf_patch(D, (x_m, y_m), radius_m=6.0)
    L.assign_uvs(D)                             # UV0 in tile units on every ground + water mesh (run LAST, after regions)
    ok, detail = L.compare_ground(D, snap)      # vertex positions of every ground mesh identical within 1e-5 m
    for name, ok, detail in L.audit_look(D): print(f"GATE: {name} {'PASS' if ok else 'FAIL'} - {detail}")
    ... P.render_overview(D); P.save(D)
    L.export_look_fbx(D)                        # = postcard_lib.export_fbx + path_mode STRIP, no embedded textures, NO texture
                                                #   references at all (see export_look_fbx), colours LINEAR (WATER_SURF A/R raw)
Gate a finished hole the same way the smoke test does: blender/scripts/postcard_look_smoke.py (+ postcard_verify.py; its
MATERIALS gate only knows the old MAT_* names and fails by design on an LK_* build).

API (all metres unless a name says _yd; D is postcard_lib's design handle)
    look_materials(D=None, rebuild=False) -> {name: Material}      every LK_* of LOOK_CONTRACT section 3
    look_material(name) -> Material                                get-or-create ONE LK_* material (props agents: use this, never
                                                                   bpy.data.materials.new, so names never become 'LK_ROCK.001')
    refresh_look_textures() -> [missing png names]                 re-link the PNGs once texture agent A1 has written them
    retarget_materials(D, overrides=None, delete_foam=True, purge=False) -> dict counters   (idempotent)
    assign_region_material(D, polygon, material='LK_SCRUB', units='yd', objects=None, top_only=True) -> faces switched
    spine_polygon(spine_yd, half_width_yd) -> polygon (course yards)   buffer of a polyline (for assign_region_material)
    assign_uvs(D, objects=None) -> {object: mode counts}           UV0 per LOOK_CONTRACT section 4 (see UV RULES)
    build_cliff_skin(D, style='strata'|'basalt', loops=None, seed=0, replace=False, **opts) -> [objects ROCK_SKIN_nn]
    build_sea(D, **opts) -> {name: obj}                            WATER_OCEAN grid, WATER_SHELF, WATER_SURF_nn
    surf_patch(D, center_m, radius_m=6.0, name=None, seed=0) -> obj   one extra whitewater patch (waterfall foot)
    build_lava(D, **opts) -> {name: obj}                           WATER_LAVA subdivided + LAVA_LIGHT_nn empties
    build_path(D, polyline, width_m=2.4, units='yd', **opts) -> [objects DRESS_PATH_nn]
    export_look_fbx(D, path=None) -> path                          use this, NOT postcard_lib.export_fbx (texture refs / colours)
    box_uv(ob, tile=None) -> ob                                    dominant-axis box UV, each face in its material's tile
    snapshot_ground(D) -> dict ; compare_ground(D, snap) -> (ok, detail) ; audit_look(D) -> [(name, ok, detail)]
    fbx_check(path, expect) -> [(name, ok, detail)]                re-import check (DESTROYS the open scene: run it last)
    terrain_top_loops(D) -> [(P (n,2), vertex indices)]            boundary loops of the TERRAIN top, land on the LEFT

MATERIALS. LOOK table below = LOOK_CONTRACT section 3 (texture stem, tile metres, URP smoothness S, fallback sRGB colour).
Principled BSDF: Image Texture (<stem>_C, sRGB) -> Base Color, (<stem>_N, Non-Color) -> Normal Map -> Normal, (<stem>_E, sRGB)
-> Emission Color; Roughness = 1 - S. When a PNG is missing the material gets the flat fallback colour of the right hue and the
name is listed in D.look_missing (lava / surf get a procedural stand-in so Blender previews still read). Every image reaches the
BSDF through an identity Gamma node, so the FBX carries the material NAMES (what Unity's GolfLook keys on) and NO texture
reference: the hole .meta files use materialName 0 (Unity 'By Base Texture Name'), which would otherwise rename an
imported LK_FAIRWAY to 'Fairway_C'. GolfLook loads the PNGs from Resources/Course/Look by material name.

UV RULES (UV0 only, tile units = metres / tile, LOOK_CONTRACT section 4; every object gets an integer shift so values stay
near 0 - textures repeat, so an integer shift changes nothing on screen):
    planar      LK_ROUGH / LK_SCRUB / LK_GREEN / LK_SAND / LK_PATH / water / lava faces: u = x / tile, v = y / tile (world);
                LK_ROUGH / LK_SCRUB / LK_LAVA get a smooth domain warp first (UV_WARP: |gradient| <= ~0.45, no seam) so the
                12 m / 24 m tile does not read as a grid from the overview
    centerline  LK_FAIRWAY faces: u = signed lateral offset from the design CENTERLINE (+ = right of play), v = arc length
                along it. The polyline is Chaikin-smoothed (5 rounds) and extended 120 m past both ends, sampled every
                0.25 m, so the projection is continuous across the kinks, the round tee end, the apron past the pin and the
                water-clipped pads: stripes follow the line of play, no seam inside a face.
    wall        TERRAIN faces that are not top faces: u = metres around the boundary loop (each wall column inherits the
                arc length of the top vertex it hangs from; per-face unwrap at the loop seam), v = z.
    box         LK_ROCK / LK_ROCK_WET / LK_MASONRY / LK_CLIFF* on non-TERRAIN meshes without their own UVs: per-face
                dominant-axis projection (props libs normally write their own UVs).
ROCK_SKIN builds its own UVs: u = arc / tile, v = (z - outward offset) / tile (ledges unroll instead of smearing).

DEPTH STACK (z above the sea / lava, all WATER_* inside z 0 .. 0.2 as postcard_verify's WATER_LEVEL gate wants):
    WATER_OCEAN / WATER_LAVA 0.00, WATER_SHELF 0.06, WATER_SURF_nn 0.12, DRESS_PATH 0.035 above the surface under it.
    Unity: 1 m = 1.0936 yd, near plane ~0.3 yd. With Metal's reversed-Z float depth the step at 300 yd is far below 1 mm;
    even a 24-bit fixed depth buffer gives z^2 / (near * 2^24) = 274^2 / (0.27 * 16.8e6) = 0.017 m at 300 yd, so 6 cm
    separations are >= 3 depth steps everywhere a player can see them (the old build used 4 / 8 / 9 cm and never fought).

WHY THE OCEAN IS A GRID. TennisWater computes linear fog PER VERTEX (ComputeFogFactor in vert, saturated there): a 4-vertex
4000 m plane has all four vertices past the fog end, so the whole sea comes out as flat fog colour. WATER_OCEAN stays ONE
object and ONE flat plane at z = 0 (world-space shader, no UV needed), but it is a graded grid: 16 m cells over the course
growing to 400 m at the 2 km rim, cells fully under the land (12 m inside the shore) dropped.
"""
import bpy
import bmesh
import math
import os
import sys
import time
import random

import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.getcwd()
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import postcard_lib as P  # noqa: E402

YD = P.YD
LOOK_DIR = os.path.join(P.COURSE_DIR, "Look")
GROUND_PREFIXES = P.GROUND_PREFIXES
SAFE_PREFIXES = ("ROCK_", "PLANT_", "DRESS_", "WATER_", "LAVA_")

Z_SHELF = 0.06
Z_SURF = 0.12
Z_PATH = 0.035

# name: (texture stem or None, maps, tile_m, smoothness, fallback sRGB, uv mode)
LOOK = {
    "LK_FAIRWAY": ("Fairway", "CN", 10.0, 0.10, (88, 172, 60), "centerline"),
    "LK_GREEN": ("Green", "CN", 6.0, 0.12, (124, 204, 74), "planar"),
    "LK_ROUGH": ("Rough", "CN", 12.0, 0.08, (66, 130, 46), "planar"),
    "LK_SCRUB": ("Scrub", "CN", 12.0, 0.08, (128, 124, 66), "planar"),
    "LK_SAND": ("Sand", "CN", 6.0, 0.12, (232, 212, 162), "planar"),
    "LK_CLIFF": ("Cliff", "CN", 12.0, 0.12, (82, 80, 76), "wall"),
    "LK_CLIFF_DARK": ("CliffDark", "CN", 12.0, 0.35, (52, 58, 54), "wall"),
    "LK_ROCK": ("Rock", "CN", 4.0, 0.12, (120, 114, 106), "box"),
    "LK_ROCK_WET": ("Rock", "CN", 4.0, 0.35, (86, 84, 80), "box"),
    "LK_PATH": ("Path", "CN", 5.0, 0.10, (206, 200, 184), "planar"),
    "LK_MASONRY": ("Masonry", "CN", 4.0, 0.10, (170, 162, 148), "box"),
    "LK_BASALT": ("Basalt", "CNE", 8.0, 0.15, (40, 38, 40), "wall"),
    "LK_LAVA": ("Lava", "CNE", 24.0, 0.30, (64, 28, 16), "planar"),
    "LK_PLANTS": ("Plants", "C", 0.0, 0.10, (98, 160, 72), None),
    "LK_WATER": (None, "", 8.0, 0.90, (22, 86, 172), "planar"),
    "LK_WATER_SHALLOW": (None, "", 8.0, 0.90, (40, 186, 196), "planar"),
    "LK_SURF": ("Surf", "C", 8.0, 0.0, (242, 250, 255), "planar"),
    "LK_FALL": ("Fall", "C", 0.0, 0.0, (222, 240, 250), None),
    "LK_SMOKE": ("Smoke", "C", 0.0, 0.0, (120, 110, 112), None),
}
ALPHA_MATS = ("LK_SURF", "LK_FALL", "LK_SMOKE")

RETARGET = {"MAT_ROUGH": "LK_ROUGH", "MAT_FAIRWAY": "LK_FAIRWAY", "MAT_FAIRWAY_STRIPE": "LK_FAIRWAY",
            "MAT_FIRSTCUT": "LK_FAIRWAY", "MAT_GREEN": "LK_GREEN", "MAT_BUNKER_LIP": "LK_GREEN", "MAT_SAND": "LK_SAND",
            "MAT_CLIFF": "LK_CLIFF", "MAT_CLIFF_DARK": "LK_CLIFF_DARK", "MAT_ROCK": "LK_ROCK", "MAT_ROCK_DARK": "LK_ROCK",
            "MAT_WATER": "LK_WATER", "MAT_WATER_SHALLOW": "LK_WATER_SHALLOW", "MAT_LAVA": "LK_LAVA"}
CRATER_OVERRIDES = {"MAT_CLIFF": "LK_BASALT", "MAT_CLIFF_DARK": "LK_BASALT", "MAT_ROCK_DARK": "LK_BASALT"}
KEEP_MATS = ("MAT_FLAG", "MAT_POLE", "MAT_CUP", "MAT_BALL")


def _log(msg):
    print(f"[postcard_look_lib] {msg}", flush=True)


def _track(D, ob):
    if D is not None:
        lst = D.__dict__.setdefault("look_objects", [])
        if ob.name not in lst:
            lst.append(ob.name)
    return ob


# ============================================================================= noise (deterministic numpy value noise)
def _hash(ix, iy, seed):
    x = (np.asarray(ix, np.int64) * 0x27D4EB2D) ^ (np.asarray(iy, np.int64) * 0x165667B1) ^ np.int64((seed * 0x9E3779B1) & 0xFFFFFFFF)
    x = x & 0xFFFFFFFF
    x = x ^ (x >> 15)
    x = (x * 0x2C1B3C6D) & 0xFFFFFFFF
    x = x ^ (x >> 12)
    x = (x * 0x297A2D39) & 0xFFFFFFFF
    x = x ^ (x >> 15)
    return (x & 0xFFFFFF).astype(np.float64) / 16777216.0


def vnoise(X, Y, scale, seed=0):
    """Smooth value noise in [0, 1) at world points (X, Y), feature size `scale` metres."""
    x = np.asarray(X, float) / scale
    y = np.asarray(Y, float) / scale
    ix, iy = np.floor(x), np.floor(y)
    fx, fy = x - ix, y - iy
    u, v = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    ix, iy = ix.astype(np.int64), iy.astype(np.int64)
    a, b = _hash(ix, iy, seed), _hash(ix + 1, iy, seed)
    c, d = _hash(ix, iy + 1, seed), _hash(ix + 1, iy + 1, seed)
    return (a + (b - a) * u) * (1 - v) + (c + (d - c) * u) * v


def fbm(X, Y, scale, seed=0, octaves=3, gain=0.5):
    tot, amp, norm = 0.0, 1.0, 0.0
    for k in range(octaves):
        tot = tot + amp * vnoise(X, Y, scale / (2 ** k), seed + 101 * k)
        norm += amp
        amp *= gain
    return tot / norm


def loop_noise(s, L, scale, seed=0, octaves=2):
    """Periodic 1-D noise along a closed loop of length L (s in metres): noise on a circle of circumference L."""
    R = L / (2 * math.pi)
    th = np.asarray(s, float) / max(R, 1e-6)
    return fbm(R * np.cos(th) + 1000.0, R * np.sin(th) - 700.0, scale, seed, octaves)


def _blocks(L, lo, hi, rnd):
    """Piecewise-constant random blocks along [0, L): (edges array, values array)."""
    edges, s = [0.0], 0.0
    while s < L:
        s += rnd.uniform(lo, hi)
        edges.append(min(s, L))
    edges = np.array(edges)
    return edges, np.array([rnd.random() for _ in range(len(edges) - 1)])


def _block_at(s, edges, vals):
    k = np.clip(np.searchsorted(edges, s, side="right") - 1, 0, len(vals) - 1)
    return vals[k]


def _smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ============================================================================= materials
def _png(stem, suffix):
    return os.path.join(LOOK_DIR, f"{stem}_{suffix}.png")


def _image(path, colorspace):
    name = os.path.basename(path)
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.load(path, check_existing=True)
        img.name = name
    else:
        img.filepath = path
        try:
            img.reload()
        except Exception:
            pass
    try:
        img.colorspace_settings.name = colorspace
    except Exception:
        pass
    if name.endswith("_C.png"):
        img.alpha_mode = 'STRAIGHT'
    return img


def _lin(c):
    return P.rgb(*c)


def _build_material(name, missing):
    stem, maps, tile, S, fallback, _mode = LOOK[name]
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    if mat.node_tree is None:
        mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (500, 0)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.name = "Principled BSDF"
    b.location = (150, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = _lin(fallback)
    b.inputs["Roughness"].default_value = max(0.05, 1.0 - S)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Specular IOR Level"].default_value = 0.35 if name.startswith("LK_WATER") else 0.2
    mat.diffuse_color = _lin(fallback)
    mat["lk_by"] = "postcard_look_lib"
    mat["lk_tile_m"] = float(tile)
    mat["lk_smoothness"] = float(S)
    y = 300
    have = {}
    for suf, cs in (("C", "sRGB"), ("N", "Non-Color"), ("E", "sRGB")):
        if stem is None or suf not in maps:
            continue
        path = _png(stem, suf)
        if not os.path.isfile(path):
            missing.append(os.path.basename(path))
            continue
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = _image(path, cs)
        node.extension = 'EXTEND' if name in ("LK_PLANTS", "LK_FALL", "LK_SMOKE") else 'REPEAT'
        node.interpolation = 'Linear'
        node.location = (-450, y)
        node.label = f"{stem}_{suf}"
        y -= 300
        have[suf] = node
    if "C" in have:
        nt.links.new(_passthru(nt, have["C"]), b.inputs["Base Color"])
    if "N" in have:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.location = (-150, -250)
        nm.inputs["Strength"].default_value = 1.0
        nt.links.new(_passthru(nt, have["N"]), nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if name in ("LK_BASALT", "LK_LAVA"):
        strength = 2.5 if name == "LK_LAVA" else 2.0
        if "E" in have:
            nt.links.new(_passthru(nt, have["E"]), b.inputs["Emission Color"])
            b.inputs["Emission Strength"].default_value = strength
        elif name == "LK_LAVA":
            _procedural_lava(nt, b)
        else:
            b.inputs["Emission Color"].default_value = (0, 0, 0, 1)
    if name.startswith("LK_WATER"):
        _procedural_ripple(nt, b)
    if name in ALPHA_MATS:
        _alpha_setup(mat, nt, b, have.get("C"), name)
    return mat


def _passthru(nt, img_node):
    """Image -> identity Gamma node -> socket. The FBX exporter only records a texture that is linked DIRECTLY to the
    Principled BSDF / Normal Map node, so the FBX carries no texture reference: the hole FBX .meta files use
    materialName 0 (Unity 'By Base Texture Name'), which would rename an imported LK_FAIRWAY to 'Fairway_C' and hide it
    from GolfLook. Blender previews still show the texture."""
    g = nt.nodes.new("ShaderNodeGamma")
    g.inputs["Gamma"].default_value = 1.0
    g.location = (img_node.location[0] + 220, img_node.location[1])
    nt.links.new(img_node.outputs["Color"], g.inputs["Color"])
    return g.outputs["Color"]


def _procedural_lava(nt, b):
    """Blender-preview stand-in while Lava_C/_E do not exist yet: dark crust plates, glowing fissures (Voronoi edges)."""
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = 'DISTANCE_TO_EDGE'
    vor.inputs["Scale"].default_value = 5.0
    vor.location = (-700, -400)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-450, -400)
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (1.0, 0.42, 0.05, 1)
    cr.elements[1].position = 0.06
    cr.elements[1].color = (0.03, 0.012, 0.008, 1)
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 3.0


def _procedural_ripple(nt, b):
    """Blender-preview only: a soft noise bump so a render does not show a dead flat plane (Unity uses TennisWater)."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-900, -500)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.location = (-650, -500)
    nz.inputs["Scale"].default_value = 0.35
    nz.inputs["Detail"].default_value = 6.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (-350, -500)
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.2
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])


def _alpha_setup(mat, nt, b, cnode, name):
    try:
        mat.surface_render_method = 'BLENDED'
    except Exception:
        pass
    try:
        mat.use_backface_culling = False
    except Exception:
        pass
    b.inputs["Roughness"].default_value = 0.6
    if cnode is not None:
        tex_alpha = cnode.outputs["Alpha"]
    else:                                         # stand-in: soft noise foam
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 6.0
        nz.inputs["Detail"].default_value = 8.0
        nz.location = (-700, 200)
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.location = (-450, 200)
        ramp.color_ramp.elements[0].position = 0.42
        ramp.color_ramp.elements[1].position = 0.62
        nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        tex_alpha = ramp.outputs["Color"]
    if name == "LK_SURF":
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        vc.location = (-450, -650)
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = 'MULTIPLY'
        mul.location = (-150, -500)
        nt.links.new(tex_alpha, mul.inputs[0])
        nt.links.new(vc.outputs["Alpha"], mul.inputs[1])
        boost = nt.nodes.new("ShaderNodeMath")                  # preview only: Surf_C alpha averages 0.35
        boost.operation = 'MULTIPLY'
        boost.use_clamp = True
        boost.inputs[1].default_value = 1.8
        boost.location = (0, -500)
        nt.links.new(mul.outputs["Value"], boost.inputs[0])
        nt.links.new(boost.outputs["Value"], b.inputs["Alpha"])
    else:
        nt.links.new(tex_alpha, b.inputs["Alpha"])


def look_material(name, D=None):
    """Get-or-create ONE LK_* material by its exact contract name (never makes 'LK_X.001')."""
    if name not in LOOK:
        raise KeyError(f"{name} is not a LOOK_CONTRACT material")
    mat = bpy.data.materials.get(name)
    if mat is None:
        missing = []
        mat = _build_material(name, missing)
        if D is not None:
            D.__dict__.setdefault("look_missing", [])
            D.look_missing.extend(m for m in missing if m not in D.look_missing)
    if D is not None:
        D.mats[name] = mat
    return mat


def look_materials(D=None, rebuild=False):
    """Create every LK_* material of LOOK_CONTRACT section 3 (see the module docstring). Existing ones made by somebody else
    (no 'lk_by' tag) are left alone unless rebuild=True. Missing PNGs -> flat fallback colour, listed in D.look_missing."""
    missing, out = [], {}
    for name in LOOK:
        mat = bpy.data.materials.get(name)
        if mat is None or rebuild or mat.get("lk_by") == "postcard_look_lib":
            mat = _build_material(name, missing)
        out[name] = mat
        if D is not None:
            D.mats[name] = mat
    missing = sorted(set(missing))
    if D is not None:
        D.look_missing = missing
    _log(f"look_materials: {len(out)} LK_* materials; textures {'ALL PRESENT' if not missing else 'MISSING ' + ', '.join(missing)}")
    return out


def refresh_look_textures():
    """Rebuild the node trees of the LK_* materials this lib made (picks up PNGs written since). Returns missing names."""
    missing = []
    for name in LOOK:
        mat = bpy.data.materials.get(name)
        if mat is not None and mat.get("lk_by") == "postcard_look_lib":
            _build_material(name, missing)
    return sorted(set(missing))


# ============================================================================= retarget
def _export_meshes(D):
    return [o for o in P._export_objects(D) if o.type == 'MESH']


def _dedupe_slots(me):
    mats = list(me.materials)
    uniq, remap = [], []
    for m_ in mats:
        if m_ in uniq:
            remap.append(uniq.index(m_))
        else:
            uniq.append(m_)
            remap.append(len(uniq) - 1)
    if len(uniq) == len(mats):
        return 0
    n = len(me.polygons)
    idx = np.zeros(n, np.int32)
    me.polygons.foreach_get("material_index", idx)
    idx = np.array(remap, np.int32)[np.clip(idx, 0, len(remap) - 1)]
    for k, m_ in enumerate(uniq):
        me.materials[k] = m_
    while len(me.materials) > len(uniq):
        me.materials.pop(index=len(me.materials) - 1)
    me.polygons.foreach_set("material_index", idx)
    me.update()
    return len(mats) - len(uniq)


def retarget_materials(D, overrides=None, delete_foam=True, purge=False):
    """MAT_* -> LK_* on every mesh datablock (instanced rocks included), per RETARGET (+ `overrides`, e.g.
    CRATER_OVERRIDES). Objects whose only material is MAT_FOAM (WATER_FOAM, WATER_FOAM_CREST) are deleted; MAT_FAIRWAY /
    MAT_FAIRWAY_STRIPE collapse into one LK_FAIRWAY slot (stripes live in the texture). Gameplay MAT_FLAG / POLE / CUP /
    BALL stay. Only material slots and material indices change; no vertex moves. Idempotent: run it again after adding
    geometry that still uses MAT_* names. The old MAT_* datablocks stay in D.mats with 0 users (not saved, not exported),
    so hole code that still reads D.mats['MAT_ROUGH'] keeps working; purge=True removes them. Returns counters."""
    if not any(n in bpy.data.materials for n in LOOK):
        look_materials(D)
    table = dict(RETARGET)
    table.update(overrides or {})
    cnt = dict(slots=0, merged=0, foam_objects=0, removed_mats=0)
    if delete_foam:
        for ob in list(bpy.data.objects):
            if ob.type == 'MESH' and len(ob.data.materials) and all(m_ is not None and m_.name.split(".")[0] == "MAT_FOAM"
                                                                   for m_ in ob.data.materials):
                D.objects.pop(ob.name, None)
                P.remove_object(ob.name)
                cnt["foam_objects"] += 1
    for me in bpy.data.meshes:
        changed = False
        for i, m_ in enumerate(list(me.materials)):
            if m_ is None:
                continue
            base = m_.name.split(".")[0]
            if base in table:
                me.materials[i] = look_material(table[base], D)
                cnt["slots"] += 1
                changed = True
        if changed:
            cnt["merged"] += _dedupe_slots(me)
    for ob in bpy.data.objects:                   # object-linked slots (rare)
        for sl in ob.material_slots:
            if sl.link == 'OBJECT' and sl.material is not None and sl.material.name.split(".")[0] in table:
                sl.material = look_material(table[sl.material.name.split(".")[0]], D)
                cnt["slots"] += 1
    for m_ in list(bpy.data.materials):
        if purge and m_.name.startswith("MAT_") and m_.users == 0 and m_.name.split(".")[0] not in KEEP_MATS:
            D.mats.pop(m_.name, None)
            bpy.data.materials.remove(m_)
            cnt["removed_mats"] += 1
    _log(f"retarget_materials: {cnt}")
    return cnt


# ============================================================================= mesh helpers
def _mesh_arrays(ob):
    me = ob.data
    nv, npoly, nl = len(me.vertices), len(me.polygons), len(me.loops)
    co = np.empty(nv * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mw = np.array(ob.matrix_world)
    W = co @ mw[:3, :3].T + mw[:3, 3]
    ls = np.empty(npoly, np.int64)
    lt = np.empty(npoly, np.int64)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    lv = np.empty(nl, np.int64)
    me.loops.foreach_get("vertex_index", lv)
    mi = np.empty(npoly, np.int64)
    me.polygons.foreach_get("material_index", mi)
    pn = np.empty(npoly * 3)
    me.polygons.foreach_get("normal", pn)
    pn = pn.reshape(-1, 3) @ np.linalg.inv(mw[:3, :3]) if npoly else pn.reshape(-1, 3)     # (M^-1)^T n as row vectors
    pn = pn / np.maximum(np.linalg.norm(pn, axis=1), 1e-12)[:, None] if npoly else pn
    return W, ls, lt, lv, mi, pn


def _poly_of_loop(ls, lt, nl):
    out = np.empty(nl, np.int64)
    for p, (a, n) in enumerate(zip(ls.tolist(), lt.tolist())):
        out[a:a + n] = p
    return out


def _top_mask(D, W, ls, lt, lv, pn):
    pz = D.play_z
    pol = _poly_of_loop(ls, lt, len(lv))
    off = np.abs(W[lv, 2] - pz) > 1e-3
    bad = np.zeros(len(ls), bool)
    np.logical_or.at(bad, pol, off)
    return (pn[:, 2] > 0.5) & ~bad


def _chain_loops(dir_edges, W):
    """Ordered boundary loops from directed boundary edges (a, b); pinch vertices resolved like postcard_lib."""
    out = {}
    for a, b in dir_edges:
        out.setdefault(a, []).append(b)
    used, loops = set(), []
    for a0, b0 in sorted(dir_edges):
        if (a0, b0) in used:
            continue
        loop, prev, cur = [a0], a0, b0
        used.add((a0, b0))
        guard = 0
        while cur != a0 and guard < len(dir_edges) + 5:
            loop.append(cur)
            cands = [c for c in out.get(cur, []) if (cur, c) not in used]
            if not cands:
                break
            if len(cands) > 1:
                back = W[prev, :2] - W[cur, :2]
                ba = math.atan2(back[1], back[0])
                best, bi = 1e9, 0
                for k, c in enumerate(cands):
                    o = W[c, :2] - W[cur, :2]
                    cw = (ba - math.atan2(o[1], o[0])) % (2 * math.pi)
                    if cw < best:
                        best, bi = cw, k
                nxt = cands[bi]
            else:
                nxt = cands[0]
            used.add((cur, nxt))
            prev, cur = cur, nxt
            guard += 1
        if cur == a0 and len(loop) >= 3:
            loops.append(loop)
    return loops


def terrain_top_loops(D, ob=None):
    """Boundary loops of the TERRAIN top faces traced from the MESH itself (works after hole 8's welds): list of
    (P (n,2) metres, vertex indices (n,)), land on the LEFT of the travel direction (outer loops CCW, holes CW)."""
    ob = ob or D.terrain or bpy.data.objects[D.terrain_name]
    W, ls, lt, lv, mi, pn = _mesh_arrays(ob)
    top = _top_mask(D, W, ls, lt, lv, pn)
    edges = set()
    for p in np.nonzero(top)[0].tolist():
        a, n = int(ls[p]), int(lt[p])
        vs = lv[a:a + n].tolist()
        for k in range(n):
            edges.add((vs[k], vs[(k + 1) % n]))
    bnd = [(a, b) for (a, b) in edges if (b, a) not in edges]
    loops = _chain_loops(bnd, W)
    return [(W[np.array(L_)][:, :2].copy(), np.array(L_)) for L_ in loops]


# ============================================================================= centerline parametrisation
class CenterlineParam:
    """Smooth (u, v) coordinates around the design CENTERLINE: u = signed lateral metres (+ right of play), v = arc metres.
    Chaikin-smoothed (5 rounds), extended `ext_m` past both ends, sampled every `step` metres."""

    def __init__(self, D, ext_m=120.0, step=0.25, rounds=5):
        pts = [Vector(P.m(x, d)) for x, d in D.hole.center]
        sm = P.chaikin([(p.x, p.y) for p in pts], iterations=rounds, closed=False) if len(pts) > 2 else pts
        sm = [Vector((p[0], p[1])) for p in sm]
        d0 = (sm[1] - sm[0]).normalized()
        d1 = (sm[-1] - sm[-2]).normalized()
        sm = [sm[0] - d0 * ext_m] + sm + [sm[-1] + d1 * ext_m]
        dense = P.resample([(p.x, p.y) for p in sm], step, closed=False)
        S = np.array([(p.x, p.y) for p in dense])
        seg = np.diff(S, axis=0)
        L = np.hypot(seg[:, 0], seg[:, 1])
        A = np.concatenate([[0.0], np.cumsum(L)])
        tee = np.array(P.m(*D.hole.center[0]))
        k0 = int(np.argmin(np.hypot(S[:, 0] - tee[0], S[:, 1] - tee[1])))
        self.S, self.A = S, A - A[k0]               # v = 0 at the tee station
        self.T = np.vstack([seg / np.maximum(L, 1e-9)[:, None], (seg[-1] / max(L[-1], 1e-9))[None]])
        self.kd = KDTree(len(S))
        for i, (x, y) in enumerate(S.tolist()):
            self.kd.insert((x, y, 0.0), i)
        self.kd.balance()

    def uv(self, X, Y):
        X = np.asarray(X, float).ravel()
        Y = np.asarray(Y, float).ravel()
        idx = np.fromiter((self.kd.find((x, y, 0.0))[1] for x, y in zip(X.tolist(), Y.tolist())), np.int64, len(X))
        n = len(self.S)
        best_d = np.full(len(X), np.inf)
        u = np.zeros(len(X))
        v = np.zeros(len(X))
        for a_off in (-1, 0):
            a = np.clip(idx + a_off, 0, n - 2)
            Pa, Pb = self.S[a], self.S[a + 1]
            ab = Pb - Pa
            l2 = np.maximum((ab ** 2).sum(1), 1e-12)
            t = np.clip(((X - Pa[:, 0]) * ab[:, 0] + (Y - Pa[:, 1]) * ab[:, 1]) / l2, 0.0, 1.0)
            qx, qy = Pa[:, 0] + ab[:, 0] * t, Pa[:, 1] + ab[:, 1] * t
            d = np.hypot(X - qx, Y - qy)
            tx, ty = ab[:, 0] / np.sqrt(l2), ab[:, 1] / np.sqrt(l2)
            lat = (X - qx) * ty - (Y - qy) * tx          # right of travel (ty, -tx) is positive
            arc = self.A[a] + t * np.sqrt(l2)
            better = d < best_d
            best_d = np.where(better, d, best_d)
            u = np.where(better, lat, u)
            v = np.where(better, arc, v)
        return u, v


# ============================================================================= UVs
def _mat_name(m_):
    return m_.name.split(".")[0] if m_ is not None else ""


def _uv_layer(me):
    while len(me.uv_layers) > 1:
        me.uv_layers.remove(me.uv_layers[-1])
    if len(me.uv_layers) == 0:
        me.uv_layers.new(name="UVMap")
    lay = me.uv_layers[0]
    lay.name = "UVMap"
    me.uv_layers.active = lay
    return lay


def _wall_arc(D, ob, W, ls, lt, lv, pn, top):
    """Per-vertex (arc metres along its boundary loop, loop length) for TERRAIN wall vertices: each wall column inherits
    the arc of the top boundary vertex it hangs from (via its vertical edges)."""
    me = ob.data
    nv = len(W)
    s_of = np.full(nv, np.nan)
    L_of = np.full(nv, np.nan)
    for Pl, vidx in terrain_top_loops(D, ob):
        seg = np.roll(Pl, -1, axis=0) - Pl
        Ls = np.hypot(seg[:, 0], seg[:, 1])
        s = np.concatenate([[0.0], np.cumsum(Ls)[:-1]])
        s_of[vidx] = s
        L_of[vidx] = Ls.sum()
    ev = np.empty(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", ev)
    ev = ev.reshape(-1, 2)
    za, zb = W[ev[:, 0], 2], W[ev[:, 1], 2]
    vert = np.abs(za - zb) > 1e-3
    up = np.where(za > zb, ev[:, 0], ev[:, 1])[vert]
    lo = np.where(za > zb, ev[:, 1], ev[:, 0])[vert]
    dxy = np.hypot(*(W[up, :2] - W[lo, :2]).T)
    order = np.lexsort((dxy, lo))
    parent = np.full(nv, -1, np.int64)
    lo_s, up_s = lo[order], up[order]
    first = np.ones(len(lo_s), bool)
    first[1:] = lo_s[1:] != lo_s[:-1]
    parent[lo_s[first]] = up_s[first]
    for v in np.argsort(-W[:, 2]).tolist():
        if np.isnan(s_of[v]) and parent[v] >= 0 and not np.isnan(s_of[parent[v]]):
            s_of[v] = s_of[parent[v]]
            L_of[v] = L_of[parent[v]]
    miss = np.isnan(s_of)
    if miss.any():                                  # fallback: nearest arc-known vertex in plan
        known = np.nonzero(~miss)[0]
        kd = KDTree(len(known))
        for i, k in enumerate(known.tolist()):
            kd.insert((W[k, 0], W[k, 1], 0.0), i)
        kd.balance()
        for v in np.nonzero(miss)[0].tolist():
            k = known[kd.find((W[v, 0], W[v, 1], 0.0))[1]]
            s_of[v], L_of[v] = s_of[k], L_of[k]
    return s_of, L_of


# planar materials whose UVs get a smooth domain warp (amp1 m, wavelength1 m, amp2 m, wavelength2 m): a 12 m / 24 m tile
# repeated over 700 m reads as a grid from the overview; a warp with |gradient| <= ~0.45 hides it with no seam
UV_WARP = {"LK_LAVA": (5.0, 110.0, 2.5, 70.0), "LK_ROUGH": (2.2, 53.0, 0.8, 29.0), "LK_SCRUB": (2.2, 53.0, 0.8, 29.0)}


def _warp(X, Y, a1, l1, a2, l2):
    t = 2 * math.pi
    xw = X + a1 * np.sin(t * Y / l1 + 1.3) + a2 * np.sin(t * (X + Y) / (l2 * 1.41) + 0.2)
    yw = Y + a1 * np.sin(t * X / (l1 * 0.91) + 0.4) + a2 * np.sin(t * (X - Y) / (l2 * 1.29) + 2.1)
    return xw, yw


def assign_uvs(D, objects=None, fill_missing=True):
    """UV0 (one layer 'UVMap') in tile units on every ground-prefix and WATER_* mesh (or `objects`, names or objects), per
    the face material (UV RULES in the module docstring). Vertex positions are never touched. fill_missing: every other
    exported mesh that carries an LK_* material but NO UV layer at all (library rocks, a hole's own sea-stack columns) gets
    an object-space box UV in its material's tile units (shared mesh data: all instances share it); meshes that already
    have UVs (props libs) are left alone. Returns {name: modes}."""
    cl = CenterlineParam(D)
    if objects is None:
        obs = [o for o in _export_meshes(D) if o.name.startswith(GROUND_PREFIXES) or
               (o.name.startswith("WATER_") and not o.name.startswith(("WATER_SURF", "WATER_FALL")))]
    else:
        obs = [bpy.data.objects[o] if isinstance(o, str) else o for o in objects]
    report = {}
    for ob in obs:
        me = ob.data
        if len(me.polygons) == 0:
            continue
        W, ls, lt, lv, mi, pn = _mesh_arrays(ob)
        pol = _poly_of_loop(ls, lt, len(lv))
        mats = [_mat_name(m_) for m_ in me.materials] or [""]
        fmode = []
        ftile = []
        is_terrain = ob.name.startswith("TERRAIN")
        top = _top_mask(D, W, ls, lt, lv, pn) if is_terrain else None
        for p in range(len(ls)):
            name = mats[min(int(mi[p]), len(mats) - 1)]
            spec = LOOK.get(name)
            tile = spec[2] if spec and spec[2] > 0 else 8.0
            mode = spec[5] if spec and spec[5] else "planar"
            if is_terrain:
                mode = "planar" if top[p] else "wall"
            elif mode == "wall":
                mode = "box"
            elif mode == "box" and pn[p, 2] > 0.9:
                mode = "planar"
            fmode.append(mode)
            ftile.append(tile)
        fmode = np.array(fmode)
        ftile = np.array(ftile)
        fname = np.array([mats[min(int(mi[p]), len(mats) - 1)] for p in range(len(ls))])
        lmode, ltile, lname = fmode[pol], ftile[pol], fname[pol]
        X, Y, Z = W[lv, 0], W[lv, 1], W[lv, 2]
        U = np.zeros(len(lv))
        V = np.zeros(len(lv))
        m = lmode == "planar"
        U[m], V[m] = X[m] / ltile[m], Y[m] / ltile[m]
        for p_mat, wp in UV_WARP.items():                 # smooth domain warp: breaks the visible tile grid, no seams
            mm = m & (lname == p_mat)
            if mm.any():
                xw, yw = _warp(X[mm], Y[mm], *wp)
                U[mm], V[mm] = xw / ltile[mm], yw / ltile[mm]
        m = lmode == "centerline"
        if m.any():
            uu, vv = cl.uv(X[m], Y[m])
            U[m], V[m] = uu / ltile[m], vv / ltile[m]
        m = lmode == "wall"
        if m.any():
            s_of, L_of = _wall_arc(D, ob, W, ls, lt, lv, pn, top)
            s = s_of[lv]
            Lp = L_of[lv]
            for p in np.unique(pol[m]).tolist():          # unwrap each face at its loop seam
                a, n = int(ls[p]), int(lt[p])
                ss = s[a:a + n]
                half = 0.5 * np.nanmax(Lp[a:a + n])
                ss = np.where(ss - ss[0] > half, ss - 2 * half, np.where(ss - ss[0] < -half, ss + 2 * half, ss))
                s[a:a + n] = ss
            U[m], V[m] = s[m] / ltile[m], Z[m] / ltile[m]
        m = lmode == "box"
        if m.any():
            n_ = pn[pol]
            ax = np.argmax(np.abs(n_), axis=1)
            bx = m & (ax == 0)
            by = m & (ax == 1)
            bz = m & (ax == 2)
            U[bx], V[bx] = Y[bx] / ltile[bx], Z[bx] / ltile[bx]
            U[by], V[by] = X[by] / ltile[by], Z[by] / ltile[by]
            U[bz], V[bz] = X[bz] / ltile[bz], Y[bz] / ltile[bz]
        for mode in ("planar", "centerline", "wall", "box"):          # integer shift per mode: values near 0
            m = lmode == mode
            if m.any():
                if mode != "centerline":
                    U[m] -= np.round(np.mean(U[m]))
                V[m] -= np.round(np.mean(V[m]))
        lay = _uv_layer(me)
        lay.data.foreach_set("uv", np.stack([U, V], 1).ravel())
        me.update()
        report[ob.name] = {k: int((fmode == k).sum()) for k in ("planar", "centerline", "wall", "box") if (fmode == k).any()}
    if fill_missing and objects is None:
        done = set()
        for ob in _export_meshes(D):
            me = ob.data
            if ob in obs or me.name in done or len(me.uv_layers) or not len(me.polygons):
                continue
            lk = [_mat_name(m_) for m_ in me.materials if m_ is not None and _mat_name(m_) in LOOK]
            if not lk:
                continue
            box_uv(ob, tile=None, object_space=True)
            done.add(me.name)
        if done:
            report["(box fill)"] = len(done)
    _log("assign_uvs: " + ", ".join(f"{k} {v}" for k, v in report.items()))
    return report


def box_uv(ob, tile=None, object_space=True):
    """Per-face dominant-axis box projection in tile units for a prop mesh (object space by default, so instances share
    it). tile None = each face uses the contract tile of its own LK_* material (4 m when it has none); a number forces one."""
    me = ob.data
    co = np.array([v.co[:] for v in me.vertices])
    if not object_space:
        mw = np.array(ob.matrix_world)
        co = co @ mw[:3, :3].T + mw[:3, 3]
    mats = [_mat_name(m_) for m_ in me.materials] or [""]
    lay = _uv_layer(me)
    uv = np.zeros((len(me.loops), 2))
    for p in me.polygons:
        t = tile if tile else (LOOK[mats[min(p.material_index, len(mats) - 1)]][2]
                               if mats[min(p.material_index, len(mats) - 1)] in LOOK else 0.0) or 4.0
        ax = int(np.argmax(np.abs(p.normal[:])))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for li in p.loop_indices:
            c = co[me.loops[li].vertex_index]
            uv[li] = (c[a] / t, c[b] / t)
    lay.data.foreach_set("uv", uv.ravel())
    return ob


# ============================================================================= region material
def spine_polygon(spine_yd, half_width_yd):
    """Polygon (course yards) = the polyline `spine_yd` buffered by half_width_yd (flat ends). For assign_region_material."""
    S = np.array(spine_yd, float)
    tg = np.gradient(S, axis=0)
    tg /= np.maximum(np.hypot(tg[:, 0], tg[:, 1]), 1e-9)[:, None]
    nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)
    left = S + nrm * half_width_yd
    right = S - nrm * half_width_yd
    return [tuple(p) for p in np.vstack([right, left[::-1]])]


def assign_region_material(D, polygon, material="LK_SCRUB", units="yd", objects=None, top_only=True):
    """Give every (top) face of `objects` (default: the TERRAIN) whose centroid lies inside `polygon` the material
    `material` (added as a slot when missing). polygon in course yards (units='yd') or metres ('m'). Geometry untouched; the
    boundary follows the existing triangles (about 6.5 m on the terrain top). Run assign_uvs afterwards. Returns count."""
    poly = np.array(polygon, float) * (YD if units == "yd" else 1.0)
    obs = objects or [D.terrain or bpy.data.objects[D.terrain_name]]
    mat = look_material(material, D) if material in LOOK else bpy.data.materials[material]
    n = 0
    for ob in obs:
        ob = bpy.data.objects[ob] if isinstance(ob, str) else ob
        me = ob.data
        W, ls, lt, lv, mi, pn = _mesh_arrays(ob)
        pol = _poly_of_loop(ls, lt, len(lv))
        cen = np.zeros((len(ls), 2))
        np.add.at(cen, pol, W[lv, :2])
        cen /= lt[:, None]
        sel = P._inside_np([tuple(p) for p in poly], cen[:, 0], cen[:, 1])
        if top_only:
            sel &= (pn[:, 2] > 0.5) & (_top_mask(D, W, ls, lt, lv, pn) if ob.name.startswith("TERRAIN") else True)
        if not sel.any():
            continue
        if mat.name not in [m_.name for m_ in me.materials if m_]:
            me.materials.append(mat)
        k = [m_.name if m_ else "" for m_ in me.materials].index(mat.name)
        mi[sel] = k
        me.polygons.foreach_set("material_index", mi.astype(np.int32))
        me.update()
        n += int(sel.sum())
    _log(f"assign_region_material: {n} faces -> {material}")
    return n


# ============================================================================= cliff skin
def _terrain_bvh(D):
    ob = D.terrain or bpy.data.objects[D.terrain_name]
    W, ls, lt, lv, mi, pn = _mesh_arrays(ob)
    polys = [lv[a:a + n].tolist() for a, n in zip(ls.tolist(), lt.tolist())]
    return BVHTree.FromPolygons([tuple(p) for p in W.tolist()], polys)


def _loop_columns(Pl, step):
    """Columns along a closed loop: every loop vertex plus evenly spaced points on each edge (spacing <= step).
    Returns positions (m,2), arc s (m,), loop length, outward unit normals (m,2) (right of travel), is_vertex (m,)."""
    n = len(Pl)
    pos, s_arr, isv, nrm = [], [], [], []
    seg = np.roll(Pl, -1, axis=0) - Pl
    Ls = np.hypot(seg[:, 0], seg[:, 1])
    tg = seg / np.maximum(Ls, 1e-9)[:, None]
    en = np.stack([tg[:, 1], -tg[:, 0]], 1)                      # outward = right of travel (land is on the left)
    acc = 0.0
    for i in range(n):
        k = max(1, int(math.ceil(Ls[i] / step)))
        for j in range(k):
            t = j / k
            pos.append(Pl[i] + seg[i] * t)
            s_arr.append(acc + Ls[i] * t)
            isv.append(j == 0)
            if j == 0:
                b = en[i - 1] + en[i]
                bl = math.hypot(*b)
                nrm.append(b / bl if bl > 0.3 else en[i])
            else:
                nrm.append(en[i])
        acc += Ls[i]
    N = np.array(nrm)
    for _ in range(2):                                           # light smoothing of the normals
        N = 0.5 * N + 0.25 * (np.roll(N, 1, axis=0) + np.roll(N, -1, axis=0))
        N /= np.maximum(np.hypot(N[:, 0], N[:, 1]), 1e-9)[:, None]
    return np.array(pos), np.array(s_arr), acc, N, np.array(isv)


def _wall_inset(bvh, T, N, Z, start=5.0, reach=16.0):
    """Distance (>= 0) from the top-edge point T along -N to the TERRAIN wall at height Z (per column x row)."""
    out = np.zeros(Z.shape)
    for i in range(Z.shape[0]):
        for r in range(Z.shape[1]):
            o = Vector((T[i, 0] + N[i, 0] * start, T[i, 1] + N[i, 1] * start, Z[i, r]))
            hit = bvh.ray_cast(o, Vector((-N[i, 0], -N[i, 1], 0.0)), reach + start)
            if hit[0] is not None:
                out[i, r] = max(0.0, hit[3] - start)
    return out


def _unfold_rows(Pc, N, R, tg):
    """Reduce offsets R (cols x rows) where the offset curve P + N r folds back (concave corners / deep insets)."""
    for _ in range(25):
        Q = Pc[:, None, :] + N[:, None, :] * R[:, :, None]
        dq = np.roll(Q, -1, axis=0) - Q
        ok = (dq * tg[:, None, :]).sum(2) > 0.05
        if ok.all():
            break
        bad = ~ok | np.roll(~ok, 1, axis=0)
        avg = 0.25 * (np.roll(R, 1, axis=0) + 2 * R + np.roll(R, -1, axis=0))
        R = np.where(bad, 0.4 * R + 0.6 * np.minimum(avg, R), R)
    return R


def _finish_mesh(ob, sharp_deg=38.0):
    me = ob.data
    me.validate()
    me.update()
    try:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(sharp_deg))
    except Exception:
        me.polygons.foreach_set("use_smooth", [False] * len(me.polygons))
    me.update()


def _new_piece(D, name, verts, faces, uvs, mats_idx, mats, col="ENVIRONMENT", sharp_deg=38.0):
    ob = P.new_mesh_object(name, col)
    P.build_mesh(ob, verts, faces, smooth=True, material_index=mats_idx, materials=mats)
    me = ob.data
    if len(me.polygons) != len(faces):
        raise RuntimeError(f"{name}: mesh validate dropped faces ({len(faces)} -> {len(me.polygons)}), UVs would misalign")
    lay = _uv_layer(me)
    fl = []
    for f, fu in zip(faces, uvs):
        fl.extend(fu)
    lay.data.foreach_set("uv", np.array(fl, float).ravel())
    _finish_mesh(ob, sharp_deg)
    D.objects[name] = ob
    return _track(D, ob)


def _next_name(D, prefix):
    k = D.__dict__.setdefault("look_counters", {}).get(prefix, 0) + 1
    while bpy.data.objects.get(f"{prefix}_{k:02d}") is not None:
        k += 1
    D.look_counters[prefix] = k
    return f"{prefix}_{k:02d}"


def build_cliff_skin(D, style="strata", loops=None, seed=0, step_m=None, lip_m=None, bottom_z=-1.6, disp_m=(0.2, 1.2),
                     follow_undercut=None, bands=4, wet_z=1.0, piece_m=140.0, material=None, material_low=None,
                     basalt_width_m=(1.0, 2.0), basalt_rows=2, name="ROCK_SKIN", replace=False):
    """Visual rock cladding ROCK_SKIN_nn over the TERRAIN walls (colliders untouched, ROCK_ prefix, no collider).

    style 'strata' (Needle / Split): a continuous jagged skin following every boundary loop: `bands` horizontal strata
        between the grass lip and bottom_z (below the waterline), each band a block-jointed face pushed out 0.2-1.2 m
        (disp_m) from the wall with its own overhang/undercut, crisp ledges between bands, chips; a capping ledge tucks
        back into the wall just below the grass lip (lip_m below PLAY_Z, default 0.15-0.45 m, so the TERRAIN grass lip
        band shows as a fringe). Faces whose centre is below wet_z get material_low (LK_CLIFF_DARK, wet), the rest
        material (LK_CLIFF). follow_undercut (default 0.5): 0 = plumb from the grass edge, 1 = hug the undercut wall.
    style 'basalt' (Crater): rows of hexagonal columns (basalt_width_m across) standing from bottom_z (in the lava) up to
        stepped tops 0.2-1.4 m below PLAY_Z, 1-3 fractured segments each, the outer row 0.2-1.2 m proud of the edge, an
        inner row behind it for stepped tops; LK_BASALT. follow_undercut (default 0) leans the columns inward with the
        undercut wall (1.0 = a tapered bowl like crater.jpg's pillar).
    loops: None = every TERRAIN top boundary loop, or a list of loop indices (terrain_top_loops order). Nothing is ever
    above PLAY_Z - 0.1. Pieces of <= piece_m metres of shore each (frustum culling). replace=True first deletes every
    existing `name`_nn object (re-running a build); leave it False when you call it once per loop group (crater rim +
    pillar). Seeded by the hole number + `seed`: rebuilding gives identical rock. Returns the objects."""
    t0 = time.time()
    if replace:
        for o in [o for o in bpy.data.objects if o.name.startswith(name + "_")]:
            D.objects.pop(o.name, None)
            P.remove_object(o.name)
        D.__dict__.setdefault("look_counters", {})[name] = 0
    rnd = random.Random(D.number * 1009 + seed)
    pz = D.play_z
    mat_hi = look_material(material or ("LK_BASALT" if style == "basalt" else "LK_CLIFF"), D)
    mat_lo = look_material(material_low or ("LK_BASALT" if style == "basalt" else "LK_CLIFF_DARK"), D)
    tile = LOOK[mat_hi.name][2]
    bvh = _terrain_bvh(D)
    all_loops = terrain_top_loops(D)
    sel = range(len(all_loops)) if loops is None else loops
    objs = []
    for li in sel:
        Pl = all_loops[li][0]
        if style == "basalt":
            objs += _basalt_loop(D, Pl, li, bvh, rnd, bottom_z, disp_m, follow_undercut or 0.0, lip_m or (0.2, 1.4),
                                 basalt_width_m, basalt_rows, mat_hi, tile, piece_m, name)
        else:
            objs += _strata_loop(D, Pl, li, bvh, rnd, step_m or 1.5, lip_m or (0.15, 0.45), bottom_z, disp_m,
                                 0.5 if follow_undercut is None else follow_undercut, bands, wet_z, mat_hi, mat_lo, tile,
                                 piece_m, name, seed)
    tris = sum(len(o.data.polygons) for o in objs) * 2
    _log(f"build_cliff_skin({style}): {len(objs)} pieces on {len(list(sel))} loops, ~{tris} tris, {time.time() - t0:.1f}s")
    return objs


def _columns_at(Pl, step, extra_s):
    """Regular loop columns (_loop_columns) plus extra columns at arc positions extra_s (fissure edges): positions on the
    polyline, normals interpolated from the regular columns. Returns Pc, s, L, N sorted by s (duplicates < 2 cm dropped)."""
    Pc, s, L, N, _ = _loop_columns(Pl, step)
    ex = np.asarray(extra_s, float) % L if len(extra_s) else np.zeros(0)
    if len(ex):
        seg = np.roll(Pl, -1, axis=0) - Pl
        Ls = np.hypot(seg[:, 0], seg[:, 1])
        Sv = np.concatenate([[0.0], np.cumsum(Ls)])
        k = np.clip(np.searchsorted(Sv, ex, side="right") - 1, 0, len(Pl) - 1)
        t = (ex - Sv[k]) / np.maximum(Ls[k], 1e-9)
        Pe = Pl[k] + seg[k] * t[:, None]
        sx = np.concatenate([s - L, s, s + L])
        Nx = np.concatenate([N, N, N])
        Ne = np.stack([np.interp(ex, sx, Nx[:, 0]), np.interp(ex, sx, Nx[:, 1])], 1)
        Ne /= np.maximum(np.hypot(Ne[:, 0], Ne[:, 1]), 1e-9)[:, None]
        Pc, s, N = np.vstack([Pc, Pe]), np.concatenate([s, ex]), np.vstack([N, Ne])
        o = np.argsort(s, kind="stable")
        Pc, s, N = Pc[o], s[o], N[o]
        keep = np.ones(len(s), bool)
        keep[1:] = np.diff(s) > 0.02
        Pc, s, N = Pc[keep], s[keep], N[keep]
    return Pc, s, L, N


def _strata_loop(D, Pl, li, bvh, rnd, step, lip_m, bottom_z, disp_m, follow, nb, wet_z, mat_hi, mat_lo, tile, piece_m,
                 name, seed):
    """Strata cladding of one loop. The shore is cut into FISSURE BLOCKS (3-9 m along the loop, a crisp vertical joint
    between two doubled columns 0.18 m apart); every block x band cell has its own outward offset (inside disp_m), its own
    ledge height step and its own overhang, all bands of a block share a 'push' (so joints run through the whole height),
    and a 22 m buttress noise swells whole stretches. Rows per band: top / mid / bottom, ledges 0.14 m tall between bands."""
    pz = D.play_z
    sd_seed = D.number * 31 + li * 7 + seed * 13
    seg = np.roll(Pl, -1, axis=0) - Pl
    L0 = float(np.hypot(seg[:, 0], seg[:, 1]).sum())
    fe, fv = _blocks(L0, 3.0, 9.0, rnd)                          # fissure blocks shared by every band
    nblk = len(fv)
    extra = np.concatenate([fe[1:-1] - 0.09, fe[1:-1] + 0.09]) if nblk > 1 else np.zeros(0)
    Pc, s, L, N = _columns_at(Pl, step, extra)
    m = len(Pc)
    tg = np.stack([-N[:, 1], N[:, 0]], 1)                         # travel direction (land on the left)
    kb = np.clip(np.searchsorted(fe, s, side="right") - 1, 0, nblk - 1)   # block of each column
    cell = rnd.random                                             # per (block, band) random values
    B = np.array([[cell() for _ in range(nb)] for _ in range(nblk)])
    STEP = np.array([[cell() for _ in range(nb + 1)] for _ in range(nblk)])
    OVER = np.array([[cell() for _ in range(nb)] for _ in range(nblk)])
    for k in range(nblk):                                         # ~35 % of the ledges vanish: two bands make one taller face
        for j in range(1, nb):
            if cell() < 0.35:
                B[k, j] = B[k, j - 1]
                OVER[k, j] = 0.0
    LIPB = np.array([cell() for _ in range(nblk)])
    lip = lip_m[0] + (lip_m[1] - lip_m[0]) * (0.55 * loop_noise(s, L, 9.0, sd_seed + 1) + 0.45 * LIPB[kb])
    z_top = pz - lip
    z_hi, z_lo = pz - float(np.mean(lip_m)), 0.45
    bh = (z_hi - z_lo) / max(nb - 1, 1)
    bnd = [z_top]
    for j in range(1, nb):
        nominal = z_hi - bh * j
        bnd.append(nominal + 0.42 * bh * (STEP[kb, j] - 0.5) * 2 + 0.08 * bh * (loop_noise(s, L, 7.0, sd_seed + 10 + j) - 0.5) * 2)
    bnd.append(np.full(m, bottom_z))
    for j in range(1, nb + 1):                                    # keep every band >= 0.45 m thick
        bnd[j] = np.minimum(bnd[j], bnd[j - 1] - 0.45)
    lo, hi = disp_m
    span = hi - lo
    push = fv[kb]                                                 # shared by all bands of a block
    buttress = loop_noise(s, L, 22.0, sd_seed + 5)
    rows_z, rows_d = [], []
    for j in range(nb):
        u = (0.16 + 0.34 * j / max(nb - 1, 1) + 0.40 * (push - 0.5) + 0.34 * (B[kb, j] - 0.5) + 0.30 * (buttress - 0.5))
        d = lo + span * np.clip(u, 0.0, 1.0) + 0.10 * (loop_noise(s, L, 2.5, sd_seed + 20 + j) - 0.5)
        d = np.clip(d, lo, hi)
        over = 0.24 * OVER[kb, j] * (0.4 + 0.6 * (j < nb - 1))
        under = 0.16 * loop_noise(s, L, 4.0, sd_seed + 40 + j)
        top = bnd[j] if j == 0 else bnd[j] - 0.07
        bot = bnd[j + 1] if j == nb - 1 else bnd[j + 1] + 0.07
        mid = 0.5 * (top + bot) + 0.12 * (bot - top) * (loop_noise(s, L, 3.0, sd_seed + 60 + j) - 0.5)
        chip = 0.14 * (loop_noise(s, L, 1.4, sd_seed + 80 + j) - 0.5)
        rows_z += [top, mid, bot]
        rows_d += [np.clip(d + over, lo, hi + 0.25), np.clip(d + chip, lo, hi), np.clip(d - under, lo * 0.8, hi)]
    Z = np.stack(rows_z, 1)
    Dd = np.stack(rows_d, 1)
    Z = Z + 0.05 * (np.stack([loop_noise(s, L, 2.2, sd_seed + 200 + r) for r in range(Z.shape[1])], 1) - 0.5) * 2
    Z[:, 0] = z_top
    Z = np.minimum(Z, pz - 0.1)
    inset = _wall_inset(bvh, Pc, N, Z)
    R = -follow * inset + Dd
    R = _unfold_rows(Pc, N, R, tg)
    cap_in = _wall_inset(bvh, Pc, N, Z[:, :1])[:, 0] + 0.25        # the cap tucks 0.25 m into the wall at the lip height
    Rall = np.concatenate([-cap_in[:, None], R], 1)
    Zall = np.concatenate([Z[:, :1], Z], 1)
    jit_t = 0.10 * (np.stack([loop_noise(s, L, 1.3, sd_seed + 300 + r) for r in range(Zall.shape[1])], 1) - 0.5) * 2
    gap = np.diff(np.concatenate([s, [s[0] + L]]))
    jit_t *= np.clip(np.minimum(gap, np.roll(gap, 1)) / 1.0, 0.0, 1.0)[:, None]   # doubled fissure columns stay apart
    shear = 0.32 * (loop_noise(s, L, 7.0, sd_seed + 400) - 0.5) * 2         # joints lean: along-shore shift grows with height
    jit_t = jit_t + shear[:, None] * (Zall - 0.5 * (pz + bottom_z))
    nr = Zall.shape[1]
    X = Pc[:, None, 0] + N[:, None, 0] * Rall + tg[:, None, 0] * jit_t
    Y = Pc[:, None, 1] + N[:, None, 1] * Rall + tg[:, None, 1] * jit_t
    # pieces along the loop (shared boundary columns: no gaps)
    n_piece = max(1, int(round(L / piece_m)))
    cuts = [int(round(k * m / n_piece)) for k in range(n_piece)] + [m]
    objs = []
    for k in range(n_piece):
        cols = [c % m for c in range(cuts[k], cuts[k + 1] + 1)]
        s_c = s[cols].copy()
        if cols[-1] == 0 and len(cols) > 1:
            s_c[-1] = L
        verts, faces, uvs, mi = [], [], [], []
        vid = {}
        for ci, c in enumerate(cols):
            for r in range(nr):
                vid[(ci, r)] = len(verts)
                verts.append((float(X[c, r]), float(Y[c, r]), float(Zall[c, r])))
        for ci in range(len(cols) - 1):
            c0, c1 = cols[ci], cols[ci + 1]
            for r in range(nr - 1):
                faces.append((vid[(ci, r)], vid[(ci, r + 1)], vid[(ci + 1, r + 1)], vid[(ci + 1, r)]))
                corner = [(ci, r, c0), (ci, r + 1, c0), (ci + 1, r + 1, c1), (ci + 1, r, c1)]
                uvs.append([(s_c[a] / tile, (Zall[c, rr] - Rall[c, rr]) / tile) for a, rr, c in corner])
                zc = 0.25 * (Zall[c0, r] + Zall[c0, r + 1] + Zall[c1, r] + Zall[c1, r + 1])
                mi.append(1 if zc < wet_z else 0)
        u0 = math.floor(min(u for fu in uvs for u, _ in fu))
        uvs = [[(u - u0, v) for u, v in fu] for fu in uvs]
        objs.append(_new_piece(D, _next_name(D, name), verts, faces, uvs, mi, [mat_hi, mat_lo]))
    return objs


def _hex_prism(cx, cy, r, z0, z1, rot, lean=(0.0, 0.0), cap=True):
    """Hexagonal prism side quads (+ top cap) from z0 to z1; `lean` moves the BOTTOM ring by (dx, dy)."""
    ang = [rot + k * math.pi / 3 for k in range(6)]
    bot = [(cx + lean[0] + r * math.cos(a), cy + lean[1] + r * math.sin(a), z0) for a in ang]
    top = [(cx + r * math.cos(a), cy + r * math.sin(a), z1) for a in ang]
    return bot, top


def _basalt_loop(D, Pl, li, bvh, rnd, bottom_z, disp_m, follow, lip_m, width_m, rows, mat, tile, piece_m, name):
    pz = D.play_z
    Pc, s, L, N, isv = _loop_columns(Pl, 0.5)
    m = len(Pc)
    pieces, cur, cur_len, objs = [], [], 0.0, []

    def flush():
        if cur:
            verts, faces, uvs = [], [], []
            for (bot, top, u0) in cur:
                base = len(verts)
                verts += bot + top
                side = math.dist(top[0][:2], top[1][:2])
                for k in range(6):
                    k2 = (k + 1) % 6
                    faces.append((base + k, base + k2, base + 6 + k2, base + 6 + k))
                    uvs.append([(u0 + k * side / tile, bot[k][2] / tile), (u0 + (k + 1) * side / tile, bot[k2][2] / tile),
                                (u0 + (k + 1) * side / tile, top[k2][2] / tile), (u0 + k * side / tile, top[k][2] / tile)])
                faces.append(tuple(base + 6 + k for k in range(6)))
                uvs.append([(top[k][0] / tile, top[k][1] / tile) for k in range(6)])
            ush = math.floor(min(u for fu in uvs for u, _ in fu))
            vsh = math.floor(min(v for fu in uvs for _, v in fu))
            uvs = [[(u - ush, v - vsh) for u, v in fu] for fu in uvs]
            objs.append(_new_piece(D, _next_name(D, name), verts, faces, uvs, [0] * len(faces), [mat], sharp_deg=25.0))
    for row in range(rows):
        acc = rnd.uniform(0, width_m[1]) if row else 0.0
        while acc < L:
            w = rnd.uniform(*width_m)
            sc = acc + w * 0.5
            acc += w * rnd.uniform(0.86, 0.98)
            if sc >= L:
                break
            k = int(np.searchsorted(s, sc, side="right") - 1)
            k2 = (k + 1) % m
            t = (sc - s[k]) / max((s[k2] if k2 else L) - s[k], 1e-6)
            T = Pc[k] + (Pc[k2] - Pc[k]) * t
            n = N[k] + (N[k2] - N[k]) * t
            n /= max(math.hypot(*n), 1e-9)
            r = w * 0.5 * 1.10
            if row == 0:
                out = rnd.uniform(*disp_m)                      # outer face this far proud of the grass edge
                c = T + n * (out - r)
                lip = rnd.uniform(*lip_m)
            else:
                c = T - n * (r * rnd.uniform(0.15, 0.55))
                lip = rnd.uniform(lip_m[0] * 0.6, lip_m[0] + 0.5 * (lip_m[1] - lip_m[0]))
            ztop = min(pz - lip, pz - 0.12)
            inset_bot = _wall_inset(bvh, T[None], n[None], np.array([[max(bottom_z, -1.0)]]))[0, 0] if follow > 0 else 0.0
            lean_v = -n * follow * inset_bot
            nseg = rnd.choice((1, 2, 2, 3))
            cuts = sorted(rnd.uniform(bottom_z + 0.8, ztop - 0.6) for _ in range(nseg - 1))
            zs = [bottom_z] + cuts + [ztop]
            rot = rnd.uniform(0, math.pi / 3)
            for g in range(nseg):
                f0 = (zs[g] - bottom_z) / max(ztop - bottom_z, 1e-6)
                f1 = (zs[g + 1] - bottom_z) / max(ztop - bottom_z, 1e-6)
                rr = r * rnd.uniform(0.93, 1.05)
                jx, jy = rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05)
                c0 = (c[0] + lean_v[0] * (1 - f0) + jx, c[1] + lean_v[1] * (1 - f0) + jy)
                c1 = (c[0] + lean_v[0] * (1 - f1) + jx, c[1] + lean_v[1] * (1 - f1) + jy)
                bot, top = _hex_prism(c1[0], c1[1], rr, zs[g] + (0.0 if g == 0 else -0.04), zs[g + 1],
                                      rot + rnd.uniform(-0.06, 0.06), lean=(c0[0] - c1[0], c0[1] - c1[1]))
                cur.append((bot, top, sc / tile + g * 0.37))
            cur_len += w
            if cur_len >= piece_m:
                flush()
                cur, cur_len = [], 0.0
    flush()
    return objs


# ============================================================================= sea: ocean grid, shelf, surf
def _graded(c0, c1, lo, hi, cell, growth=1.22, max_cell=400.0):
    xs = list(np.arange(c0, c1 + 1e-6, cell))
    if xs[-1] < c1:
        xs.append(c1)
    x, w = xs[-1], cell
    while x < hi - 1e-6:
        w = min(w * growth, max_cell)
        x = min(x + w, hi)
        xs.append(x)
    x, w, left = xs[0], cell, []
    while x > lo + 1e-6:
        w = min(w * growth, max_cell)
        x = max(x - w, lo)
        left.append(x)
    return np.array(left[::-1] + xs)


def _ocean_grid(D, name, mat, cell=16.0, half=2000.0, margin=130.0, cut_under_land_m=12.0):
    bx0, by0, bx1, by1 = P._shore_bbox_m(D)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    xs = _graded(bx0 - margin, bx1 + margin, cx - half, cx + half, cell)
    ys = _graded(by0 - margin, by1 + margin, cy - half, cy + half, cell)
    GX, GY = np.meshgrid(xs, ys, indexing="ij")
    sd = np.full(GX.shape, 1e3)
    near = (GX > bx0 - 5) & (GX < bx1 + 5) & (GY > by0 - 5) & (GY < by1 + 5)
    if near.any():
        sd[near] = P.signed_dist_m(D, GX[near], GY[near])
    nx, ny = len(xs), len(ys)
    vid = np.arange(nx * ny).reshape(nx, ny)
    faces = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            if max(sd[i, j], sd[i + 1, j], sd[i + 1, j + 1], sd[i, j + 1]) < -cut_under_land_m:
                continue
            faces.append((int(vid[i, j]), int(vid[i + 1, j]), int(vid[i + 1, j + 1]), int(vid[i, j + 1])))
    used = sorted({v for f in faces for v in f})
    remap = {v: k for k, v in enumerate(used)}
    verts = [(float(GX.ravel()[v]), float(GY.ravel()[v]), 0.0) for v in used]
    faces = [tuple(remap[v] for v in f) for f in faces]
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = P.new_mesh_object(name, "ENVIRONMENT")
    P.build_mesh(ob, verts, faces, smooth=True, materials=[mat])
    D.objects[name] = ob
    return _track(D, ob)


def _region_mesh(D, name, loops, z, mat, spacing, col="ENVIRONMENT"):
    res = P._triangulate_region(loops, spacing)
    if res is None:
        return None, None
    V, T = res
    ob = P.new_mesh_object(name, col)
    P.build_mesh(ob, [(float(x), float(y), z) for x, y in V], [tuple(int(i) for i in t) for t in T], smooth=True,
                 materials=[mat])
    D.objects[name] = ob
    return _track(D, ob), V


def _set_surf_attrs(ob, A, R):
    me = ob.data
    for nm in [a.name for a in me.color_attributes]:
        me.color_attributes.remove(me.color_attributes[nm])
    att = me.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
    col = np.stack([R, np.zeros_like(R), np.zeros_like(R), A], 1)
    att.data.foreach_set("color", col.astype(np.float32).ravel())
    try:
        me.color_attributes.active_color_name = "Col"
        me.color_attributes.render_color_index = 0
    except Exception:
        pass
    W = np.array([v.co[:] for v in me.vertices])
    lay = _uv_layer(me)
    lv = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    U, V = W[lv, 0] / 8.0, W[lv, 1] / 8.0
    U -= np.round(U.mean())
    V -= np.round(V.mean())
    lay.data.foreach_set("uv", np.stack([U, V], 1).ravel())
    me.update()


def _pieces_by_cluster(loops, cluster_m):
    """Group contour loops (outer CCW + holes CW) into pieces, then pieces into clusters of about cluster_m metres."""
    outers = [L_ for L_ in loops if P.signed_area(L_) > 0]
    holes = [L_ for L_ in loops if P.signed_area(L_) <= 0]
    pieces = [[o] for o in outers]
    for h in holes:
        c = h.mean(0)
        for pc in pieces:
            if P.point_in_poly(c, pc[0]):
                pc.append(h)
                break
    groups = {}
    for pc in pieces:
        c = pc[0].mean(0)
        key = (int(math.floor(c[0] / cluster_m)), int(math.floor(c[1] / cluster_m)))
        groups.setdefault(key, []).append(pc)
    return pieces, [sum(g, []) for _, g in sorted(groups.items())]


def build_sea(D, ocean=True, ocean_cell_m=16.0, shelf=True, shelf_m=(10.0, 24.0), inner_m=4.0, surf=True,
              surf_m=(1.8, 6.5), surf_inner_m=-2.5, surf_gap=0.40, shelf_surf=True, cluster_m=90.0, seed=0, cell=1.0):
    """The sea around the islands (Needle, Split). Deletes WATER_SHALLOW / WATER_FOAM / WATER_FOAM_CREST, then builds:
      WATER_OCEAN   one flat graded grid at z 0 (LK_WATER, see WHY THE OCEAN IS A GRID); ocean=False keeps the old plane
      WATER_SHELF   z 0.06, LK_WATER_SHALLOW: from inner_m under the walls (hidden) out to a RAGGED outer edge 10-24 m
                    (shelf_m) from the shore: low-frequency width + 6 m fingers + 2 m rag
      WATER_SURF_nn z 0.12, LK_SURF: whitewater pieces hugging the real shore (signed_dist_m): from surf_inner_m (under the
                    cliff skin) out to 1.8-6.5 m (surf_m), broken by a noise mask (surf_gap = share of the shore left without
                    foam), plus sparse patches on the shelf edge (shelf_surf). Vertex colour 'Col': A = shoreline closeness
                    (1 at the wet line, 0 at every open edge incl. the ends of each piece), R = phase (smooth noise 0..1);
                    UV0 = world (x, y) / 8 m. Pieces are clustered into objects of about cluster_m metres.
    Returns {name: obj}."""
    t0 = time.time()
    rng_seed = D.number * 977 + seed
    out = {}
    old = [nm for nm in ("WATER_SHALLOW", "WATER_FOAM", "WATER_FOAM_CREST") if bpy.data.objects.get(nm) is not None]
    old += [o.name for o in bpy.data.objects if o.name.startswith("WATER_SURF") and o.get("surf_kind") in ("shore", "shelf")]
    for nm in old:                                # the old bands, and this function's own surf when it is re-run
        D.objects.pop(nm, None)
        P.remove_object(nm)
    if ocean:
        out["WATER_OCEAN"] = _ocean_grid(D, "WATER_OCEAN", look_material("LK_WATER", D), cell=ocean_cell_m)
    bx0, by0, bx1, by1 = P._shore_bbox_m(D)
    ext = shelf_m[1] + 12.0
    grid = P._Grid((bx0 - ext, by0 - ext, bx1 + ext, by1 + ext), cell, pad=2)
    GX, GY = grid.X, grid.Y
    sd = P.signed_dist_m(D, GX, GY)
    w_shelf = (shelf_m[0] + (shelf_m[1] - shelf_m[0]) * fbm(GX, GY, 55.0, rng_seed + 1)
               + 4.0 * (vnoise(GX, GY, 7.0, rng_seed + 2) - 0.5) + 1.6 * (vnoise(GX, GY, 2.2, rng_seed + 3) - 0.5))
    if shelf:
        F = np.minimum(w_shelf - sd, sd + inner_m)
        loops = P._contours(grid, F > 0, F=F, simplify=0.05, min_area=12.0)
        ob, _ = _region_mesh(D, "WATER_SHELF", loops, Z_SHELF, look_material("LK_WATER_SHALLOW", D), 7.0)
        if ob:
            out["WATER_SHELF"] = ob
    if surf:
        w_s = surf_m[0] + (surf_m[1] - surf_m[0]) * fbm(GX, GY, 28.0, rng_seed + 4)
        mask = fbm(GX, GY, 11.0, rng_seed + 5, octaves=2)
        thr = np.quantile(mask[(sd > -1) & (sd < 3)], surf_gap) if ((sd > -1) & (sd < 3)).any() else 0.4
        Fb = np.minimum(w_s - sd, sd - surf_inner_m)
        Fm = (mask - thr) * 30.0
        F = np.minimum(Fb, Fm)
        fields = [("shore", F, w_s, thr)]
        if shelf_surf and shelf:
            m2 = fbm(GX, GY, 16.0, rng_seed + 6, octaves=2)
            thr2 = 0.62
            F2 = np.minimum(np.minimum(1.3 - np.abs(sd - (w_shelf - 1.0)), (m2 - thr2) * 30.0), sd - 4.0)
            fields.append(("shelf", F2, None, thr2))
        mat = look_material("LK_SURF", D)
        n_obj, n_pieces = 0, 0
        for kind, Fk, wk, thk in fields:
            loops = P._contours(grid, Fk > 0, F=Fk, simplify=0.04, min_area=3.0)
            pieces, groups = _pieces_by_cluster(loops, cluster_m)
            n_pieces += len(pieces)
            for g in groups:
                nm = _next_name(D, "WATER_SURF")
                ob, V = _region_mesh(D, nm, g, Z_SURF, mat, 1.4)
                if ob is None:
                    continue
                X, Y = V[:, 0], V[:, 1]
                s_ = P.signed_dist_m(D, X, Y)
                if kind == "shore":
                    w_ = surf_m[0] + (surf_m[1] - surf_m[0]) * fbm(X, Y, 28.0, rng_seed + 4)
                    a_rad = 1.0 - _smoothstep(0.3, 1.0, (s_ - 0.3) / np.maximum(w_ - 0.3, 0.3))
                    mk = fbm(X, Y, 11.0, rng_seed + 5, octaves=2)
                    a_m = _smoothstep(thk, thk + 0.06, mk)
                    A = np.clip(a_rad * a_m, 0, 1)
                else:
                    ws = (shelf_m[0] + (shelf_m[1] - shelf_m[0]) * fbm(X, Y, 55.0, rng_seed + 1)
                          + 4.0 * (vnoise(X, Y, 7.0, rng_seed + 2) - 0.5) + 1.6 * (vnoise(X, Y, 2.2, rng_seed + 3) - 0.5))
                    a_rad = 1.0 - _smoothstep(0.0, 1.3, np.abs(s_ - (ws - 1.0)))
                    a_m = _smoothstep(thk, thk + 0.08, fbm(X, Y, 16.0, rng_seed + 6, octaves=2))
                    A = np.clip(0.7 * a_rad * a_m, 0, 1)
                if float(A.max()) < 0.5:                  # a piece too faint to read: drop it (keeps every object's A ramp >= 0.5)
                    D.objects.pop(nm, None)
                    P.remove_object(nm)
                    continue
                Rp = fbm(X, Y, 23.0, rng_seed + 9)
                Rp = np.clip((Rp - Rp.min()) / max(Rp.max() - Rp.min(), 1e-6), 0, 1)
                _set_surf_attrs(ob, A, Rp)
                ob["surf_kind"] = kind
                out[nm] = ob
                n_obj += 1
        _log(f"build_sea: surf {n_pieces} pieces in {n_obj} objects")
    _log(f"build_sea: {', '.join(f'{k} {len(v.data.polygons)}f' for k, v in out.items())} ({time.time() - t0:.1f}s)")
    return out


def surf_patch(D, center_m, radius_m=6.0, name=None, seed=0, z=Z_SURF, strength=1.0):
    """One ragged whitewater patch (LK_SURF, vertex colour A fading to 0 at the rim, R phase, UV world/8) - e.g. the foot
    of a waterfall. Returns the object (WATER_SURF_nn unless `name`)."""
    rnd_seed = D.number * 4243 + seed
    cx, cy = center_m
    n = 48
    ang = np.linspace(0, 2 * math.pi, n, endpoint=False)
    rr = radius_m * (0.72 + 0.5 * vnoise(np.cos(ang) * 3 + 10, np.sin(ang) * 3 + 10, 1.3, rnd_seed))
    ring = np.stack([cx + rr * np.cos(ang), cy + rr * np.sin(ang)], 1)
    nm = name or _next_name(D, "WATER_SURF")
    ob, V = _region_mesh(D, nm, [ring], z, look_material("LK_SURF", D), max(0.8, radius_m / 5))
    d = np.hypot(V[:, 0] - cx, V[:, 1] - cy)
    rl = np.interp(np.arctan2(V[:, 1] - cy, V[:, 0] - cx) % (2 * math.pi), np.append(ang, 2 * math.pi), np.append(rr, rr[0]))
    A = strength * (1.0 - _smoothstep(0.35, 1.0, d / np.maximum(rl, 1e-6)))
    _set_surf_attrs(ob, np.clip(A, 0, 1), vnoise(V[:, 0], V[:, 1], 9.0, rnd_seed + 1))
    ob["surf_kind"] = "patch"
    return ob


# ============================================================================= lava
def build_lava(D, cell_m=3.5, near_m=45.0, mid_m=130.0, extent_m=None, inner_margin_m=8.0, lights=4, light_z=2.2,
               light_points=None, name="WATER_LAVA"):
    """Replace the 1-polygon lava plane by a subdivided WATER_LAVA at z 0 (LK_LAVA, UV world / 24 m): cells of cell_m
    within near_m of the land and over every water ellipse, 2.5 x coarser to mid_m, 7 x coarser out to the extent (a disc
    reaching 40 m past SCENERY['wall_ring'] r_outer, else the shore box + 350 m). The land interior deeper than
    inner_margin_m inside the walls is left out (the undercut walls hide the edge). Also places `lights` LAVA_LIGHT_nn
    EMPTY objects (Unity puts static orange point lights there) light_z above the lava, 3-14 m off the walls, around the
    lava ellipse, inside SCENERY['crater'] rim_radius - 10 m when given, spread by farthest-point sampling starting at the
    pin side; or exactly at light_points [(x_m, y_m[, z])]. Returns {name: obj}."""
    t0 = time.time()
    sc = D.scenery
    wr = sc.get("wall_ring")
    bx0, by0, bx1, by1 = P._shore_bbox_m(D)
    if extent_m is None:
        if wr:
            cx, cy = P.m(wr["cx"], wr["cd"])
            R = wr["r_outer"] * YD + 40.0
            ext = ("disc", cx, cy, R)
        else:
            ext = ("box", bx0 - 350, by0 - 350, bx1 + 350, by1 + 350)
    else:
        ext = extent_m
    if ext[0] == "disc":
        _, cx, cy, R = ext
        x0, y0, x1, y1 = cx - R, cy - R, cx + R, cy + R
    else:
        _, x0, y0, x1, y1 = ext
    ells = [(P.m(hx, hd), w / 2 * YD, l / 2 * YD) for kind, hx, hd, w, l, tag in D.hole.hazards if kind == "water"]

    def grid_pts(cell, off):
        xs = np.arange(x0 + off * cell, x1, cell)
        ys = np.arange(y0, y1, cell * 0.866)
        GX, GY = np.meshgrid(xs, ys, indexing="ij")
        GX = GX + (np.arange(len(ys))[None, :] % 2) * cell * 0.5
        return GX.ravel(), GY.ravel()
    pts = []
    for cell, lo, hi in ((cell_m, -inner_margin_m, near_m), (cell_m * 2.5, near_m, mid_m), (cell_m * 7.0, mid_m, 1e9)):
        X, Y = grid_pts(cell, 0.37)
        if ext[0] == "disc":
            k = np.hypot(X - cx, Y - cy) <= R
            X, Y = X[k], Y[k]
        near_box = (X > bx0 - hi - 5) & (X < bx1 + hi + 5) & (Y > by0 - hi - 5) & (Y < by1 + hi + 5) if hi < 1e8 else np.ones(len(X), bool)
        s_ = np.full(len(X), 1e4)
        cand = (X > bx0 - mid_m - 10) & (X < bx1 + mid_m + 10) & (Y > by0 - mid_m - 10) & (Y < by1 + mid_m + 10)
        if cand.any():
            s_[cand] = P.signed_dist_m(D, X[cand], Y[cand])
        in_ell = np.zeros(len(X), bool)
        for (ex, ey), a, b in ells:
            in_ell |= ((X - ex) / (a + 6)) ** 2 + ((Y - ey) / (b + 6)) ** 2 <= 1
        if lo < 0:
            keep = ((s_ >= lo) & (s_ < hi)) | (in_ell & (s_ >= lo))
        else:
            keep = (s_ >= lo) & (s_ < hi) & ~in_ell & near_box
        pts.append(np.stack([X[keep], Y[keep]], 1))
    if ext[0] == "disc":
        nring = max(64, int(2 * math.pi * R / (cell_m * 7.0)))
        th = np.linspace(0, 2 * math.pi, nring, endpoint=False)
        pts.append(np.stack([cx + R * np.cos(th), cy + R * np.sin(th)], 1))
    Pp = np.vstack(pts)
    V, T = P._cdt(Pp, [])
    cen = V[T].mean(1)
    sdc = P.signed_dist_m(D, cen[:, 0], cen[:, 1])
    T = T[sdc >= -inner_margin_m]
    V, T = P._compact(V, T)
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = P.new_mesh_object(name, "ENVIRONMENT")
    P.build_mesh(ob, [(float(x), float(y), 0.0) for x, y in V], [tuple(int(i) for i in t) for t in T], smooth=True,
                 materials=[look_material("LK_LAVA", D)])
    D.objects[name] = ob
    _track(D, ob)
    assign_uvs(D, objects=[ob])
    out = {name: ob}
    # ---- LAVA_LIGHT_nn
    for o in [o for o in bpy.data.objects if o.name.startswith("LAVA_LIGHT_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    if light_points is None:
        cand = V[(np.hypot(V[:, 0] - (bx0 + bx1) / 2, V[:, 1] - (by0 + by1) / 2) < 0.75 * max(bx1 - bx0, by1 - by0))]
        s_ = P.signed_dist_m(D, cand[:, 0], cand[:, 1])
        cand = cand[(s_ >= 3.0) & (s_ <= 14.0)]
        if ells:
            (ex, ey), a, b = ells[0]
            de = np.hypot((cand[:, 0] - ex) / (a + 45), (cand[:, 1] - ey) / (b + 45))
            if (de <= 1).sum() >= lights:
                cand = cand[de <= 1]
        cr = sc.get("crater")
        if cr and len(cand):                      # stay well inside SCENERY['crater'] rim_radius (postcard_look_verify limit + 20 m)
            ccx, ccy = P.m(cr["cx"], cr["cd"])
            inside = np.hypot(cand[:, 0] - ccx, cand[:, 1] - ccy) <= cr.get("rim_radius", 200.0) * YD - 10.0
            if inside.sum() >= lights:
                cand = cand[inside]
        pin = np.array(P.m(*D.hole.pin))
        chosen = [int(np.argmin(np.hypot(cand[:, 0] - pin[0], cand[:, 1] - pin[1])))] if len(cand) else []
        while len(chosen) < min(lights, len(cand)):
            dmin = np.min(np.stack([np.hypot(cand[:, 0] - cand[c, 0], cand[:, 1] - cand[c, 1]) for c in chosen]), 0)
            chosen.append(int(np.argmax(dmin)))
        light_points = [(float(cand[c, 0]), float(cand[c, 1]), light_z) for c in chosen]
    for i, p in enumerate(light_points):
        e = bpy.data.objects.new(f"LAVA_LIGHT_{i + 1:02d}", None)
        e.empty_display_type = 'SPHERE'
        e.empty_display_size = 1.5
        bpy.context.scene.collection.objects.link(e)
        P.link_to(e, "ENVIRONMENT")
        e.parent = P.get_root()
        e.location = (p[0], p[1], p[2] if len(p) > 2 else light_z)
        D.objects[e.name] = e
        _track(D, e)
        out[e.name] = e
    _log(f"build_lava: {name} {len(T)} tris ({len(V)} verts), {len(light_points)} LAVA_LIGHT empties ({time.time() - t0:.1f}s)")
    return out


# ============================================================================= stone path
def _ground_bvh(D):
    V, F = [], []
    for ob in _export_meshes(D):
        if not ob.name.startswith(GROUND_PREFIXES):
            continue
        W, ls, lt, lv, mi, pn = _mesh_arrays(ob)
        base = len(V)
        V += [tuple(p) for p in W.tolist()]
        for p in np.nonzero(pn[:, 2] > 0.5)[0].tolist():
            a, n = int(ls[p]), int(lt[p])
            F.append([base + int(v) for v in lv[a:a + n]])
    return BVHTree.FromPolygons(V, F)


def _ground_top(bvh, X, Y, z0, r=0.5):
    out = np.full(len(X), -1e9)
    for dx, dy in (((0, 0),) if r <= 0 else ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r))):
        for i, (x, y) in enumerate(zip(X.tolist(), Y.tolist())):
            hit = bvh.ray_cast(Vector((x + dx, y + dy, z0)), Vector((0, 0, -1)), 50.0)
            if hit[0] is not None:
                out[i] = max(out[i], hit[0].z)
    return out


def build_path(D, polyline, width_m=2.4, units="yd", seed=0, step_m=0.6, z_off=Z_PATH, wobble=0.16, notch=0.22,
               skirt_m=0.04, clip_to_land=True, name="DRESS_PATH"):
    """Irregular flagstone path DRESS_PATH_nn (LK_PATH, non-colliding) along `polyline` (course yards, or metres with
    units='m'), Catmull-Rom smoothed. Half-widths wander +-wobble, a few bites (notch), rounded tapered ends; every vertex
    sits z_off above the highest play surface within 0.5 m under it (so it never dips under a fairway edge) and a skirt
    runs down from the outline to skirt_m under the ground right below it, so a step between surfaces shows no gap (lowest
    vertex PLAY_Z - 0.04: inside the 'sits on the pad' band of postcard_look_verify). Pieces are clipped
    to land (>= half width + 0.3 m inside the shore). UV: u = lateral / 5 m, v = arc / 5 m. Returns the objects."""
    rnd = random.Random(D.number * 7717 + seed)
    sc = YD if units == "yd" else 1.0
    pts = [(x * sc, y * sc) for x, y in polyline]
    cr = P.catmull_rom(pts, samples_per_seg=12, closed=False) if len(pts) > 2 else [Vector(p) for p in pts]
    dense = P.resample([(p[0], p[1]) for p in cr], step_m, closed=False)
    C = np.array([(p[0], p[1]) for p in dense])
    seg = np.diff(C, axis=0)
    Ls = np.hypot(seg[:, 0], seg[:, 1])
    s = np.concatenate([[0.0], np.cumsum(Ls)])
    tg = np.gradient(C, axis=0)
    tg /= np.maximum(np.hypot(tg[:, 0], tg[:, 1]), 1e-9)[:, None]
    rt = np.stack([tg[:, 1], -tg[:, 0]], 1)
    hw = width_m / 2
    nseed = D.number * 53 + seed
    wl = hw * (1 + wobble * 2 * (fbm(s, np.zeros_like(s), 7.0, nseed + 1) - 0.5) + 0.1 * (vnoise(s, 0 * s, 1.1, nseed + 2) - 0.5))
    wr_ = hw * (1 + wobble * 2 * (fbm(s, np.zeros_like(s), 7.0, nseed + 3) - 0.5) + 0.1 * (vnoise(s, 0 * s, 1.1, nseed + 4) - 0.5))
    for w_ in (wl, wr_):
        for _ in range(max(1, int(s[-1] / 9.0))):
            c = rnd.uniform(0, s[-1])
            ln = rnd.uniform(0.5, 1.2)
            w_ *= 1 - notch * np.exp(-((s - c) / ln) ** 2)
    taper = np.sqrt(np.clip(np.minimum(s, s[-1] - s) / 1.2, 0.12, 1.0))
    wl, wr_ = wl * taper, wr_ * taper
    ok = np.ones(len(C), bool)
    if clip_to_land:
        sd = P.signed_dist_m(D, C[:, 0], C[:, 1])
        ok = sd <= -(np.maximum(wl, wr_) + 0.3)
    runs, cur = [], []
    for i, k in enumerate(ok.tolist()):
        if k:
            cur.append(i)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    runs = [r for r in runs if s[r[-1]] - s[r[0]] >= 2.0]
    bvh = _ground_bvh(D)
    mat = look_material("LK_PATH", D)
    tile = LOOK["LK_PATH"][2]
    fr = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
    objs = []
    for run in runs:
        idx = np.array(run)
        n = len(idx)
        lat = np.where(fr[None, :] < 0, fr[None, :] * wl[idx][:, None], fr[None, :] * wr_[idx][:, None])
        X = C[idx, 0][:, None] + rt[idx, 0][:, None] * lat
        Y = C[idx, 1][:, None] + rt[idx, 1][:, None] * lat
        Zg = _ground_top(bvh, X.ravel(), Y.ravel(), D.play_z + 3.0).reshape(X.shape)
        Zg = np.where(Zg < -1e8, D.play_z, Zg)
        Z = Zg + z_off
        Zp = _ground_top(bvh, X.ravel(), Y.ravel(), D.play_z + 3.0, r=0.0).reshape(X.shape)    # ground right below
        Zs = np.where(Zp < -1e8, D.play_z, Zp) - skirt_m                                         # skirt foot
        verts, faces, uvs = [], [], []
        vid = np.zeros((n, 7), np.int64)
        for i in range(n):
            for k in range(5):
                vid[i, k + 1] = len(verts)
                verts.append((float(X[i, k]), float(Y[i, k]), float(Z[i, k])))
            for side, k, col in ((-1, 0, 0), (1, 4, 6)):          # skirt foot just outside the outline, skirt_m under the ground
                vid[i, col] = len(verts)
                verts.append((float(X[i, k] + side * rt[idx[i], 0] * 0.04), float(Y[i, k] + side * rt[idx[i], 1] * 0.04),
                              float(Zs[i, k])))
        lat_full = np.concatenate([lat[:, :1] - 0.04 - skirt_m, lat, lat[:, -1:] + 0.04 + skirt_m], 1)
        for i in range(n - 1):
            for k in range(6):
                f = (int(vid[i, k]), int(vid[i, k + 1]), int(vid[i + 1, k + 1]), int(vid[i + 1, k]))
                faces.append(f)
                uvs.append([(lat_full[i, k] / tile, s[idx[i]] / tile), (lat_full[i, k + 1] / tile, s[idx[i]] / tile),
                            (lat_full[i + 1, k + 1] / tile, s[idx[i + 1]] / tile), (lat_full[i + 1, k] / tile, s[idx[i + 1]] / tile)])
        for i, back in ((0, True), (n - 1, False)):               # end skirts across the whole end section
            for k in range(6):
                a, b = int(vid[i, k]), int(vid[i, k + 1])
                d = -tg[idx[i]] * 0.04 if back else tg[idx[i]] * 0.04
                va = len(verts)
                za = float(Zs[i, max(0, min(4, k - 1))])
                zb = float(Zs[i, max(0, min(4, k))])
                verts.append((verts[a][0] + d[0], verts[a][1] + d[1], min(verts[a][2], za)))
                verts.append((verts[b][0] + d[0], verts[b][1] + d[1], min(verts[b][2], zb)))
                f = (a, va, va + 1, b) if back else (b, va + 1, va, a)
                faces.append(f)
                v0 = s[idx[i]] / tile
                uvs.append([(lat_full[i, k] / tile, v0), (lat_full[i, k] / tile, v0 - 0.03), (lat_full[i, k + 1] / tile, v0 - 0.03),
                            (lat_full[i, k + 1] / tile, v0)] if back else
                           [(lat_full[i, k + 1] / tile, v0), (lat_full[i, k + 1] / tile, v0 + 0.03), (lat_full[i, k] / tile, v0 + 0.03),
                            (lat_full[i, k] / tile, v0)])
        vsh = math.floor(min(v for fu in uvs for _, v in fu))
        uvs = [[(u, v - vsh) for u, v in fu] for fu in uvs]
        ob = _new_piece(D, _next_name(D, name), verts, faces, uvs, [0] * len(faces), [mat], col="STRUCTURES", sharp_deg=50.0)
        objs.append(ob)
    _log(f"build_path: {len(objs)} pieces, {sum(len(o.data.polygons) for o in objs)} faces")
    return objs


# ============================================================================= export
class _ExportSceneProxy:
    def __init__(self, real, extra):
        self._real, self._extra = real, extra

    def __getattr__(self, k):
        f = getattr(self._real, k)
        if k != "fbx":
            return f
        extra = self._extra

        def fbx(*a, **kw):
            kw.update(extra)
            return f(*a, **kw)
        return fbx


class _OpsProxy:
    def __init__(self, real, extra):
        self._real, self._extra = real, extra

    def __getattr__(self, k):
        if k == "export_scene":
            return _ExportSceneProxy(self._real.export_scene, self._extra)
        return getattr(self._real, k)


class _BpyProxy:
    def __init__(self, real, extra):
        self._real = real
        self.ops = _OpsProxy(real.ops, extra)

    def __getattr__(self, k):
        return getattr(self._real, k)


def export_look_fbx(D, path=None, colors_type="LINEAR"):
    """postcard_lib.export_fbx (same object selection, axes, unit scale, .meta handling, hole 7 guard) with three extra
    exporter options: path_mode='STRIP', embed_textures=False (LOOK_CONTRACT section 4) and colors_type (LINEAR:
    WATER_SURF A / R arrive as raw data). The FBX carries NO texture reference at all (see _passthru: materialName 0 in
    the .meta would otherwise name Unity's material after the texture); any direct image link on an LK_* material made by
    another lib is cut for the duration of the export and restored. Unity's GolfLook loads the PNGs by material name."""
    extra = dict(path_mode='STRIP', embed_textures=False, colors_type=colors_type)
    cut = []                                      # direct image -> BSDF / Normal Map links (materials made elsewhere)
    for mat in bpy.data.materials:
        if not mat.name.startswith("LK_") or mat.node_tree is None:
            continue
        for ln in list(mat.node_tree.links):
            if ln.from_node.type == 'TEX_IMAGE' and ln.to_node.type in ('BSDF_PRINCIPLED', 'NORMAL_MAP'):
                cut.append((mat.node_tree, ln.from_socket, ln.to_socket))
                mat.node_tree.links.remove(ln)
    real = P.bpy
    P.bpy = _BpyProxy(real, extra)
    try:
        return P.export_fbx(D, path)
    finally:
        P.bpy = real
        for nt, a, b in cut:
            nt.links.new(a, b)


# ============================================================================= gates / audits
def snapshot_ground(D):
    """{name: world vertex array} of every TERRAIN/FAIRWAY/GREEN/TEE_BOX/BUNKER/CART_PATH mesh in the export set."""
    out = {}
    for ob in _export_meshes(D):
        if ob.name.startswith(GROUND_PREFIXES):
            out[ob.name] = _mesh_arrays(ob)[0].copy()
    return out


def compare_ground(D, snap, tol=1e-5):
    now = snapshot_ground(D)
    bad = []
    if set(now) != set(snap):
        bad.append(f"ground objects differ: added {sorted(set(now) - set(snap))}, removed {sorted(set(snap) - set(now))}")
    worst = 0.0
    nv = 0
    for k in sorted(set(now) & set(snap)):
        a, b = snap[k], now[k]
        if a.shape != b.shape:
            bad.append(f"{k} vertex count {len(a)} -> {len(b)}")
            continue
        d = float(np.abs(a - b).max()) if len(a) else 0.0
        worst = max(worst, d)
        nv += len(a)
        if d > tol:
            bad.append(f"{k} moved {d:.2e} m")
    ok = not bad
    return ok, (f"{len(now)} ground meshes, {nv} vertices, max |delta| {worst:.2e} m (tol {tol:g})" + ("" if ok else "; " + "; ".join(bad[:6])))


def _uv_stats(ob, tile_of, wall_mask=None):
    me = ob.data
    if len(me.uv_layers) != 1:
        return False, f"{ob.name}: {len(me.uv_layers)} UV layers"
    W, ls, lt, lv, mi, pn = _mesh_arrays(ob)
    uv = np.empty(len(lv) * 2)
    me.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    if not np.isfinite(uv).all():
        return False, f"{ob.name}: NaN/inf UV"
    if np.abs(uv).max() > 1e4:
        return False, f"{ob.name}: |uv| {np.abs(uv).max():.0f}"
    mats = [_mat_name(m_) for m_ in me.materials] or [""]
    ratios, wall_r = [], []
    for p in range(len(ls)):
        a, n = int(ls[p]), int(lt[p])
        tile = tile_of(mats[min(int(mi[p]), len(mats) - 1)])
        wall = wall_mask is not None and wall_mask[p]
        for k in range(n):
            i, j = a + k, a + (k + 1) % n
            wl = float(np.linalg.norm(W[lv[i]] - W[lv[j]]))
            if wl < 0.05:
                continue
            (wall_r if wall else ratios).append(float(np.linalg.norm(uv[i] - uv[j])) * tile / wl)
    r = np.array(ratios) if ratios else np.array([1.0])
    rw = np.array(wall_r) if wall_r else np.array([1.0])
    return True, (r.min(), np.percentile(r, 99.9), r.max(), float(np.abs(uv).max()), float(rw.max()))


def audit_look(D, uv_ratio=(0.45, 2.2)):
    """GATE tuples (name, ok, detail) on the current scene: no new object with a ground prefix, no MAT_FOAM, UV sanity
    (one layer, finite, |uv| < 1e4, world-vs-UV edge ratio within uv_ratio on ground/water meshes), skin under the play
    height, water stack inside z 0..0.2, surf pieces broken + vertex colours, lava tri count."""
    res = []
    ex = P._export_objects(D)
    meshes = [o for o in ex if o.type == 'MESH']
    ground = sorted(o.name for o in meshes if o.name.startswith(GROUND_PREFIXES))
    allowed = [r"^TERRAIN_[A-Za-z0-9_]+$", r"^FAIRWAY$", r"^FAIRWAY_FIRSTCUT$", r"^GREEN$", r"^GREEN_APRON$", r"^TEE_BOX$",
               r"^BUNKER_\d\d$", r"^BUNKER_\d\d_LIP$"]
    import re
    odd = [n for n in ground if not any(re.match(p, n) for p in allowed)]
    mine = D.__dict__.get("look_objects", [])
    bad_new = [n for n in mine if n.startswith(GROUND_PREFIXES)]
    res.append(("LOOK_NO_COLLISION_PREFIX", not odd and not bad_new,
                f"{len(mine)} objects made by postcard_look_lib, none with a ground prefix; ground meshes {len(ground)} all on the "
                f"postcard_verify allow-list" + (f"; BAD {odd + bad_new}" if odd or bad_new else "")))
    foam = sorted({o.name for o in meshes for m_ in o.data.materials if m_ is not None and m_.name.startswith("MAT_FOAM")})
    foam_obj = [o.name for o in meshes if o.name.startswith("WATER_FOAM")]
    mf = bpy.data.materials.get("MAT_FOAM")
    res.append(("LOOK_NO_MAT_FOAM", not foam and not foam_obj and (mf is None or mf.users == 0),
                f"exported meshes using MAT_FOAM {foam}, WATER_FOAM* objects {foam_obj}, MAT_FOAM datablock users "
                f"{mf.users if mf else 'gone'} (0-user data is neither saved nor exported)"))
    flat_mats = sorted({_mat_name(m_) for o in meshes if o.name.startswith(GROUND_PREFIXES + ("WATER_",))
                        for m_ in o.data.materials if m_ is not None and not _mat_name(m_).startswith("LK_")})
    res.append(("LOOK_GROUND_WATER_ARE_LK", not flat_mats, f"non-LK materials on ground/water meshes: {flat_mats}"))
    tile_of = lambda n: (LOOK[n][2] if n in LOOK and LOOK[n][2] > 0 else 8.0)
    worst, probs = [], []
    for o in meshes:
        if not (o.name.startswith(GROUND_PREFIXES) or o.name.startswith(("WATER_OCEAN", "WATER_SHELF", "WATER_LAVA"))):
            continue
        wm = None
        if o.name.startswith("TERRAIN"):
            W_, ls_, lt_, lv_, mi_, pn_ = _mesh_arrays(o)
            wm = ~_top_mask(D, W_, ls_, lt_, lv_, pn_)
        ok, st = _uv_stats(o, tile_of, wm)
        if not ok:
            probs.append(st)
            continue
        lo_, p999, hi_, mx, wall_max = st
        worst.append((o.name, lo_, hi_, mx, wall_max))
        if lo_ < uv_ratio[0] or hi_ > uv_ratio[1]:
            probs.append(f"{o.name} UV/world edge ratio {lo_:.2f}..{hi_:.2f}")
        if wall_max > 8.0:
            probs.append(f"{o.name} wall UV jump: ratio {wall_max:.1f} (> 8 = a seam inside a face)")
    res.append(("LOOK_UV_SANE", not probs,
                f"{len(worst)} ground/water meshes: one UV layer, finite, max |uv| {max((w[3] for w in worst), default=0):.1f}, "
                f"UV*tile/world edge ratio on every top/flat face {min((w[1] for w in worst), default=1):.2f}..{max((w[2] for w in worst), default=1):.2f} "
                f"(limits {uv_ratio[0]}..{uv_ratio[1]}); TERRAIN wall faces (hidden by the skin; arc-of-the-top-loop u) max ratio "
                f"{max((w[4] for w in worst), default=1):.2f} (<= 8: no seam jump)" + (f"; PROBLEMS {probs[:5]}" if probs else "")))
    skins = [o for o in meshes if o.name.startswith("ROCK_SKIN")]
    if skins:
        zmax = max(float(_mesh_arrays(o)[0][:, 2].max()) for o in skins)
        tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in skins)
        res.append(("LOOK_SKIN_BELOW_PLAY", zmax <= D.play_z - 0.05,
                    f"{len(skins)} ROCK_SKIN pieces, {tris} tris, highest vertex {zmax:.3f} m (play {D.play_z} - 0.05)"))
    wat = [o for o in meshes if o.name.startswith("WATER_")]
    zs = [(o.name, float(_mesh_arrays(o)[0][:, 2].min()), float(_mesh_arrays(o)[0][:, 2].max())) for o in wat if len(o.data.vertices)]
    badz = [z for z in zs if z[1] < -1e-3 or z[2] > 0.2]
    res.append(("LOOK_WATER_STACK", not badz, f"{len(zs)} WATER_* meshes inside z 0..0.2" + (f"; BAD {badz[:4]}" if badz else "")))
    surfs = [o for o in wat if o.name.startswith("WATER_SURF")]
    if surfs:
        okc, nparts, longest = True, 0, 0.0
        for o in surfs:
            me = o.data
            if "Col" not in me.color_attributes:
                okc = False
                continue
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            seen = set()
            for v in bm.verts:
                if v.index in seen:
                    continue
                stack, comp = [v], []
                seen.add(v.index)
                while stack:
                    a = stack.pop()
                    comp.append(a.co.xy.copy())
                    for e in a.link_edges:
                        b = e.other_vert(a)
                        if b.index not in seen:
                            seen.add(b.index)
                            stack.append(b)
                nparts += 1
                cc = np.array([(c.x, c.y) for c in comp])
                longest = max(longest, float(np.hypot(*(cc.max(0) - cc.min(0)))))
            bm.free()
        res.append(("LOOK_SURF_BROKEN", okc and nparts >= 12 and longest <= 140.0,
                    f"{len(surfs)} WATER_SURF objects, {nparts} separate pieces (>= 12), longest piece {longest:.1f} m (<= 140), "
                    f"vertex colour 'Col' on all: {okc}"))
    lava = bpy.data.objects.get("WATER_LAVA")
    if lava is not None and lava in meshes:
        me = lava.data
        me.calc_loop_triangles()
        nt = len(me.loop_triangles)
        lm = [_mat_name(m_) for m_ in me.materials]
        lights = [o.name for o in ex if o.name.startswith("LAVA_LIGHT_")]
        res.append(("LOOK_LAVA_MESH", nt >= 3000 and lm == ["LK_LAVA"] and 3 <= len(lights) <= 5,
                    f"WATER_LAVA {nt} tris (>= 3000), materials {lm}, {len(lights)} LAVA_LIGHT empties (3..5)"))
    return res


def fbx_check(path, expect_ground, expect_lk=True):
    """Re-import `path` into an EMPTY scene (destroys the open one) and measure: ground-prefix object set == expect_ground,
    every ground/water mesh carries LK_* materials and exactly one UV layer, WATER_SURF meshes carry a colour layer,
    no MAT_FOAM. Returns [(name, ok, detail)]."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    res = []
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    ground = sorted(o.name for o in meshes if o.name.startswith(GROUND_PREFIXES))
    res.append(("FBX_GROUND_SET", ground == sorted(expect_ground), f"ground meshes {len(ground)} == expected {len(expect_ground)}"
                + ("" if ground == sorted(expect_ground) else f"; got {ground} want {sorted(expect_ground)}")))
    bad_mat, bad_uv, lk_names = [], [], set()
    for o in meshes:
        names = [m_.name for m_ in o.data.materials if m_]
        lk_names |= {n for n in names if n.startswith("LK_")}
        if o.name.startswith(GROUND_PREFIXES + ("WATER_",)) and (not names or not all(n.startswith("LK_") for n in names)):
            bad_mat.append((o.name, names))
        if o.name.startswith(GROUND_PREFIXES + ("WATER_", "ROCK_SKIN", "DRESS_PATH")) and len(o.data.uv_layers) != 1:
            bad_uv.append((o.name, len(o.data.uv_layers)))
    res.append(("FBX_LK_MATERIALS", not bad_mat, f"LK materials in the file: {sorted(lk_names)}" + (f"; BAD {bad_mat[:4]}" if bad_mat else "")))
    res.append(("FBX_UV0", not bad_uv, f"every ground/water/skin/path mesh has exactly one UV layer" + (f"; BAD {bad_uv[:4]}" if bad_uv else "")))
    surfs = [o for o in meshes if o.name.startswith("WATER_SURF")]
    nocol = [o.name for o in surfs if len(o.data.color_attributes) == 0]
    amax = 0.0
    for o in surfs:
        if len(o.data.color_attributes):
            a = np.empty(len(o.data.color_attributes[0].data) * 4)
            o.data.color_attributes[0].data.foreach_get("color", a)
            amax = max(amax, float(a.reshape(-1, 4)[:, 3].max()))
    res.append(("FBX_SURF_COLOURS", (not surfs) or (not nocol and amax > 0.5),
                f"{len(surfs)} WATER_SURF meshes, all with a colour layer: {not nocol}, max alpha {amax:.2f}"))
    imgs = sorted(i.name for i in bpy.data.images)
    res.append(("FBX_NO_TEXTURE_REFS", not imgs, f"texture references in the FBX: {imgs[:6]} (Unity names materials by base "
                f"texture name with materialName 0, so the LK_* names only survive without them)"))
    foam = [m_.name for m_ in bpy.data.materials if m_.name.startswith("MAT_FOAM")]
    res.append(("FBX_NO_MAT_FOAM", not foam, f"MAT_FOAM materials in the file: {foam}"))
    return res
