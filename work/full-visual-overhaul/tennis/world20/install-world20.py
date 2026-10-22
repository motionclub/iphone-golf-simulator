from pathlib import Path
import hashlib
import json

stage = Path(__file__).parent
repo = stage.parents[3]
changes = []


def replace(relative, before, after):
    target = repo / relative
    text = target.read_text()
    if after in text:
        return
    if text.count(before) != 1:
        raise ValueError(f"Expected exactly one bounded patch in {relative}")
    target.write_text(text.replace(before, after))
    changes.append(relative)


relative = "Unity/Assets/Resources/Tennis/Shaders/TennisWorldSurface.shader"
live = (repo / relative).read_text()
staged = (stage / relative).read_text()
if "                if (_CourtFinish > .5)" in live:
    start = live.index("                if (_CourtFinish > .5)")
    end = live.index("                input.viewDirectionWS", start)
    new_start = staged.index("                // The old 4cm procedural normal ripples")
    new_end = staged.index("                input.viewDirectionWS", new_start)
    replace(relative, live[start:end], staged[new_start:new_end])
elif "// The old 4cm procedural normal ripples" not in live:
    raise ValueError("Expected World20 court block or the original CourtFinish normal block")

relative = "Unity/Assets/Scripts/Tennis/TennisLook.cs"
replace(relative, 'result.SetFloat("_MicroStrength",.19f);result.SetFloat("_MicroScale",1)',
        'result.SetFloat("_MicroStrength",.07f);result.SetFloat("_MicroScale",2)')
replace(relative, 'result.SetFloat("_MicroStrength",.16f);result.SetFloat("_MicroScale",1)',
        'result.SetFloat("_MicroStrength",.06f);result.SetFloat("_MicroScale",2)')

relative = "Unity/Assets/Resources/Tennis/Shaders/TennisCoastalSky.shader"
replace(relative, 'half cloud=smoothstep(.16,.65,min(sky.r,sky.g));',
        'half cloud=smoothstep(.05,.33,min(sky.r,sky.g));')
replace(relative, 'half3 clear=lerp(half3(.34,.56,.76),half3(.085,.30,.58),pow(saturate(d.y),.42));',
        'half3 clear=lerp(half3(.40,.64,.82),half3(.10,.37,.65),pow(saturate(d.y),.42));')

relative = "Unity/Assets/Resources/Tennis/Shaders/TennisLava.shader"
replace(relative, 'half3 channel=lerp(_Flow.rgb*.65h,_Hot.rgb,saturate(.22h+heat*.58h+temperature*.20h));',
        'half3 channel=lerp(_Flow.rgb*.65h,_Hot.rgb,saturate(.34h+temperature*.43h));')

relative = "Unity/Assets/Editor/TennisVenueCapture.cs"
before = '            yield return Shot("9_hero_postcard", new Vector3(2.6f,2.2f,-17.2f), new Vector3(0,.85f,3.5f),52);\n'
after = before + '            if(System.Environment.GetEnvironmentVariable("HERO_VENUE_REFERENCE")=="1")\n                yield return Shot("14_reference_camera",new Vector3(2,1.80f,-15.3f),new Vector3(0,1,7),54);\n'
replace(relative, before, after)

files = []
installed = ["Unity/Assets/Resources/Tennis/Shaders/TennisWorldSurface.shader",
             "Unity/Assets/Scripts/Tennis/TennisLook.cs",
             "Unity/Assets/Resources/Tennis/Shaders/TennisCoastalSky.shader",
             "Unity/Assets/Resources/Tennis/Shaders/TennisLava.shader",
             "Unity/Assets/Editor/TennisVenueCapture.cs"]
for relative in installed:
    target = repo / relative
    files.append({"path": relative, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                  "bytes": target.stat().st_size})
manifest = {"checkpoint": "World20 fine acrylic / coastal cloud / cooling channel candidate",
            "status": "installed; actual Unity comparison pending",
            "invariants": ["court/net/collision geometry untouched", "gameplay contact/toss/actor transforms untouched",
                           "quality/cascades/shadow distance untouched", "world and foliage density untouched",
                           "closer reference camera is capture-only"], "files": files}
proof = repo / "proof/full-visual-overhaul/tennis/world20-installed-manifest.json"
proof.write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({"installed": len(files), "patched": len(set(changes)), "manifest": str(proof)}, indent=2))
