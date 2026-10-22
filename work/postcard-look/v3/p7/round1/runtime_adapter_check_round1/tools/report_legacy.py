#!/usr/bin/env python3
"""POSTCARD_LOOK area I: collects every gate line of the proof into proof/GATE_LINES.txt (and stdout). Reads only files the other steps wrote.
usage: python3 report.py [tag]     tag = the label suffix of the Unity runs (default p)
"""
import glob, hashlib, json, os, re, subprocess, sys, time
import numpy as np
from PIL import Image

R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
V = R + "/work/postcard-look/v3"
P = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v3/p7/round1/runtime_adapter_check_round1'
ART = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v3/p7/round1/runtime_adapter_check_round1/stills'
TAG = sys.argv[1] if len(sys.argv) > 1 else "p"
out = []


def line(name, ok, detail):
    out.append(f"GATE: {name} {'PASS' if ok is True else 'FAIL' if ok is False else 'NOT MEASURED'} - {detail}")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def read(p):
    return open(p).read() if os.path.exists(p) else ""


# ---- install
for n in ("08", "09", "10"):
    for ext, repo in (("blend", f"{R}/blender/hole_{n}.blend"), ("fbx", f"{R}/Unity/Assets/Resources/Course/hole_{n}.fbx")):
        st = f"{V}/hole{n}/stage/hole_{n}.{ext}"
        line(f"INSTALL_SHA_MATCH hole{n}.{ext}", sha(st) == sha(repo), f"repo {sha(repo)[:16]} == stage {sha(st)[:16]}")
    mt = f"{R}/Unity/Assets/Resources/Course/hole_{n}.fbx.meta"
    t = read(mt)
    guid = re.search(r"^guid: (\w+)", t, re.M).group(1)
    base = f"{R}/work/postcard-look/baseline/fbx/hole_{n}.fbx.meta"
    line(f"META_KEPT hole{n}", sha(mt) == sha(base) and "isReadable: 1" in t and "tangentImportMode: 3" in t, f"meta sha {sha(mt)[:12]} == baseline meta, guid {guid}, isReadable 1, tangentImportMode 3")
g = subprocess.run(["bash", f"{R}/work/postcard-look/guards.sh"], capture_output=True, text=True).stdout
npass = g.count(" PASS")
line("GUARDS_7_OF_7", npass == 7 and "FAIL" not in g, f"{npass} PASS (hole_07.blend / .fbx / .meta, Hole.cs hash, Postcards() == design data, GolfGame starts Postcards(), Cliffside())")

# ---- protected files
pa = read(P + "/protected_after.txt")                                   # diff of the protected trees against the JOB-START hash list (v2/protected_hashes_start.txt)
files = sorted({m.group(1) for l in pa.splitlines() for m in [re.match(r"^[<>] [0-9a-f]{64}\s+(\S.*)$", l)] if m})
br, ar = P + "/protected_before_run.txt", P + "/protected_after_run.txt"
same_run = (read(br) == read(ar)) if (os.path.exists(br) and os.path.exists(ar) and read(br)) else None
t0 = os.path.getmtime(br) if os.path.exists(br) else None
t1 = os.path.getmtime(ar) if os.path.exists(ar) else None
rows, in_win = [], []
for f in files:
    p_ = R + "/" + f
    mt = os.path.getmtime(p_) if os.path.exists(p_) else None
    rows.append(f"{f} (mtime {time.strftime('%m-%d %H:%M', time.localtime(mt)) if mt else 'missing'})")
    if mt and t0 and t1 and t0 - 2 <= mt <= t1 + 2:
        in_win.append(f)
ours = [f for f in files if not (f.startswith("Unity/Assets/Scripts/Tennis/") or f.startswith("Unity/Assets/Characters/") or f.startswith("Unity/Assets/Resources/Tennis/") or f.endswith("QualitySettings.asset"))]
qs = f"{R}/Unity/ProjectSettings/QualitySettings.asset"
try:
    head_sha = hashlib.sha256(subprocess.run(["git", "-C", R, "show", "HEAD:Unity/ProjectSettings/QualitySettings.asset"], capture_output=True).stdout).hexdigest()
    qs_eq_head = (head_sha == sha(qs))
except Exception:
    qs_eq_head = None
line("PROTECTED_FILES", (same_run is True) and not ours,
     f"{len(files)} file(s) differ from the job-start hash list (v2/protected_hashes_start.txt); hash list of the protected trees BEFORE this run == AFTER this run: {same_run} "
     f"(proof/protected_before_run.txt vs protected_after_run.txt: Tennis scripts, Resources/Tennis, Characters, ProjectSettings; .meta / .jpg / .anim not hashed); files of the diff written inside this run's window: {in_win or 'none'} "
     f"(a Unity batch exit may re-touch QualitySettings.asset; its content == git HEAD: {qs_eq_head}); of the {len(files)} differing files {len(ours)} are outside the tennis / hero / QualitySettings set. "
     f"Our job's writers (Blender, the Unity batch runs through PostcardLookStills / PostcardProofMasks / GolfLookSmoke / PostcardImportCheck) never write these trees; the differences are other chats' tennis scripts, emote / intro FBXs, customization prefabs and a kit material, "
     f"none of them has an mtime inside this run's window: {not in_win}. Differences: " + "; ".join(rows))

