"""Clone-only: lets HeroTurnaround pose a hero on any tennis clip at any time, and optionally hide the body.
usage: python3 patch_turnaround.py <clone>/Unity
env at capture time: TURNAROUND_CLIP=Forehand  TURNAROUND_T=0.95  TURNAROUND_HIDE=body|top_inner|none
Writes the patched file in place (the clone only; never the shared project)."""
import sys, pathlib

p = pathlib.Path(sys.argv[1]) / "Assets/Editor/HeroTurnaround.cs"
s = p.read_text()
if "TURNAROUND_CLIP" in s:
    print("already patched"); sys.exit(0)
reps = [
    ("            else ready = driver.slots.First(s => s.id == HeroTennisDriver.Clip.Ready).clip;",
     "            else { var want = Enum.TryParse<HeroTennisDriver.Clip>(Environment.GetEnvironmentVariable(\"TURNAROUND_CLIP\") ?? \"Ready\", out var pc) ? pc : HeroTennisDriver.Clip.Ready;\n"
     "                   ready = driver.slots.First(s => s.id == want).clip; }"),
    ("            ready.SampleAnimation(root, 0);\n            if (ironSocket.HasValue)",
     "            ready.SampleAnimation(root, float.TryParse(Environment.GetEnvironmentVariable(\"TURNAROUND_T\"), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var pt) ? pt : 0f);\n            if (ironSocket.HasValue)"),
    ("                if (r.name.StartsWith(\"Collider\")) continue;",
     "                if (r.name.StartsWith(\"Collider\")) continue;\n"
     "                if (Environment.GetEnvironmentVariable(\"TURNAROUND_HIDE\") == \"body\" && r == look.body) continue;"),
]
for a, b in reps:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
p.write_text(s)
print("patched", p)
