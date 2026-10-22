# Classic racket — how to reproduce (all headless; Blender 5.2.2 LTS, repo-relative paths are absolute inside the scripts)

```
B=/Applications/Blender.app/Contents/MacOS/Blender
# 1. racket (geometry: racket_geom.py + sdf_tools.py; builds export/Racket_Classic.blend)
$B -b --factory-startup --python scripts/build_racket.py -- export/Racket_Classic.blend
# 2. FBX (hero flags: meters, scale 1, -Z forward / Y up) + re-import verification
$B -b export/Racket_Classic.blend --python scripts/export_racket.py -- export
# 3. fit / sockets / proof poses (male|female); hero blends are only read via library load
$B -b --factory-startup --python scripts/run_onhand.py -- male   export/Racket_Classic.blend data/onhand_run 52 -0.02 0.0 45
$B -b --factory-startup --python scripts/run_onhand.py -- female export/Racket_Classic.blend data/onhand_run 52 -0.02 0.0 45
#    (args after the blend/out dir: phi_deg U_g V_g roll_deg)
# 4. renders
$B -b --factory-startup --python scripts/render_racket.py -- export/Racket_Classic.blend proof/raw/racket all
$B -b export/RacketOnHero_Male_APose.blend --python scripts/render_proofs.py -- proof/raw/male_apose male apose all
$B -b export/RacketOnHero_Male_APose.blend --python scripts/render_socket_diagram.py -- proof/raw/socket_male_apose male apose
python3 scripts/compose_proofs.py
# 5. gates
$B -b --factory-startup --python scripts/final_checks.py
```

| file | role |
|---|---|
| `racket_geom.py`, `sdf_tools.py`, `build_racket.py` | racket geometry (tube SDF smooth union, surface nets, decimate), materials, blend |
| `export_racket.py`, `fbx_peek.py` | FBX export + re-import check, FBX header/node inspection |
| `onhand.py`, `run_onhand.py`, `fitlib.py` | hand frames, grip solve (exact clearance, tri–tri overlap), proof poses, socket data |
| `male_hand.py`, `female_hand.py`, `handpose.py`, `wrap.py`, `fingerwrap.py`, `armpose.py` | digit models, path-based finger wrap, arm skinning (proof-only, on copies) |
| `render_*.py`, `compose_proofs.py` | proof renders / sheets |
| `final_checks.py`, `measure_racket.py` | measurements and gate evaluation -> `checks.json` |
| `vertex_dist_check.py` | Blender-side counterpart of the Unity socket check (`data/unity_check_socket.json`) |

`scripts/dev/` holds the exploratory probes/experiments used while developing (hand maps, wrap scans, remesh experiments); they are not part of the pipeline.

Unity checks (`data/unity_check_*.json`) were produced in a throwaway project in the session scratchpad with Unity 6000.3.24f1 batchmode (`RacketCheck.Run`, `SocketCheck.Run`); the editor scripts are not kept in the repo.
