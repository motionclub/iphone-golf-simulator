# Golf course reference backlog — current whole-catalog review

Reviewed latest saved actual gameplay for all 19 routes (1–3, 7–10, 12–23), the nine-tee turf sheet, latest19 preview, and original GPT coastal/temple/volcanic targets. `capture-index.json` records the newest available per-route evidence; `all19-gameplay-review.jpg` is the review contact sheet. Older final-world captures remain the newest available for several dry/cold/volcanic routes, so those routes need refreshed captures after the next shared change. This is a visual backlog, not an implementation-complete gate.

## 1. Replace the remaining coarse tree crowns; give rough margins connected planting masses

**Visible gap:** Coastal12's artist conifers are a step above the rest of the catalog. Holes7/13/15/17 still show stacked angular conifers;14/20 show faceted elongated canopy blobs. Temple19 and volcanic21–23 have very thin drooping palm crowns and isolated bushes. The temple reference instead has full arched palm canopies and overlapping broadleaf masses whose silhouettes connect into an island edge. Current low plants remain small repeated islands, leaving large empty rough areas.

**Implementable next deliverable:** Golf-only tropical planting pilot on19, preserving every original tree pivot and obstacle. Port the existing source-reviewed coconut/canopy candidates into a separate render-only golf kit; fix silhouette/scale at the current cameras, then add 2–3 bounded edge planting clusters with near/far meshes. Start from existing authored sources, not another procedural palm reset. Capture normal gameplay + preview + approach, with an actual before/after pair. Only after this passes, roll tropical art into16/21–23 and corresponding links, and prepare an evergreen/canopy swap for7/13–15/17/20 andMeadow1–3.

**Exact files:**
- `Unity/Assets/Scripts/Course/GolfResortDress.cs` (tree kind/placement, pivot-preserving crown proportions, batching and LOD)
- `ArtDir/golf/source/BotanicalKit.blend` (current templates; do not silently overwrite)
- `ArtDir/golf/tools/export-golf-art.py` (bounded export)
- `ArtDir/tennis/venues/botany/source/TennisCoconutPalm.blend`
- `ArtDir/tennis/venues/botany/build-coconut-palm.py`
- `ArtDir/tennis/venues/botany/source/TennisCanopy.blend`
- `Unity/Assets/Scripts/Course/GolfCoastalBotany.cs` (proven separate kit pattern on12)

Tennis source candidates are not automatically accepted for golf; the palm's current near/far counts are31,876/14,284tri, so golf placements need a stricter far representation and measured aggregate cost. Existing `golf-art-next` primary-forms work only improved shrubs/rocks, not these tree crowns; do not repeat it.

## 2. Build layered rock/horizon compositions that expose the water/lava and landmarks

**Visible gap:** Coastal12 currently presents a nearly full-width tall textured cliff, with little visible water opening, small treetops and sparse crest vegetation. The target balances a lower visible cliff band, blue ocean, plant masses and distant ridges. Volcanic21–23 show smooth dark crater slopes with narrow glowing stripes; the target has stepped fractured basalt silhouettes, distinct near/middle/far layers and a broad luminous lava channel. Temple19's existing playable island/temple shape is usable, but previews are too distant and aerial fog washes out contrast.

**Implementable next deliverable:** One composition pass each for12 and21 using existing playable geometry unchanged: lower/offset selected render-only foreground geological shoulders, replace smooth background crater silhouette with 2–3 authored basalt ridge layers, and set a preview camera that fills the frame with the course. Use crest vegetation and rocks to connect the cliff top to grass. Do not alter tee/pin, colliders, ground or obstacle groups to imitate a generated layout. Golf12 can use a modest camera-height/pitch adjustment already explicitly authorized by the user; judge the actual playable camera and aim readability.

**Exact files:**
- `Unity/Assets/Scripts/Course/GolfCoastalCliff12.cs`
- `ArtDir/golf/source/ReferenceCliffs12.blend`
- `ArtDir/golf/tools/build-reference-cliffs.py`
- `Unity/Assets/Scripts/Course/GolfCoastalBotany.cs` (`PlantCrestPockets`)
- `Unity/Assets/Scripts/Course/LavaWorld.cs` (`DistantRidges`, crater wall, cascades)
- `Unity/Assets/Scripts/Course/GolfCourseAtmosphere.cs`
- `Unity/Assets/Scripts/Game/CameraRig.cs`
- `Unity/Assets/Scripts/Course/CourseShot.cs`

This is primary silhouette/composition work. Adding stronger noise to the existing wall material alone will not close the gap. Any displaced visible rock beside collision surfaces must retain clear obstacle cues.

## 3. Carry the accepted turf treatment through play; blend cut zones into landscape edges

**Visible gap:** Dense15 blades and real-course palette are the most successful recent improvement. They currently occupy bounded12m tee patches on nine holes. The player can still leave them behind; Meadow and nonselected natural turf have no physical blade treatment. Many surfaces switch at straight geometric edges and look like isolated flat green panels. The reference shows physical leaf detail around the player and restrained cut-height/rough transitions throughout the course.

**Implementable next deliverable:** Move the same bounded tile pool with the local golfer/ball, rebuilding only when crossing a coarse cell boundary and reusing the existing48near/96mid/640total caps. Retain fine green texture without long green blades. Keep path, bunker, snow, rock and lava exclusions, with role-based heights for tee/fairway/fringe/rough. Pilot12 tee→fairway→approach and14 along a tree-shadowed fairway; then extend the shared turf sampling contract toMeadow and suitable grass zones on17/18/volcaniccourses without planting in snow/sand/ash. Add a narrow irregular transition strip where existing surface meshes allow it; don't recolor the accepted palette globally again.

**Exact files:**
- `Unity/Assets/Scripts/Course/GolfCoastalTurf.cs` (currently static `ApplyAroundTee`, `RadiusMeters=12`, `Supports` nine routes)
- `Unity/Assets/Scripts/Course/GolfTurfPalette.cs` (accepted per-role colors/patterns)
- `Unity/Assets/Resources/Course/Shaders/GolfCoastalTurf.shader`
- `Unity/Assets/Scripts/Course/GolfCourseFringe.cs`
- `Unity/Assets/Scripts/Course/GolfSurfaceEdges.cs`
- `Unity/Assets/Scripts/Course/GolfMeadowWorld.cs`

Required evidence: ordinary actual frames at each position, exact collider/ground/obstacle invariance, same submission/cell limits, no blades on protected surfaces. Native/phone performance remains unverified and phone testing remains deferred as requested.

## Acceptance for these next passes

Capture actual current and candidate in matching views; use the saved GPT target for composition and material goals without implying pixel-exact attainable parity. Preserve current good grass and all original character work. Passes should each deliver one complete visual slice before catalog rollout, with explicit remaining gaps.