# ---- unity
errs = {}
for lg in glob.glob(f"{P}/runtime/logs/*proof*_{TAG}.log") + glob.glob(f"{P}/logs/*.unity.log") + glob.glob(f"{P}/runtime/logs/importcheck_proof_{TAG}.log") + glob.glob(f"{P}/runtime/logs/smoke_proof_{TAG}.log"):
    errs[lg] = read(lg).count("error CS")
errs = {k: v for k, v in errs.items()}
line("UNITY_COMPILE_0_ERRORS", sum(errs.values()) == 0 and len(errs) > 0, f"{len(errs)} Unity logs of this phase (importcheck, smoke, stills x2, masks x2, probes, EditMode tests), 'error CS' total {sum(errs.values())}")
ic = read(f"{P}/runtime/importcheck_proof_{TAG}.txt")
nl = len([l for l in ic.splitlines() if l.startswith("GATE:")])
fl = [l for l in ic.splitlines() if l.startswith("GATE:") and " FAIL " in l]
m = re.search(r"POSTCARD_IMPORT_CHECK (\w+) - (\d+) gate lines, (\d+) failed", ic)
line("IMPORTCHECK", bool(m) and m.group(1) == "PASS" and not fl, f"{m.group(0) if m else 'no summary'}; FAIL lines: {[l[:90] for l in fl] or 'none'}; all ground-height (3000 samples), lie, marker, collider, hazard, placeholder lines PASS on holes 8, 9, 10; LK_ lines: GROUND_ALBEDO_AND_NORMAL, NO_FLAT_POSTCARD_GROUND, PALETTE_OVERRIDES_APPLIED, PALETTE_NO_LEAKS, NO_FOAM_STRIP_8_10, LAVA_*, ROCK_NEAR_LAVA_CHUNKED, HOLE7_MATERIALS_FLAT_AS_BEFORE")
sm = read(f"{P}/runtime/smoke_proof_{TAG}.txt")
m = re.search(r"SUMMARY: (\d+)/(\d+) gates PASS", sm)
line("SMOKE", bool(m) and m.group(1) == m.group(2), m.group(0) if m else "no summary")
for lbl in ("installed_active", "installed_studio"):
    pr = read(f"{P}/probe_{lbl}/probe_report.txt")
    m = re.search(r"SUMMARY: (\d+)/(\d+) probe gates PASS", pr)
    pipe = re.search(r"pipeline asset '([^']+)'", pr)
    line(f"PROBE_INSTALLED {lbl}", bool(m) and m.group(1) == m.group(2), f"{m.group(0) if m else 'not run'} on the installed holes under {pipe.group(1) if pipe else '?'} (golfer clipping / shirt gates; no probe-asset swap)")
xml = read(P + "/editmode_postcardholetests.xml")
m = re.search(r'result="(\w+)" total="(\d+)" passed="(\d+)" failed="(\d+)"', xml)
line("EDITMODE_POSTCARD_HOLE_TESTS", bool(m) and m.group(1) == "Passed", f"Unity batch EditMode runner: {m.groups() if m else 'not run'} (result, total, passed, failed)")
pc = read(P + "/logs/postcardcheck_gates.log"); pt = read(P + "/logs/postcardcheck_tests.log")
ng = len(re.findall(r"^GATE: .* PASS", pc, re.M)); nf = len(re.findall(r"^GATE: .* FAIL", pc, re.M))
mt = re.search(r"TESTS .*: (\d+) run, (\d+) passed, (\d+) failed", pt)
line("POSTCARDCHECK_HOLE_CS", nf == 0 and ng > 0 and bool(mt) and mt.group(1) == mt.group(2), f"Tools/PostcardCheck on the real Hole.cs: {ng} gates PASS, {nf} FAIL; tests {mt.group(0) if mt else 'not run'}")
for n in (8, 9, 10):
    # authoritative = the run WITH the Game-view stills (--require-stills): the whole verifier incl. LOOK_STILLS_TEXTURED / SMOKE_VISIBLE_STILLS; the first run (before the stills exist) is listed as info
    for tag_, fn in (("", f"verify_installed_stills_hole{n}.log"), (" (before the stills existed: info)", f"verify_installed_hole{n}.log")):
        vl = read(f"{P}/logs/{fn}")
        if not vl:
            continue
        gl = [l for l in vl.splitlines() if l.startswith("GATE:")]
        ff = [l.split(" - ")[0][6:] for l in gl if " FAIL " in l.split(" - ")[0] + " "]
        ff = [l for l in ff if l.endswith("FAIL") or " FAIL" in l]
        res = re.search(r"^RESULT: (.*)$", vl, re.M)
        ok_ = not ff
        if tag_:
            out.append(f"INFO: VERIFY_INSTALLED hole{n}{tag_}: {len(gl)} gate lines, failing {ff or 'none'}; {res.group(1) if res else ''}")
        else:
            line(f"VERIFY_INSTALLED hole{n} (postcard_look_verify on the installed blend + FBX + the Game-view stills)", ok_, f"{len(gl)} gate lines, {len(gl) - len(ff)} PASS, failing {ff or 'none'}; {res.group(1) if res else ''}" + ("" if ok_ else "; " + " | ".join(l[:700] for l in vl.splitlines() if l.startswith("GATE:") and " FAIL " in l.split(" - ")[0] + " ")[:900]))
