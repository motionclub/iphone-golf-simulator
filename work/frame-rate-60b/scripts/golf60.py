"""FRAME_RATE_60B: the golfer FBX (Resources/Hero/golfer_<m|f>.fbx) with every take keyed every 1/60 s.

A fork of work/swing-fix/scripts/splice_swings.py (same rig, clubs, solver set-up and export settings), run on the
SHIPPED golfer FBX:
  * Drive, IronSwing, HalfSwing, Chip: golf_swing.py's swings are continuous in time (Swing.pose(t) takes any t),
    so they are posed again at every half frame. At the whole frames they are the installed takes (--verify proves it).
  * Putt (its installed take predates the current golf_swing.py putt) and Idle, Wave, Cheer, FistPump (retargeted from
    the old V4 golfer, whose source is itself a 30 fps bake): their
    1/60 s in-betweens come from a monotone cubic through the installed keys (the keys themselves are kept).
  * Walk, RunForward, Emote_Scuba/Spike/Thrust, Intro_BringIt/Pushups/Wave: the golfer borrowed these from a stale
    Oct 4 branch (memory golf-emotes-stale-clips). They are copied again, frame for frame, from the CURRENT
    match-hero clips (rev 37 emotes from --emotes, Walk/RunForward from Characters/MatchHeroes), which are 60 Hz.
Writes <out>/golfer_<m|f>.fbx at 60 fps and <out>/golfer_<m|f>_clips.json (fps 60, frame landmarks doubled).

    Blender -b --factory-startup --python golf60.py -- --sex Male --in <golfer_m.fbx> --heroes <Characters/MatchHeroes>
        --emotes <dir with <Sex>_Emote_*.fbx, <Sex>_Intro_*.fbx> --out <dir> [--gs <dir with golf_swing.py>]
"""
import bpy, sys, os, math, json, importlib.util
from mathutils import Vector, Matrix, Quaternion

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d=None): return ARGV[ARGV.index(n) + 1] if n in ARGV else d
SEX = arg("--sex", "Male"); FEMALE = SEX == "Female"; TAG = "f" if FEMALE else "m"
IN = arg("--in"); OUT = arg("--out"); GS_DIR = arg("--gs")
VERIFY = "--verify" in ARGV; MEASURE = "--measure" in ARGV
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
HEROES = arg("--heroes", os.path.join(REPO, "Unity", "Assets", "Characters", "MatchHeroes")); EMOTES = arg("--emotes", HEROES)
GS_DIR = GS_DIR or os.path.join(REPO, "blender", "scripts")

ORDER = ["Drive", "IronSwing", "HalfSwing", "Chip", "Putt", "Idle", "Wave", "Cheer", "FistPump",
         "Walk", "RunForward", "Emote_Scuba", "Emote_Spike", "Emote_Thrust", "Intro_BringIt", "Intro_Pushups", "Intro_Wave"]
HELD = {"Drive": "Driver", "IronSwing": "Iron", "HalfSwing": "Iron", "Chip": "Wedge", "Putt": "Putter"}
AUTHORED_NAMES = ["Drive", "IronSwing", "HalfSwing", "Chip", "Putt"]
BORROWED = ["Walk", "RunForward", "Emote_Scuba", "Emote_Spike", "Emote_Thrust", "Intro_BringIt", "Intro_Pushups", "Intro_Wave"]
# Putt: the installed take predates golf_swing.py's current putt (re-posing it moves the head 22 mm), so it is upsampled like the V4 moves
UPSAMPLED = ["Putt", "Idle", "Wave", "Cheer", "FistPump"]
# (matchhero_golf.py's constants)
CLUB_LENGTH = {"Driver": 1.14, "Iron": 0.97, "Wedge": 0.92, "Putter": 0.86}
V4_CLUB_LENGTH = {"Driver": 1.156, "Iron": 1.018, "Wedge": 0.955, "Putter": 0.906}
SIDES = (("L", "Left"), ("R", "Right"))
FINGERS = ("Index", "Middle", "Ring", "Little")
GRIP = {"Index": (50, 70, 40), "Middle": (55, 75, 45), "Ring": (62, 80, 45), "Little": (68, 82, 45)}

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
bpy.ops.import_scene.fbx(filepath=IN)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
club_meshes = [o for o in meshes if o.name.startswith("CLUB_")]
bpy.context.view_layer.update()
def near_identity(M, tol=1e-5): return all(abs(M[i][j] - (1.0 if i == j else 0.0)) < tol for i in range(4) for j in range(4))
assert near_identity(rig.matrix_world), f"the armature is expected at the origin: {rig.matrix_world}"
assert near_identity(rig.data.bones["Club"].matrix_local), "the Club bone is expected to rest at the origin"

