# Existing face finish 29

One candidate built from the exact accepted OriginalSeamBlinkFinish1 sources. The diagnosis was shallow lip relief and weak separation in actual face-default26, despite existing lip UV pigment masks. This candidate sculpts the original Body only; it adds no replacement head or feature meshes.

Upper/lower lip relief follows smooth symmetric fits through each source’s own upper/lower lip vertex loops, rather than following individual scattered seam points. The upper lobe advances 2.6 mm male / 2.8 mm female; lower lobe 3.7 / 4.0 mm. A 1 mm recess follows the existing mouth seam. Nose wings advance at most 1.8 mm, tip 1 mm, nostril recess 1.6 mm and broad cheek relief 1.2 mm. Combined actual displacement is bounded by 4.5 mm, only along face depth Y. See source-gate.json for exact per-vertex deltas and changed bounds.

The initial source preview caught jagged relief from interpolating scattered seam samples. The staged single candidate uses smooth fitted loop curves and lobes aligned to the original upper/lower lip bands. The final front and threequarter source portraits show clearly separate lip volumes and a continuous mouth separation; pigment remains natural. Existing source lip pigment masks, UVs, colors and runtime pigment revision1 are unchanged. No runtime material patch is included.

Source and exported-FBX checks pass: 53 bones/rest hierarchy, topology/weights/groups/UV/colors, Eye13 ReferenceFeatures and shape targets, X/Z coordinates and all active blink vertices exact. Same Y displacement is applied to Basis, Hero_Blink_Half and Hero_Blink, preserving all blink deltas. Rest/export checks are reproducible using build-face-finish.py and verify-fbx-roundtrip.py.

The existing recorded-pose ray test passes full closure on Ready/Serve/Forehand/IntroWave sample2 for both sexes. Female all aperture stages and male three other clips are exact. Male Serve right-eye visible-ray counts change from 166 to 135 open, 107 to 78 at quarter blink and 60 to 37 at half blink; left eye and later stages stay exact. This is a recorded visibility difference from sculpted facial depth, not a modified eyelid, eye or blink delta. It needs actual pose review. See blink-regression-gate.json; it deliberately does not label counts identical.

Root integration: use Male_OriginalFaceFinish29.fbx and Female_OriginalFaceFinish29.fbx with the existing original-seam importer/rig contracts and pigment revision1. Assets remain root-owned. Run matched actual front/threequarter portraits and blink stages against face-default26; also review male Serve2. The CPU Blender portraits only establish a visible source change. Actual gameplay portrait/art acceptance is pending; no Unity/phone or final-performance claim.

Reproduce work-only:

    /Applications/Blender.app/Contents/MacOS/Blender -b -t 3 --python work/reference-rebuild/face-finish29/build-face-finish.py
    /Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python work/reference-rebuild/face-finish29/verify-fbx-roundtrip.py
    /Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python work/reference-rebuild/face-finish29/verify-blink-regression.py
    /Applications/Blender.app/Contents/MacOS/Blender -b -t 3 --python work/reference-rebuild/face-finish29/render-source-preview.py
