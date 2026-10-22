#!/usr/bin/env python3
"""make_orig.py <original Unity dir> <clone Unity dir> — for the off-path proof (TOGGLE_RESTORES).

Copies the ORIGINAL (unpatched) version of every world shader the weather patch touches, and every shader that includes
EnvironmentSurface.hlsl, into <clone>/Assets/MWOrig/ under the name "<Shader name>__orig". Relative includes are rewritten
to absolute Assets/ paths; EnvironmentSurface.hlsl points at an unpatched copy in MWOrig. The proof harness swaps materials
between each patched shader and its __orig twin inside one frozen frame (no asset reimport, no second run)."""
import os, re, sys

src, clone = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
assets = os.path.join(src, "Assets")
out = os.path.join(clone, "Assets", "MWOrig")
os.makedirs(out, exist_ok=True)
SURF = "Resources/Environment/Shaders/EnvironmentSurface.hlsl"
DIRECT = ["Resources/Course/Shaders/GolfRock.shader", "Resources/Course/Shaders/GolfBotanical.shader",
          "Resources/Course/Shaders/GolfOcean.shader", "Resources/Environment/LuminousCoast/CoastalPine.shader"]

shaders = set(DIRECT)
for root, _, files in os.walk(os.path.join(assets, "Resources")):
    for f in files:
        if f.endswith(".shader"):
            p = os.path.join(root, f)
            if "EnvironmentSurface.hlsl" in open(p, encoding="utf-8", errors="ignore").read():
                shaders.add(os.path.relpath(p, assets))

inc = re.compile(r'#include(_with_pragmas)?\s+"([^"]+)"')

def absolutize(text, rel_dir):
    def fix(m):
        path = m.group(2)
        if path.startswith("Packages/") or path.startswith("Assets/"):
            return m.group(0)
        full = os.path.normpath(os.path.join("Assets", rel_dir, path)).replace(os.sep, "/")
        if full.endswith("EnvironmentSurface.hlsl"):
            full = "Assets/MWOrig/EnvironmentSurface.hlsl"
        return f'#include{m.group(1) or ""} "{full}"'
    return inc.sub(fix, text)

# the unpatched surface include (its own includes are package paths only)
open(os.path.join(out, "EnvironmentSurface.hlsl"), "w", encoding="utf-8").write(open(os.path.join(assets, SURF), encoding="utf-8").read())
names = []
for rel in sorted(shaders):
    text = open(os.path.join(assets, rel), encoding="utf-8").read()
    m = re.search(r'Shader\s+"([^"]+)"', text)
    if not m:
        continue
    names.append(m.group(1))
    text = text[:m.start()] + f'Shader "{m.group(1)}__orig"' + text[m.end():]
    text = absolutize(text, os.path.dirname(rel))
    open(os.path.join(out, os.path.basename(rel).replace(".shader", "__orig.shader")), "w", encoding="utf-8").write(text)
open(os.path.join(out, "twins.txt"), "w").write("\n".join(names) + "\n")
print(f"{len(names)} __orig twins in {out}")

# control set: the PATCHED source (the clone's own files) under "<name>__pat", so the proof can compare twin against twin
# (both go through the same material swap, which changes draw order and coplanar z-fight edges by itself)
cassets = os.path.join(clone, "Assets"); pout = os.path.join(cassets, "MWPat"); os.makedirs(pout, exist_ok=True)
pn = 0
for rel in sorted(shaders):
    text = open(os.path.join(cassets, rel), encoding="utf-8").read()
    m = re.search(r'Shader\s+"([^"]+)"', text)
    if not m:
        continue
    text = text[:m.start()] + f'Shader "{m.group(1)}__pat"' + text[m.end():]
    def fixp(mm):
        path = mm.group(2)
        if path.startswith("Packages/") or path.startswith("Assets/"):
            return mm.group(0)
        full = os.path.normpath(os.path.join("Assets", os.path.dirname(rel), path)).replace(os.sep, "/")
        return f'#include{mm.group(1) or ""} "{full}"'
    text = inc.sub(fixp, text)
    open(os.path.join(pout, os.path.basename(rel).replace(".shader", "__pat.shader")), "w", encoding="utf-8").write(text); pn += 1
print(f"{pn} __pat control twins in {pout}")