spec = importlib.util.spec_from_file_location("golf_swing", os.path.join(GS_DIR, "golf_swing.py"))
gs = importlib.util.module_from_spec(spec); spec.loader.exec_module(gs)
print("golf_swing from", os.path.join(GS_DIR, "golf_swing.py"))

def rest_head(n): return rig.data.bones[n].head_local.copy()
def rest_rot(n): return rig.data.bones[n].matrix_local.to_3x3()
LEN = {}
for s, side in SIDES:
    for key, (a, b, c) in ((f"arm{s}", (f"{side}UpperArm", f"{side}LowerArm", f"{side}Hand")), (f"leg{s}", (f"{side}UpperLeg", f"{side}LowerLeg", f"{side}Foot"))):
        LEN[key] = ((rest_head(b) - rest_head(a)).length, (rest_head(c) - rest_head(b)).length)
GEO = {}
for m in club_meshes:
    assert near_identity(m.matrix_world), m.name
    nm = m.name[5:].title()
    GEO[nm] = gs.ClubGeo(m, nm, CLUB_LENGTH[nm], V4_CLUB_LENGTH[nm])      # (the FBX's club meshes are already prepared: right-handed, sole flat at the lie)
GOLFER = gs.Golfer(gs.Rig({b.name: rest_head(b.name) for b in rig.data.bones}, {b.name: rest_rot(b.name) for b in rig.data.bones},
                          {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones}, LEN), FEMALE, GEO)
AUTHORED = {"Drive": lambda: gs.full_swing(GOLFER, "Driver", top=56, impact=69, finish=90, end=104),
            "IronSwing": lambda: gs.full_swing(GOLFER, "Iron"),
            "HalfSwing": lambda: gs.half_swing(GOLFER),
            "Chip": lambda: gs.chip(GOLFER),
            "Putt": lambda: gs.putt(GOLFER)}


def finger_pose(gamma):
    out = {}
    for s_, side_ in SIDES:
        fan = -gamma[s_] if s_ == "L" else gamma[s_]
        for fin in FINGERS:
            for i, part in enumerate(("Proximal", "Intermediate", "Distal")):
                q = Quaternion((1, 0, 0), math.radians(GRIP[fin][i]))
                if i == 0: q = Quaternion((0, 0, 1), fan) @ q
                out[f"{side_}{fin}{part}"] = q
    return out


def authored_clip(clip, sub=1, sw=None):
    """The swing posed `sub` times per authored (30 fps) frame: frame k + 1 is authored time k / sub."""
    sw = sw or AUTHORED[clip]()
    frames = []
    for k in range(sw.end * sub + 1):
        i = k / sub
        P, info = sw.pose(i)
        # the lead hand and lead shoulder in the chest's turning frame, from the mid-shoulder point, in units of his reach (the club keys' `hands` coordinates)
        Rch = GOLFER.heading(info["p"]); S = info["S"]
        kc = lambda w: GOLFER.to_rfu(Rch.inverted() @ (w - S)) / GOLFER.reach
        GL = info["origin"] + info["R"] @ Vector((0, 0, GOLFER.geos[sw.club].top - GOLFER.GRIP_LEAD))
        frames.append((k + 1, {"basis": P.basis, "club": info["M"], "heads": dict(P.heads), "head": info["head"], "R": info["R"], "fingers": finger_pose(info["gamma"]),
                              "keyhand": kc(GL), "keyshoulder": kc(P.child_head("LeftUpperArm", "LeftShoulder")), "p": info["p"],
                              "miss": info["miss"], "leg_miss": info["leg_miss"]}))
    misses = sorted(((max(r["miss"].values()), f) for f, r in frames), reverse=True)[:4]
    print(f"{clip} x{sub}: worst hand misses (cm @ frame): " + ", ".join(f"{m * 100:.2f}@{f - 1}" for m, f in misses))
    worst_arm = max(max(r["miss"].values()) for _f, r in frames); worst_leg = max(max(r["leg_miss"].values()) for _f, r in frames)
    print(f"{clip}: authored {len(frames)} frames, top {sw.top}, impact {sw.impact}, finish {sw.finish}; hands miss the grip by {worst_arm * 100:.2f} cm at most, a foot its ground by {worst_leg * 100:.2f} cm")
    return frames, sw


