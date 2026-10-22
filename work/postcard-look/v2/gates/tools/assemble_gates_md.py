"""Assemble work/postcard-look/GATES.md: keep everything above the marker, append v2/gates/GATES_v2_section.md + an Evidence block built from
the self-test log and the run JSONs. Idempotent (replaces from the marker)."""
import os, re, json, glob, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.abspath(os.path.join(HERE, ".."))
JOB = os.path.abspath(os.path.join(G, "..", ".."))
md = os.path.join(JOB, "GATES.md")
src = open(md).read()
mark = "\n---\n\n# v2 2026-10-04"
i = src.find(mark)
head = src if i < 0 else src[:i]
head = head.rstrip("\n") + "\n"
sec = open(os.path.join(G, "GATES_v2_section.md")).read()
log = open(os.path.join(G, "runs", "selftest_all_fbx_r3.log"), errors="ignore").read().splitlines()
gl = [l for l in log if l.startswith("SELFTEST_GATE ")]
tot = [l for l in log if l.startswith("SELFTEST: ") and re.search(r"\d+ lines", l)]
nm = [l for l in log if l.startswith("SELFTEST: hole") and ("mutation" in l or "control" in l)]
ev = ["", "## Evidence (2026-10-04)", ""]
ev.append("Files: `v2/gates/runs/*.json|log` (verify runs), `v2/gates/runs/selftest_all_fbx_r3.log` (self-test of the round-3 verifier; the round-2 self-test log is `runs/selftest_all_fbx.log`), `v2/gates/fixtures/` (old failing textures, lib smoke builds "
          "of 2026-10-03 22:00 and 2026-10-04 10:44, the Look snapshot the runs used + sha256), `v2/gates/tools/run_evidence.sh` (re-creates it all), "
          "`v2/gates/st/` (the synthetic positives), `v2/gates/postcard_look_verify.py.at_start` / `.before_review_fix` / `.before_review2_fix` (the file before this pass / before the first / before the second review fix), `runs_prev_r2/` (the verify runs of the round-2 verifier), `review3/` (the skeptic's mutants replayed against the round-3 verifier), `r3/` (round-3 working logs), `v2/gates/calib/still_calib.txt` (stills vs the window statistic), `v2/gates/tools/*` (probes, run_gate.py, skeptic_mut.py).")
ev.append("")
import hashlib
vsha = hashlib.sha256(open(os.path.join(JOB, "..", "..", "blender", "scripts", "postcard_look_verify.py"), "rb").read()).hexdigest()
ev.append(f"Verifier `blender/scripts/postcard_look_verify.py` sha256 `{vsha}` ({len(open(os.path.join(JOB, '..', '..', 'blender', 'scripts', 'postcard_look_verify.py')).read().splitlines())} lines) = the file the self-test below ran against (`runs/verify_sha_for_selftest_r3.txt`).")
ev.append("")
ev.append("**Self-test** (`--selftest --selftest-fbx`, all holes): " + (tot[-1] if tot else "n/a"))
ev.append("")
ev.append("(An earlier run of the same verifier minus two edits - `runs/selftest_all_fbx_r3_first_run.log`, 434 lines - ended with ONE expectation not met: the hole-9 control `ctl_terrain_wall_polygon_poked_same_surface` raised "
          "'no isolated non-up-facing TERRAIN polygon' because hole 9's smallest wall-polygon non-planarity is 1.5e-5 m, over the control's own 1e-5 m flatness filter. The filter became 2e-4 m (far under the gate's 1 mm) and the "
          "LOOK_FILES window floor became the named constant `TH2['win_sd']` (same value 0.03); no gate verdict changed. The run below is the full self-test of the final file.)")
ev.append("")
ev.append("```")
ev += gl
ev.append("```")
ev.append("")
tab = subprocess.run([sys.executable, os.path.join(HERE, "summarize_mut.py"), os.path.join(G, "runs", "selftest_all_fbx_r3.log")], capture_output=True, text=True).stdout.strip()
ev.append("**Per-gate mutation table of EVERY gate** (all holes, both stages; MUT_FAILS_ON_BAD = mutants that must fail the gate and do; MUT_PASSES_ON_GOOD = positives + controls that pass it; the first table's V2 rows are the tool's own SELFTEST_GATE counts):")
ev.append("")
ev.append("```")
ev.append(tab)
ev.append("```")
ev.append("")
rv = subprocess.run([sys.executable, os.path.join(HERE, "summarize_review3.py")], capture_output=True, text=True).stdout.strip()
if rv:
    ev.append("**The skeptic's own mutants replayed against this verifier** (`v2/gates/review3/mut2.py`, `mut3.py` = pointed copies of the reviewer's `review_V` harness, FBX stage included; positives = `review_V/st2`):")
    ev.append("```")
    ev.append(rv)
    ev.append("```")
    ev.append("")
ex = []
for h in ("8", "9"):
    pth = os.path.join(G, "runs", f"extra_attacks_h{h}.log")
    if os.path.isfile(pth):
        ex += [l[:230] for l in open(pth, errors="ignore").read().splitlines() if l.startswith("MUT ")]
if ex:
    ev.append("**The builder's own extra attacks** (`v2/gates/review3/extra_attacks.py`, FBX stage included): continuous white curtains / ramps 6, 9, 11 m offshore and underwater, a white skirt named FLAG, welded icosahedra sharing a FACE, icosahedra with poked faces. "
              "The poked-face bundle with only 14 pokes over 7 cells fails (4-7 of 11 rock meshes still regular); one with >= 2 pokes in every cell is the disclosed residual (Known gaps):")
    ev.append("```")
    ev += ex
    ev.append("```")
    ev.append("")
props = []
for h in ("08", "10"):
    pth = os.path.join(G, "runs", f"props_lib_{h}.log")
    if os.path.isfile(pth):
        props += [l[:260] for l in open(pth, errors="ignore").read().splitlines() if l.startswith("RG ")]
if props:
    ev.append("**The real props library** (props-only test FBXs of the props agent; `run_gate.py`):")
    ev.append("```")
    ev += props
    ev.append("```")
    ev.append("")
for pat, title in (("baseline_*.json", "Baseline holes 8-10 (= the files in the repo today; Look = snapshot 2026-10-04 10:45)"),
                   ("libsmoke_old_*.json", "A3 lib smoke builds of 2026-10-03 (pre-repair; Look = the old failing textures)"),
                   ("libsmoke_now_*.json", "A3 lib smoke builds of 2026-10-04 10:44 (`lib_ground/smoke_holeNN`, work in progress of the ground agent; Look snapshot)"),
                   ("livelook_*.json", "the same lib smoke holes against the LIVE `Unity/.../Look` folder at the time of the run (the tex agent keeps writing it)")):
    out = subprocess.run([sys.executable, os.path.join(HERE, "summarize_runs.py"), pat], capture_output=True, text=True).stdout.strip()
    ev.append(f"**{title}**")
    ev.append("```")
    ev.append(out)
    ev.append("```")
    ev.append("")
open(md, "w").write(head + sec.rstrip("\n") + "\n" + "\n".join(ev) + "\n")
print("GATES.md rewritten:", len(open(md).read().splitlines()), "lines;", len(gl), "SELFTEST_GATE lines;", len(nm), "mutation/control lines")
