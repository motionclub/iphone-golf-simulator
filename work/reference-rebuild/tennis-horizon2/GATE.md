# Tennis horizon2 — layered forest ridge island

GATE: WORK-ONLY SOURCE / SCOPE PASS.
GATE: ACTUAL UNITY APPEARANCE / IMPORT / BALL READABILITY PENDING ROOT CAPTURE.

One backdrop deliverable: replace the three smooth low mounds with one authored archipelago mesh, using the existing TennisCoast constrained-Delaunay / sealed-shell / blended-vertex-colour workflow. The centre island carries an irregular connected high spine, a lower winding foreground forest ridge and descending spurs. Recessed side islands keep lower cooler ridges. Forest light/shade and bounded limestone breaks supply depth without tiny trees, alpha foliage or new scene decorations. Original centres and nominal island extents are retained; court/runoff/coast fixtures remain authoritative.

Source budget: 7,540 triangles /3,777 vertices, one mesh and one material. Existing runtime three-island tessellation produces32,400 triangles, so source triangle count drops76.7%; actual imported vertices/passes remain root capture measurements. Three source shells have0 boundary /0 nonmanifold edges, with sealed submerged skirts/bottoms. Main crest61.84m, east32.26m, west26.41m. World geometry remains at least500.65m beyond the court; no physical or gameplay meshes change.

Source proof:
- ridge-panorama-source.png shows the authored landform and lower forest layer.
- reference14-horizon-source.png uses the unchanged actual reference14 camera position(2,1.8,-15.3), target(0,1,7), vertical FOV54. It renders source islands/sea only, with source lighting. It does not establish the Unity material/fog result or complete court composition.
- Before authority is the actual accepted palm frame proof/reference-rebuild/tennis-resort-finish1/candidate/resort_14_reference_camera.png plus the user tennis-target.png. The new crest is intentionally taller/craggier than the low mound silhouette; compare the actual frame before accepting its prominence.

The existing resort linear fog starts180m /ends900m. At600m it washes approximately58% into the global sky haze, collapsing the old green ridge response. A dedicated TennisHorizon2.shader copies the existing TennisWorldSurface shader with only a per-material horizon fog-share setting. Share.40 keeps about23% of that haze at600m, retaining designed forest/mineral gradients and cooler recessed layers. This does not alter the original shader, global fog, lighting, postprocess, court or character materials. horizon-shader-origin.patch documents the exact four conceptual differences.

Integration:
1. Root imports TennisHorizon2.fbx with supplied .fbx.meta into Unity/Assets/Resources/Tennis/Premium/. Editable .blend and build-horizon.py remain work-only. Import globalScale1, file units/source normals, no colliders. The FBX exports linear vertex colours under HorizonAlbedo and one HORIZON_FOREST_LIMESTONE material role.
2. Copy the dedicated shader into Unity/Assets/Resources/Tennis/Shaders/TennisHorizon2.shader. Apply horizon-runtime.patch to TennisResortVista.cs. It only adds the pilot early return and resource/material helper; Island/Pergola/Column/Make remain byte-unchanged. Missing prefab/shader preserves the old island fallback.
3. Pilot via TENNIS_HORIZON2=1. Flag0/absent renders the old mounds. No live Assets changes or Unity runs were made by this agent.

Small capture gate: capture-gate.json requests before/candidate gameplay1, hero-postcard9 and reference14 only. Require actual imported bounds at positiveUnityZ500–779m (otherwise reject import orientation), one backdrop mesh/material and no colliders. Require green forests, sunlit rock breaks and at least two readable ridge layers, with quieter cooler side islands; reject a pale glacier response, dark triangular spikes, noisy streaks, aliased coastline or distracting repeated bumps. Preserve clear central sky/sea and white/yellow ball readability; no new object may enter the play corridor. Require unchanged court/net/actor/collider/ground data and cameras, no missing-resource/shader errors, and actual triangle/pass accounting. This bounded source candidate does not establish full resort or three-venue acceptance.