def write_action(name, frames_data, held=True):
    """(matchhero_golf.py write_action, unchanged in effect)"""
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
    rig.animation_data_create()
    act = bpy.data.actions.new(name)
    rig.animation_data.action = act
    slot = act.slots.new('OBJECT', rig.name) if not len(act.slots) else act.slots[0]
    rig.animation_data.action_slot = slot
    layer = act.layers.new("L") if not len(act.layers) else act.layers[0]
    strip = layer.strips.new(type='KEYFRAME') if not len(layer.strips) else layer.strips[0]
    cb = strip.channelbag(slot, ensure=True)
    n_f = len(frames_data)
    def curve(path, idx, values):
        fc = cb.fcurves.new(path, index=idx)
        fc.keyframe_points.add(n_f)
        co = []
        for (fr, _), v in zip(frames_data, values): co += [float(fr), float(v)]
        fc.keyframe_points.foreach_set('co', co)
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
        fc.update()
    def quats(getter):
        qs = [getter(rec) for _, rec in frames_data]
        for i in range(1, len(qs)):
            if qs[i].dot(qs[i - 1]) < 0: qs[i] = -qs[i]
        return qs
    bones = [b for b in rig.data.bones.keys() if b in frames_data[0][1]["basis"]]
    for n in bones:
        qs = quats(lambda rec: rec["basis"][n][0].to_quaternion())
        for k in range(4): curve(f'pose.bones["{n}"].rotation_quaternion', k, [q[k] for q in qs])
        if n in ("Root", "Hips"):
            for k in range(3): curve(f'pose.bones["{n}"].location', k, [rec["basis"][n][1][k] for _, rec in frames_data])
    for s, side in SIDES:
        for fin in FINGERS:
            for i, part in enumerate(("Proximal", "Intermediate", "Distal")):
                n = f"{side}{fin}{part}"
                if n not in rig.data.bones: continue
                qs_ = quats(lambda rec: rec["fingers"][n])
                for k in range(4): curve(f'pose.bones["{n}"].rotation_quaternion', k, [q_[k] for q_ in qs_])
    qs, ls, ss = [], [], []
    for fr, rec in frames_data:
        loc, rot, scl = rec["club"].decompose(); qs.append(rot); ls.append(loc); ss.append(scl)
    for i in range(1, len(qs)):
        if qs[i].dot(qs[i - 1]) < 0: qs[i] = -qs[i]
    for k in range(4): curve('pose.bones["Club"].rotation_quaternion', k, [q[k] for q in qs])
    for k in range(3): curve('pose.bones["Club"].location', k, [l[k] for l in ls])
    for k in range(3): curve('pose.bones["Club"].scale', k, [sc[k] for sc in ss])
    return act


def sample(act, frames, bones=None):
    """Every bone's armature-space head and tail, and the Club bone's matrix, at each frame of the action."""
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    out = []
    for f in frames:
        scn.frame_set(f)
        out.append({pb.name: (pb.head.copy(), pb.tail.copy()) for pb in rig.pose.bones if bones is None or pb.name in bones})
    return out


def action_of(clip):
    return bpy.data.actions.get(f"{rig.name}|{clip}") or bpy.data.actions.get(clip)


# ---------------------------------------------------------------- FRAME_RATE_60B
import numpy as np
FINGER_WORDS = ("Thumb", "Index", "Middle", "Ring", "Little")
TRACK = [n for n in ("LeftHand", "RightHand", "LeftFoot", "RightFoot", "LeftToes", "RightToes", "Head") if n in rig.data.bones]
CLUB_TIP = {m.name[5:].title(): min((v.co for v in m.data.vertices), key=lambda v: v.z).copy() for m in club_meshes}
REPORT = {"sex": SEX, "clips": {}}


def use(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]


def at(f):
    fi = int(math.floor(f + 1e-9)); scn.frame_set(fi, subframe=max(0.0, f - fi))


