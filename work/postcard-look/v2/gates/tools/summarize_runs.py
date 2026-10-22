"""Print the PASS/FAIL of the v2 gates (blend stage; fbx stage in brackets when it differs) for the verify runs in runs/*.json."""
import json, sys, os, glob
V2 = ["ROCK_NOT_ICOSAHEDRON", "ROCK_VARIETY", "LOOK_FILES", "ALBEDO_DISTINCT", "GRASS_ALBEDO_HUE", "NO_FOAM_STRIP", "SURF_SHORE", "SHELF_THIN",
      "LAVA_TEXTURE", "BASALT_PRISMS", "SMOKE_SOFT", "SPLIT_SCRUB_RIDGE", "PROPS_OFF_PLAY", "NO_PLANT_ON_WATER", "NO_ROCK_STRETCH_2X", "PATH_UNDER_BALL",
      "CRATER_WALL_COVERED", "SEASTACK_TAPERED", "NEEDLE_SEA_STACKS", "NEEDLE_ARCH", "ONE_GREEN", "UV_DENSITY", "NEEDLE_CLIFF_SKIN", "SPLIT_SHORE_SKIN",
      "PLAY_SURFACE_FACES", "PLAY_SURFACE_WALLS", "PLAY_SURFACE_GRID", "PLAY_SURFACE_TOPS", "SHADERS_STATIC", "HOLE07_UNTOUCHED"]
runs = sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "runs", sys.argv[1] if len(sys.argv) > 1 else "*.json")))
for r in runs:
    d = json.load(open(r))
    g = {x["name"]: x["ok"] for x in d["gates"]}
    row = []
    for n in V2:
        b = g.get(n + "@blend", g.get(n))
        f = g.get(n + "@fbx")
        if b is None:
            continue
        tag = "PASS" if b else "FAIL"
        if f is not None and f != b:
            tag += f"(fbx {'PASS' if f else 'FAIL'})"
        row.append(f"{n}={tag}")
    print(f"{os.path.basename(r)}: {d['name']} {len(d['gates'])} gates, {len(d['failures'])} failed")
    print("   " + ", ".join(row))