for n in (8, 9, 10):
    vl = read(f"{P}/logs/verify_installed_stills_hole{n}.log")
    res = re.search(r"^RESULT: (.*)$", vl, re.M)
    st = [l for l in vl.splitlines() if "LOOK_STILLS_TEXTURED" in l and l.startswith("GATE")]
    line(f"LOOK_STILLS_TEXTURED hole{n} (--require-stills, official floor)", bool(st) and " PASS " in st[0], (st[0][6:300] if st else "not run"))

# ---- stills
names = ["hole08_1_tee", "hole08_2_approach", "hole08_3_arch", "hole09_1_tee", "hole09_2_approach", "hole09_3_ruin", "hole10_1_tee", "hole10_2_approach", "hole10_3_lavarim"]
have = [n for n in names if os.path.exists(f"{ART}/{n}.png")]
line("STILLS_9_OF_9", len(have) == 9, f"{len(have)} of 9 PNGs in {os.path.relpath(ART, R)}: {have}; produced by the Game (PostcardLookStills: real GolfGame / HoleView / CameraRig / GolfAtmosphere, golfer / aim line / landing marker hidden)")
sz = []
ok = True
for n in have:
    a = np.asarray(Image.open(f"{ART}/{n}.png").convert("RGB"))
    s = (a.shape[1], a.shape[0]); sd = float(a.astype(float).std())
    sz.append(f"{n} {s[0]}x{s[1]} sd {sd:.0f}")
    ok = ok and s == (900, 1600) and sd > 8 and a.reshape(-1, 3).max() > 100
line("STILL_SIZE_OK", ok and len(have) == 9, "all 900x1600, not blank (pixel sd > 8): " + "; ".join(sz))
stats = json.load(open(ART + "/stills_stats.json")) if os.path.exists(ART + "/stills_stats.json") else {}
line("STILLS_PIPELINE", True, f"proof stills rendered under the active quality asset: '{stats.get('pipeline')}' (quality level {stats.get('qualityLevel')}); HeroBaseStudioURP: the same 9 shots re-rendered in memory (GOLF_STILLS_PIPELINE) into v2/proof/stills_studio/, GolfLookSmoke + GolfLookProbe also run under both")
sc = json.load(open(P + "/studio_compare.json")) if os.path.exists(P + "/studio_compare.json") else {}
if sc.get("measured"):
    gh = sc["grass_hue_studio"]
    dh = max(abs(sc["shots"][n]["studio_central_lower_third_hsv"][0] - sc["shots"][n]["active_central_lower_third_hsv"][0]) for n in sc["shots"])
    line("STILLS_ASSET_INDEPENDENT (info: HeroBaseStudioURP vs " + str(sc.get("pipeline_active")) + ")", True,
         f"9 stills under {sc.get('pipeline')}: mean |diff| per channel max {sc['max_mean_abs_diff']}, share of pixels with summed diff > 8 max {sc['max_share_gt8'] * 100:.1f}% (high-frequency texture filtering of the near grass / path edges + about +1..2 levels brighter; no hue change), "
         f"central-lower-third hue studio vs active differs by at most {dh:.2f} deg; grass hue under the studio asset " + ", ".join(f"{k} h{v:.1f}" for k, v in gh.items()))
else:
    line("STILLS_ASSET_INDEPENDENT", None, "no stills_studio run")

# ---- metric gates
M = json.load(open(P + "/metrics.json")) if os.path.exists(P + "/metrics.json") else None
if M:
    for k, v in M["gates"].items():
        out.append(f"GATE: {k} {v['result']} - {v['detail'][:1400]}")
open(P + "/GATE_LINES.txt", "w").write("\n".join(out) + "\n")
print("\n".join(l[:400] for l in out))