def points(act, frames, club):
    """Hands, feet, toes, head (bone heads) and the club head, armature space, at each (possibly fractional) frame."""
    use(act); out = []
    tip = CLUB_TIP.get(club, CLUB_TIP.get("Driver"))
    for f in frames:
        at(f)
        d = {n: rig.pose.bones[n].head.copy() for n in TRACK}
        d["ClubHead"] = rig.pose.bones["Club"].matrix @ rig.data.bones["Club"].matrix_local.inverted() @ tip
        out.append(d)
    return out


def worst(a, b, keys=None):
    w = (0.0, "", -1)
    for i, (x, y) in enumerate(zip(a, b)):
        for n in (keys or x.keys()):
            d = (x[n] - y[n]).length
            if d > w[0]: w = (d, n, i)
    return w


def basis_at(src_rig, frames, skip_fingers=False):
    """{bone: (quaternion, location, scale)} of every bone of `src_rig` that this rig has, per frame (pose basis)."""
    out = []
    for f in frames:
        at(f)
        d = {}
        for pb in src_rig.pose.bones:
            if pb.name not in rig.data.bones or (skip_fingers and any(w in pb.name for w in FINGER_WORDS)): continue
            loc, rot, scl = pb.matrix_basis.decompose(); d[pb.name] = (rot, loc, scl)
        out.append(d)
    return out


def pchip_cols(t, V, x):
    """Monotone cubic (Fritsch-Carlson, golf_swing.Curve) through the rows of V at times t, evaluated at x; column-wise."""
    n = len(t); h = np.diff(t); d = np.diff(V, axis=0) / h[:, None]; m = np.zeros_like(V)
    for i in range(1, n - 1):
        a, b = d[i - 1], d[i]; w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
        ok = a * b > 0
        m[i] = np.where(ok, (w1 + w2) / np.where(ok, w1 / np.where(ok, a, 1) + w2 / np.where(ok, b, 1), 1), 0.0)
    def end(h0, h1, d0, d1):
        e = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
        e = np.where(e * d0 <= 0, 0.0, e)
        return np.where((d0 * d1 <= 0) & (np.abs(e) > 3 * np.abs(d0)), 3 * d0, e)
    if n > 2: m[0] = end(h[0], h[1], d[0], d[1]); m[-1] = end(h[-1], h[-2], d[-1], d[-2])
    else: m[0] = m[-1] = d[0]
    k = np.clip(np.searchsorted(t, x, side='right') - 1, 0, n - 2); hh = (t[k + 1] - t[k])[:, None]; s = ((x - t[k]) / (t[k + 1] - t[k]))[:, None]
    return ((2 * s**3 - 3 * s**2 + 1) * V[k] + (s**3 - 2 * s**2 + s) * hh * m[k] + (-2 * s**3 + 3 * s**2) * V[k + 1] + (s**3 - s**2) * hh * m[k + 1])


def upsample(samples):
    """30 fps pose samples -> 60 fps: every 30 fps sample kept, the in-betweens on a monotone cubic (quaternions sign-aligned, renormalised)."""
    n = len(samples); t = np.arange(n, dtype=float); x = np.arange(2 * n - 1) / 2.0
    out = [dict() for _ in x]
    for b in samples[0]:
        Q = np.array([list(s[b][0]) for s in samples]); L = np.array([list(s[b][1]) for s in samples]); S = np.array([list(s[b][2]) for s in samples])
        for i in range(1, n):
            if np.dot(Q[i], Q[i - 1]) < 0: Q[i] = -Q[i]
        Qx, Lx, Sx = pchip_cols(t, Q, x), pchip_cols(t, L, x), pchip_cols(t, S, x)
        Qx[::2], Lx[::2], Sx[::2] = Q, L, S
        for k in range(len(x)):
            q = Quaternion(Qx[k]); q.normalize(); out[k][b] = (q, Vector(Lx[k]), Vector(Sx[k]))
    return [(k + 1, rec) for k, rec in enumerate(out)]


