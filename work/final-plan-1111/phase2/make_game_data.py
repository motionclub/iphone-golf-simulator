"""make_game_data.py [out dir]: the studio result as the files the game loads (Unity/Assets/Scripts/Tennis/HeroStudio.cs):
Resources/HeroStudio/<renderer name>_<vertex count>.bytes = per-vertex offsets (rest pose, hero frame) for his body and every
garment that moved in the tennis, golf and bowling kits, and for her three tops. Run from work/final-plan-1111/phase2."""
import sys, os, numpy as np, armio, posed, fit, herfit
out = sys.argv[1] if len(sys.argv) > 1 else "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/HeroStudio"
os.makedirs(out, exist_ok=True)
UNIT = 50000.0
def write(name, old, new, tag):
    """HSD1, int32 count, int16 x,y,z per vertex in 1/50000 m: the OFFSET the game adds (HeroStudio.cs)."""
    d = np.rint((new - old) * UNIT); assert np.abs(d).max() < 32767, name
    f = os.path.join(out, f"{name}_{len(new)}.bytes")
    with open(f, "wb") as o: o.write(b"HSD1"); o.write(np.int32(len(new)).tobytes()); o.write(d.astype('<i2').tobytes())
    print(f"{tag:22} {name:12} {len(new):6d} vertices, largest move {np.linalg.norm(new - old, axis=1).max()*100:5.2f} cm -> {os.path.basename(f)} ({os.path.getsize(f)//1024} KB)")
total = 0
for tag in ("male_build0", "male_golfkit_base", "male_bowlingkit_base"):
    parts = {n[:-4]: armio.read(f"export/{tag}/{n}") for n in sorted(os.listdir(f"export/{tag}")) if n.endswith(".bin")}
    new = fit.dress(parts, posed.B, posed.mL, posed.mR, fit=True, under=("Kit_Bottom", "Kit_Belt"))
    for n, m in new.items():
        if np.linalg.norm(m['pos'] - parts[n]['pos'], axis=1).max() < 1e-5: continue
        write("Body_M" if n == "Body" else n, parts[n]['pos'], m['pos'], tag)     # (HeroStudio asks for every hero's body as Body_M; the golfer's renderer is named Body)
# her: the body is untouched; only her refitted tops
for tag in ("female_tennis", "female_golfkit", "female_bowlingkit"):
    parts, new = herfit.fitted(tag); write("Kit_Top", parts["Kit_Top"]['pos'], new["Kit_Top"]['pos'], tag)
print("total", sum(os.path.getsize(os.path.join(out, f)) for f in os.listdir(out) if f.endswith(".bytes")) // 1024, "KB in", out)
