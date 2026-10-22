# Character-lighting look-dev capture

The lighting is **opt-in**: set `VISUAL_HERO_LIGHTING=1` before launching Unity. Unset or `0` retains the original lighting response. This is an experiment, not an accepted venue rollout.

Use Unity 6000.3.24f1 and a scratch copy of `Unity/Assets`, `Unity/Packages`, `Unity/ProjectSettings` and optionally its APFS-cloned `Library`. Do not run the capture installer against the shared project. No Git checkout is needed.

```sh
python3 ArtDir/style/character-lighting/tools/prepare_capture.py /private/tmp/hero-lighting-lookdev
VISUAL_HERO_LIGHTING=1 CHARLIGHT_ALL=1 AUDIT_OUT=/private/tmp/hero-lighting-lookdev/after \
  /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity \
  -batchmode -projectPath /private/tmp/hero-lighting-lookdev \
  -runTests -testPlatform PlayMode -testFilter GolfArcade.PlayTests.CharLightCaptureTests \
  -testResults /private/tmp/hero-lighting-lookdev/after-results.xml \
  -logFile /private/tmp/hero-lighting-lookdev/after.log
```

For an independent light-inventory baseline, run the same command first with `VISUAL_HERO_LIGHTING=0`, omit `CHARLIGHT_ALL`, and use `AUDIT_OUT=/private/tmp/hero-lighting-lookdev/before`, `before-results.xml` and `before.log`. The report compares that inventory with the enabled run.

Run foreground, with graphics enabled. `CHARLIGHT_QUICK=1` replaces the full matrix with Resort and hole 7 Clear plus the eight fixed-pose look-dev shots. Without either matrix variable, the supplied test's 44-shot matrix is retained, followed by the eight look-dev shots. Filter `GolfArcade.PlayTests.CharLight` to include the three activation/venue-state checks.

`prepare_capture.py` reads the supplied, unchanged `CharLightCaptureTests.cs.txt`. It preserves the beauty-shot cameras, adds a same-frame baseline, replaces the diagnostic mask, and adds the four-hero/two-environment comparison. All matrix sizes skip non-gameplay intros; they still wait for Aim and the supplied 1.5-second settle. Hole and weather assertions verify that each requested case loaded.

The original mask used lit materials on layer 31, which is also the game's weather-overlay layer. The diagnostic uses an asserted-unused layer 28 and unlit IDs: red = registered visible cheek/nose/forehead skin, green = shirt, blue = other hero geometry. Materials and layers are restored in `finally`. Eye, cap, lip and background colours cannot be mistaken for face skin. The face region comes from the existing head registration and bind positions; no mesh is edited. The all-four look-dev comparison freezes production poses into temporary meshes in the scratch process only.

The baseline switches off the analytic lighting and restores the old 0.12 presentation fill for a second render of the **same frame**. Camera, pose, materials, weather, venue lights and post are identical. The supplied `before_jpg/` and `metrics_before.json` remain unchanged; their rectangular/lit-mask samples are not used to claim a numerical improvement.

```sh
python3 ArtDir/style/character-lighting/tools/measure.py /private/tmp/hero-lighting-lookdev/after \
  --before /private/tmp/hero-lighting-lookdev/after/paired-before
python3 ArtDir/style/character-lighting/tools/build_lobby_reference.py \
  /private/tmp/hero-lighting-lookdev/native /private/tmp/hero-lighting-lookdev/after/hero-colours.tsv
/private/tmp/hero-lighting-lookdev/native/capture \
  /private/tmp/hero-lighting-lookdev/native/reference /private/tmp/hero-lighting-lookdev/native/colours.json
python3 ArtDir/style/character-lighting/tools/build_review.py \
  /private/tmp/hero-lighting-lookdev/after ArtDir/style/character-lighting/after
python3 ArtDir/style/character-lighting/tools/report_gates.py \
  /private/tmp/hero-lighting-lookdev/after ArtDir/style/character-lighting/after \
  /private/tmp/hero-lighting-lookdev/native/reference
```

Measurement uses D65 CIELAB from linearized sRGB and medians over the ID masks, eroded one pixel to avoid mixed boundary pixels. Fewer than 12 skin pixels is “not visible / insufficient pixels,” not a pass. Shirt hue uses circular HSV distance from the actual material's selected base colour. Silhouette dL is the absolute difference between the median inner three-pixel contour and the median outer three-pixel ring; it includes equipped geometry. This strict luminance test is not replaced by subjective colour contrast. It is applied to every gameplay shot.

The lobby reference compiles the app's existing SceneKit renderer and exported assets with the §15 key/fill/rim/ambient rig and the exact recorded skin/shirt picks. Marked cheek/nose ROIs and material-ID masks make those samples inspectable. The reference pose is the lobby pose; the golf gameplay pose still looks down under the cap. Native garment geometry may differ from the latest Unity kit, so this is a comparison to the current lobby, not a claim that those exports are identical.

Beauty PNGs and masks remain in the scratch capture directory. Review copies are JPEGs; measurements are calculated from PNGs, before JPEG conversion. `build_review.py` preserves the modern reference panels from the original W1–W4 sheets. Capture-test PASS means the captures completed, not that the visual gates passed. No editor capture proves iPhone FPS or the +0.2 ms GPU budget.

Exact installed test sources are also saved in `after/` with a `.txt` suffix. They can be copied directly into a scratch `Assets/Tests/PlayMode/` directory with that suffix removed; this avoids depending on the original brief input when reviewing only the staged files.