def write_generic(name, frames_data):
    """Keys rotation (quaternion), location and scale of every bone in the records, linear, at the records' frames."""
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
    rig.animation_data_create()
    act = bpy.data.actions.new(name); rig.animation_data.action = act
    slot = act.slots.new('OBJECT', rig.name); rig.animation_data.action_slot = slot
    cb = act.layers.new("L").strips.new(type='KEYFRAME').channelbag(slot, ensure=True)
    fr = [float(f) for f, _ in frames_data]
    def curve(path, idx, values):
        fc = cb.fcurves.new(path, index=idx); fc.keyframe_points.add(len(fr))
        co = []
        for f, v in zip(fr, values): co += [f, float(v)]
        fc.keyframe_points.foreach_set('co', co)
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
        fc.update()
    for b in frames_data[0][1]:
        qs = [rec[b][0] for _, rec in frames_data]
        for i in range(1, len(qs)):
            if qs[i].dot(qs[i - 1]) < 0: qs[i] = -qs[i]
        for k in range(4): curve(f'pose.bones["{b}"].rotation_quaternion', k, [q[k] for q in qs])
        for k in range(3): curve(f'pose.bones["{b}"].location', k, [rec[b][1][k] for _, rec in frames_data])
        for k in range(3): curve(f'pose.bones["{b}"].scale', k, [rec[b][2][k] for _, rec in frames_data])
    return act


def borrowed60(clip):
    """The current match-hero take, every one of its frames (a 60 fps file), as pose-basis records on this rig (fingers left at rest, as before)."""
    path = os.path.join(EMOTES, SEX, f"{SEX}_{clip}.fbx") if clip.startswith(("Emote_", "Intro_")) else os.path.join(HEROES, SEX, f"{SEX}_{clip}.fbx")
    if not os.path.exists(path): path = os.path.join(EMOTES, f"{SEX}_{clip}.fbx")
    before_o, before_a = set(bpy.data.objects), set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=path)
    fps = scn.render.fps / scn.render.fps_base
    assert abs(fps - 60) < 1e-6, f"{path} is a {fps} fps file"
    src = next(o for o in bpy.data.objects if o not in before_o and o.type == 'ARMATURE')
    act = src.animation_data.action; f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    recs = basis_at(src, range(f0, f1 + 1), skip_fingers=True)
    # the source's own points, to prove the copy (same bone names, same rest)
    pts = []
    for f in range(f0, f1 + 1):
        at(f); pts.append({n: (src.matrix_world @ src.pose.bones[n].head) for n in TRACK})
    for o in list(bpy.data.objects):
        if o not in before_o: bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions):
        if a not in before_a: bpy.data.actions.remove(a)
    print(f"{clip}: {len(recs)} frames at 60 fps from {os.path.relpath(path, REPO)}")
    return [(k + 1, r) for k, r in enumerate(recs)], pts, path


old_acts = {c: action_of(c) for c in ORDER}
for c, a in old_acts.items(): assert a is not None, c
old_range = {c: (int(round(a.frame_range[0])), int(round(a.frame_range[1]))) for c, a in old_acts.items()}
new_acts, swings = {}, {}
for clip in ORDER:
    f0, f1 = old_range[clip]; n_old = f1 - f0 + 1
    club = HELD.get(clip, "Driver")
    shared_old = list(range(f0, f1 + 1))
    if clip in AUTHORED and clip not in UPSAMPLED:
        sw = AUTHORED[clip]()
        f30, _ = authored_clip(clip, 1, sw)
        a30 = write_action("__v30_" + clip, f30)
        dv = worst(points(old_acts[clip], shared_old, club), points(a30, [f for f, _ in f30], club))
        bpy.data.actions.remove(a30)
        frames, _ = authored_clip(clip, 2, sw); swings[clip] = (frames, sw)
        act = write_action("__new_" + clip, frames)
        kind = "authored (golf_swing.py posed every 1/60 s)"
        extra = {"verify_30fps_vs_installed_mm": round(dv[0] * 1000, 3), "verify_worst": dv[1]}
    elif clip in UPSAMPLED:
        use(old_acts[clip]); recs = basis_at(rig, shared_old)
        act = write_generic("__new_" + clip, upsample(recs)); kind = "monotone cubic through the installed 30 fps keys"; extra = {}
    else:
        frames, src_pts, path = borrowed60(clip)
        act = write_generic("__new_" + clip, frames)
        mine = points(act, [f for f, _ in frames], club)
        dsrc = worst([{n: rig.matrix_world @ p[n] for n in TRACK} for p in mine], src_pts, TRACK)
        kind = "copied from the current 60 Hz match-hero take"
        extra = {"source": os.path.relpath(path, REPO), "vs_source_all_frames_mm": round(dsrc[0] * 1000, 3), "old_frames_30fps": n_old, "new_frames_60fps": len(frames)}
    new_acts[clip] = act
    nr = (int(round(act.frame_range[0])), int(round(act.frame_range[1])))
    entry = {"kind": kind, "frames_30": n_old, "frames_60": nr[1] - nr[0] + 1, **extra}
    if clip not in BORROWED:
        # shared frames: old frame f0 + i is new frame 1 + 2i (the same time); in-betweens: new vs the old straight line
        assert entry["frames_60"] == 2 * n_old - 1, (clip, entry)
        a = points(old_acts[clip], shared_old, club); b = points(act, [1 + 2 * i for i in range(n_old)], club)
        w = worst(a, b); entry["shared_frames_max_mm"] = round(w[0] * 1000, 3); entry["shared_worst"] = f"{w[1]} @ old frame {f0 + w[2]}"
        mid_old = points(old_acts[clip], [f0 + i + .5 for i in range(n_old - 1)], club); mid_new = points(act, [2 + 2 * i for i in range(n_old - 1)], club)
        w = worst(mid_old, mid_new); entry["inbetween_vs_old_straight_line_max_mm"] = round(w[0] * 1000, 2); entry["inbetween_worst"] = f"{w[1]} @ old frame {f0 + w[2]}.5"
    REPORT["clips"][clip] = entry
    print("CLIP60", SEX, clip, json.dumps(entry))

if OUT:
    os.makedirs(OUT, exist_ok=True)
    for clip in ORDER:
        bpy.data.actions.remove(old_acts[clip]); new_acts[clip].name = clip
    rig.animation_data.action = None
    for t in list(rig.animation_data.nla_tracks): rig.animation_data.nla_tracks.remove(t)
    track = rig.animation_data.nla_tracks.new()
    start = 1
    for clip in ORDER:
        act = new_acts[clip]
        strip = track.strips.new(clip, start, act)
        try: strip.action_slot = act.slots[0]
        except Exception: pass
        start = int(strip.frame_end) + 10
    rig.data.pose_position = 'POSE'
    scn.render.fps = 60; scn.render.fps_base = 1.0
    sel = [rig] + meshes
    for o in scn.objects: o.select_set(False)
    for o in sel: o.select_set(True)
    bpy.context.view_layer.objects.active = rig
    path = os.path.join(OUT, f"golfer_{TAG}.fbx")
    with bpy.context.temp_override(selected_objects=sel, active_object=rig, object=rig):
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'ARMATURE', 'MESH'},
                                 apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', global_scale=1.0,
                                 axis_forward='-Z', axis_up='Y', bake_space_transform=False,
                                 use_mesh_modifiers=True, mesh_smooth_type='OFF', add_leaf_bones=False,
                                 use_armature_deform_only=True, armature_nodetype='NULL',
                                 bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True,
                                 bake_anim_use_all_actions=False, bake_anim_force_startend_keying=True,
                                 bake_anim_step=1.0, bake_anim_simplify_factor=0.0, path_mode='STRIP', embed_textures=False)
    print("exported", path)
    src_json = os.path.join(os.path.dirname(IN), f"golfer_{TAG}_clips.json")
    js = json.load(open(src_json))
    for c in js["clips"]:
        assert c["fps"] == 30, c
        c["fps"] = 60; c["frames"] = 2 * c["frames"] - 1; c["top"] *= 2; c["impact"] *= 2
        if c["name"] in swings:
            frames, sw = swings[c["name"]]
            m = next(o for o in club_meshes if o.name == "CLUB_" + HELD[c["name"]].upper())
            head_local = min((v.co for v in m.data.vertices), key=lambda v: v.z).copy()
            path_ = [rec["club"] @ head_local for _, rec in frames]
            assert c["frames"] == len(frames) and c["top"] == 2 * sw.top, (c, len(frames), sw.top)
            c["headAddress"] = list(path_[0]); c["headImpact"] = list(path_[min(c["impact"], len(path_) - 1)])
    json.dump(js, open(os.path.join(OUT, f"golfer_{TAG}_clips.json"), "w"), indent=2)
    json.dump(REPORT, open(os.path.join(OUT, f"golf60_report_{TAG}.json"), "w"), indent=1)
    print("clips json + report written")
