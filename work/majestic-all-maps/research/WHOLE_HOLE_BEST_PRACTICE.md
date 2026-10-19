# Whole-hole beauty at 60 fps: best practice from golf and open-world games

Research date: 2026-10-17. Web research only. No local Unity or Blender work was done.
Every claim has a URL. **UNVERIFIED** marks anything I could not confirm from a source I actually read.
Most points are paraphrased. No source is quoted for more than 15 words.

**Source quality.** No golf studio has published a postmortem on environment dressing. That covers Camelot, Clap Hanz, HB Studios, Playdemic and Yakuto. The golf evidence below comes from developer interviews, the official PGA 2K designer pages and patch notes, wikis and reviews. The environment-art methods come from GDC talks, studio blogs, 80.lv artist write-ups and the Unity and Unreal manuals.

---

## 1. Sightline planning: give every camera a subject

**What the games do**
- **Mario Golf: Super Rush always marks the target.** A tall, glowing blue pillar of light marks the hole and can be seen from far away. The game also has several views of the hole: a bird's-eye view with a club-range circle, a terrain scan, a landing-zone scan from higher up, a zoomable full map with a mini-map, and a side-on trajectory replay. Whichever way the camera points, the goal is in shot. https://www.mariowiki.com/Mario_Golf:_Super_Rush
- **Super Rush's courses are open fields, not holes in boxes.** Camelot aimed for courses the size of Breath of the Wild's fields, with Nintendo's help. Holes flow into each other with fewer screen changes than earlier games. https://nintendoeverything.com/mario-golf-super-rush-camelot-zelda-advice/ and https://destructoid.com/mario-golf-apparently-took-some-notes-from-zelda-breath-of-the-wild
- **The cost of open fields.** EGM called the big open courses boring and said they needed more varied terrain. Big, open and sparse is not beautiful. https://egmnow.com/mario-golf-super-rush-review/
- **Breath of the Wild's triangle rule (CEDEC 2017).** Triangular hills partly hide what is behind them, which makes the player wonder what is there. Rectangular masses hide things completely. Nintendo used the rule at three scales. https://80.lv/articles/the-design-secrets-of-breath-of-the-wild/?amp=1 and https://gigazine.net/gsc_news/en/20171004-breath-of-the-wild-design-secret
- **Breath of the Wild's landmarks.** Nintendo moved from planned routes between points to scattered landmarks, which players found and used on their own. https://gmtk.substack.com/p/how-nintendo-solved-zeldas-open-world
- **Ghost of Tsushima's sightlines.** The team's rule was close to "if you can see it, you can reach it". Recognisable landmarks act as destinations: shrines, castles and huts. Each region has its own identity. https://blog.playstation.com/?p=333111
- **Destiny 2's backgrounds.** Tony Arechiga, a background artist, finds the spots in the playspace where players actually see the background, then tightens the composition there. https://80.lv/articles/creating-breathtaking-game-backgrounds

**Real golf architecture**
- **Partial view of the target.** A classic course-design principle shows only part of the flagstick from the ideal approach, controlling what the golfer sees. https://archive.lib.msu.edu/tic/bulls/article/1964nov9.pdf
- **Every hole should have its own character.** Architects surveyed in 2021 still rated this principle as highly relevant. https://thegolfbusiness.co.uk/2021/10/four-of-the-13-principles-of-golf-course-design-are-no-longer-relevant/
- **Framing is a contested term.** Framing can be natural, as at Cypress Point and Turnberry, rather than built by the architect. https://www.golfclubatlas.com/forum/index.php/topic,3500.0.html

**What to do here**
- Make a table of the hole's cameras: tee, ball in flight, landing, fairway lie, approach, green, looking back from the green, and the intro flyover.
- Name one subject per camera: the green and flag, a landmark, a water edge or a tree frame.
- Treat a camera with no subject as a FAIL.
- Keep the flag or green marker readable from every gameplay camera, as Super Rush does with its pillar.

## 2. Landmarks and skyline layers: near, mid, far and sky, all the way round

- **Build beyond the playable area.** Arechiga builds terrain and mountains outside the play space. He blends the land into the sky dome with additive fog cards at the horizon. He uses a few alpha cards to break up ridgelines and hide seams. https://80.lv/articles/creating-breathtaking-game-backgrounds
- **Check values and scale.** Arechiga checks the values in greyscale so that each layer recedes. He repeats foreground objects, such as tree types, in the distance so the far layers read as large and far away. Same source as above.
- **Work from the sky inward.** Mukul Soman's skybox method starts with the sky. The mid- and near ground are real geometry. Fog and cloud cards with vertex alpha and scrolling UVs tie terrain, vista and sky together. Motion in distant layers stays slow. https://80.lv/articles/creating-skyboxes-for-aaa-games?amp=1
- **A skybox only works for what the player can never reach.** It suits sky, clouds and far mountains. Its faces must meet with no visible seam. Fog hides the background but can make the scene look flat or closed in. https://www.gamedeveloper.com/art/creating-backgrounds-for-3d-games
- **PGA Tour 2K23's designer has backdrop options.** It has 12 themes, and Lighting, Terrain, Weather and Backdrop can each be set separately. So distant scenery is a swappable layer, independent of the holes. https://pgatour.2k.com/2k23/up-your-game/course-designer/
- **Wuhu Island is treated as a character.** Miyamoto wanted the island itself to be a character, reused across games so players already know its layout. https://iwataasks.nintendo.com/interviews/wii/wiisportsresort/0/1
- **Wuhu golf sits on Wedge Island.** The archipelago also has a large volcano. https://en.wikipedia.org/wiki/Wii_Sports_Resort
- **UNVERIFIED: the volcano as a landmark for the golf holes.** I found no source saying the volcano was placed so it shows up behind golf holes.
- **Reverse views.** I found no source, for any of the named games, on how they dress the view looking back at the tee. **UNVERIFIED.** My recommendation, drawn from Arechiga's 360° approach: give each hole one landmark per compass quadrant, or at least one behind the tee, and check the look-back camera like any other camera.
- **A sky that looks good wins.** Firewatch's procedural sky let artists set its colours by eye, without physically based scattering settings. https://blog.camposanto.com/post/112703721804/this-blog-post-is-an-in-detail-explanation-of-part

## 3. Scatter and dressing rules

- **Ghost of Tsushima, foliage.**
  - Few foliage types per biome.
  - Push colour values, raise translucency and cut texture noise so plants read as clean shapes.
  - Treat one element, such as a pampas field, as a graphic feature.
  - Scatter procedurally, keep density and plant type editable, and allow hand-painting where control matters.
  - Source: https://blog.playstation.com/?p=333111
- **Horizon Zero Dawn, placement.**
  - Placement is data-driven, deterministic and locally stable. Moving terrain or roads does not mean redressing by hand. https://www.guerrilla-games.com/read/gpu-based-procedural-placement-in-horizon-zero-dawn
  - The slides give 500+ asset types, 100k+ objects and about 250 µs of GPU time. I got these figures from the search index; the 10 MB PDF was too large to open, so its density-thinning rules are **UNVERIFIED**. https://www.guerrilla-games.com/media/News/Files/GDC2017_VanMuijden_GPUBasedProceduralPlacementInHorizonZeroDawn.pdf
- **Far Cry 5, ecological rules.** Forests grow denser on north slopes, ponderosa pine fills the valleys, and grassland covers exposed hills. Placement follows the terrain, not a uniform spray. https://blog.playstation.com/2018/03/22/the-procedural-world-generation-of-far-cry-5/
- **Far Cry 5, forest edges.** Earlier Far Cry games needed artists to hand-draw forest boundaries; Far Cry 5's procedural tools replaced that. https://gamesbeat.com/ubisoft-winnipeg-guides-ubisofts-use-of-ai-and-cloud-computing-to-make-bigger-better-games/
- **PGA Tour 2K designer tools.**
  - **Auto rough.** Rough is generated automatically. A "Clear Auto Rough" tool removes it with any brush, with an opacity setting (patch 1.06). Patch 1.10 added 75+ rocks and 40 trees. https://pgatour.2k.com/2k23/fr-FR/patch-updates
  - **Splines.** 2K23's spline tool lays walls and fences on slopes. The older tool handled surfaces and bulk planting of trees, flowers and natural elements. https://gamechronicles.com/course-designer-upgrades-revealed-for-pga-tour-2k23
  - **2K25 additions.**
    - Fescue that changes colour with the surface below it.
    - An edge-blending slider where two surfaces meet.
    - Surface weathering, which browns some of the grass.
    - Four-layer terrain painting.
    - Higher-resolution terrain.
    - Water splines.
    - Rocks with adjustable wetness.
    - Bunkers stamped into the terrain with lip controls.
    - Source: https://pgatour.2k.com/2k25/up-your-game/course-designer/
- **UNVERIFIED: PGA 2K density caps and object budgets.** I found no published limit. One review says the designer has no practical limit. https://www.golfchannel.com/news/pga-tour-2k21-review-finally-golf-game-thats-best-both-worlds
- **What goes wrong without dressing rules (Everybody's Golf Hot Shots, 2025).**
  - Trees look simplistic and grass flat. https://www.nintendolife.com/reviews/nintendo-switch/everybodys-golf-hot-shots
  - Courses look unlit, foliage sticks awkwardly out of the ground, and the reviewer found the PS3 versions of the same courses looked better. https://nintendoeverything.com/everybodys-golf-hot-shots-review-for-nintendo-switch/
  - Almost no crowd makes the courses feel empty. https://nintendowire.com/reviews/everybodys-golf-hot-shots/
- **My synthesis (not from a source).**
  - **Corridor gradient:** clean fairway, then the first cut, then rough with clumps, then a tree line, then a dense mass of trees and finally the backdrop layer.
  - **Clusters:** place in groups of 3–7 with gaps, never a uniform grid.
  - **Grounding:** every tree and rock gets a base: a soft dark patch, longer grass or a skirt.
  - **No empty ground:** no flat empty area larger than about one screen-width in any gameplay camera.

## 4. Performance: keeping it cheap

- **Unity Terrain distance settings.**
  - Detail Distance culls grass and detail meshes; too short and they visibly pop.
  - Tree Distance culls trees.
  - Billboard Start switches a tree from mesh to billboard; too short and trees seem to change shape.
  - Fade Length sets the length of that crossfade.
  - Source: https://docs.unity.com/en-us/engine/6000.0/manual/creating-environments/script-terrain/terrain-other-settings
- **LOD Group.** Transitions are set by on-screen size, with optional crossfade. https://docs.unity3d.com/Manual/LevelOfDetail.html
- **Unity's mobile tips.**
  - Cut triangles by about 50% at each LOD step.
  - Use static batching or CombineMeshes, and texture atlases.
  - Bake AO into the diffuse texture.
  - Bake occlusion culling.
  - Skip LODs when the camera is static or the mesh is already low-poly.
  - Source: https://unity.com/how-to/mobile-game-optimization-tips-part-1
- **Per-layer culling.** `Camera.layerCullDistances` gives each layer its own cull distance, for example small props at 60 m. `layerCullSpherical` stops objects popping at the screen edges when the camera turns. https://docs.unity3d.com/ScriptReference/Camera-layerCullDistances.html
- **HLOD.** Merging distant groups into one proxy mesh with one material gives one draw call per proxy. https://dev.epicgames.com/documentation/unreal-engine/hierarchical-level-of-detail-overview-in-unreal-engine
  - Unity has `com.unity.hlod` (Unity-Technologies/HLODSystem), but it is not officially supported. https://openupm.com/packages/com.unity.hlod/
- **Impostors.** Unity's industry toolkit describes impostors for far-distance LOD. https://docs.unity3d.com/Packages/com.unity.industry.toolkit@3.0/manual/create-impostors.html
  - Amplify Impostors pitches them for mobile and Switch to cut polygons and draw calls. https://discussions.unity.com/t/amplify-impostors-next-generation-billboards/707589
- **Batching in URP.** The SRP Batcher takes priority over GPU instancing. A foliage shader has to be built for one path or the other. https://docs.unity3d.com/cn/2023.2/Manual/GPUInstancing.html
- **The PGA 2K series runs on Unity.** Its Switch 2 port uses Unity 6 deferred lighting and screen-space reflections. https://unity.com/ja/news/unity-2k-games-pga-tour-2k25-nintendo-switch-2
- **The Golf Club also chose Unity.** It wanted no loading screens between holes. https://www.mcvuk.com/unity-focus-the-golf-club/
- **Pop-in shows up when the camera moves.**
  - In Hot Shots, trees and shadows pop in as the camera pans over a course. https://www.cubed3.com/games/reviews/nintendo-switch/everybodys-golf-hot-shots
  - Nintendo Life reported heavy LOD pop-in and said frame-rate trouble hurt swing timing. https://www.nintendolife.com/reviews/nintendo-switch/everybodys-golf-hot-shots
  - Unlocking the frame rate on the first Switch led to about 35 fps with uneven frame timing. https://www.nintendolife.com/news/2025/09/everybodys-golf-hot-shots-update-improves-performance-on-switch-2
  - Lesson: flyovers and pans are where you test LOD and cull distances, and a stable frame rate beats detail in a timing-based game.
- **Mobile golf (Golf Rival vs Golf Clash).** Golf Rival has simpler textures, shaders and lighting than Golf Clash. It runs on low-end Android and loads faster, while Golf Clash lagged more in the author's tests. https://naavik.co/deep-dives/the-turf-war-between-golf-clash-golf-rival/
  - **UNVERIFIED: how Golf Clash and Golf Rival build their courses.** I found no source on pre-rendered backgrounds, camera-limited dressing, their engines or draw-call budgets.
- **Ghost of Tsushima, wind.** Its wind simulation favoured volume over accuracy across millions of grass blades. Cheap, coherent motion sells a scene. https://gdcvault.com/play/1027124/Blowing-from-the-West-Simulating and https://gamedeveloper.com/design/using-vorticles-to-simulate-wind-in-i-ghost-of-tsushima-i-

## 5. Hiding the seams at the edge of the island

- **Hide with land, cards and fog.** Build land past the playable area, put additive fog cards at the horizon, and break hard ridgelines with alpha cards. Hide as much as possible with as little geometry as possible. https://80.lv/articles/creating-breathtaking-game-backgrounds
- **Hide transitions under cover.** Swap between sky layers while the player is in a covered section. https://80.lv/articles/creating-skyboxes-for-aaa-games?amp=1
- **Skybox rules.** Use a skybox only for what the player can never reach, and match its faces exactly. Fog alone flattens the scene. https://www.gamedeveloper.com/art/creating-backgrounds-for-3d-games
- **Aerial perspective.** Distant surfaces pick up atmospheric haze. Unreal evaluates this per vertex on mobile, and a distance-scale setting thickens it. https://dev.epicgames.com/documentation/unreal-engine/sky-atmosphere-component-in-unreal-engine
- **Rectangular masses block the view completely,** for example a bluff or a building that hides the end of the map. https://80.lv/articles/the-design-secrets-of-breath-of-the-wild/?amp=1
- **UNVERIFIED: how the named golf games bound their worlds.** I found no source on whether they use terrain skirts, water rings or camera limits at the edge. The Wuhu setting, an island in open sea (https://en.wikipedia.org/wiki/Wii_Sports_Resort), suggests ocean as a natural edge. That is my inference.
- **My recommendation (synthesis).**
  - **Skirt:** a terrain skirt that rises or falls past the edge.
  - **Water ring:** a horizon-locked water plane.
  - **Card ring:** a ring of far tree and mountain cards, with height fog matched to the sky colour at the horizon.
  - **Camera clamp:** clamp camera pitch and yaw on the flyover and look-back cameras so they never see past the skirt.
  - **Test shot:** look at the horizon from each gameplay camera.

## 6. Golf camera sets

- **Mario Golf: Super Rush.**
  - Bird's-eye view with a range circle.
  - Terrain scan and landing-zone scan.
  - Full map plus mini-map.
  - Rangefinder.
  - Camera reset.
  - Side-on trajectory replay showing carry and roll.
  - Source: https://www.mariowiki.com/Mario_Golf:_Super_Rush
- **PGA Tour 2K25.** The designer now includes the camera-sequence tools HB Studios used for official courses in the previous two releases. That suggests every official hole is shot from authored camera sequences. https://pgatour.2k.com/2k25/up-your-game/course-designer/
  - **UNVERIFIED: flyovers dropped.** One player claim, not checked, says hole flyovers were removed in the last two 2K games. https://steamcommunity.com/app/1588010/discussions/0/4288063042476907238
  - Scout cam and zoom cam controls in 2K23 are also only from player forum answers (same thread).
- **Golf Clash.**
  - The aim target is placed automatically and can be moved.
  - Putts show a path of light; the flag rises when power is right, and the hole glows when the putt is lined up.
  - Source: https://www.levelwinner.com/golf-clash-ultimate-guide-13-tips-tricks-become-best-player/
  - **Golf Rival:** zooming and pinching are less smooth, which makes long shots harder to aim. https://naavik.co/deep-dives/the-turf-war-between-golf-clash-golf-rival/
  - **UNVERIFIED:** the exact Golf Clash camera list (top-down overview, flight follow).
- **A camera idea from players.** A sim-forum proposal: watch the first two-thirds of the flight from the tee, then cut to a follow camera for the landing. https://golfsimulatorforum.com/forum/golf-simulator-brands-and-types/the-golf-club/14650-tgc-cool-camera-idea
- **Everybody's Golf Hot Shots.**
  - Character animations block the view while teeing up and putting. https://nintendowire.com/reviews/everybodys-golf-hot-shots/
  - Pop-in shows during camera pans. https://www.cubed3.com/games/reviews/nintendo-switch/everybodys-golf-hot-shots
- **Golf Story.** A top-down 2D game across eight areas, each with its own courses and characters. Each area is more than greens and fairways. Because the camera is fixed, dressing only has to survive one viewing angle.
  - https://en.wikipedia.org/wiki/Golf_Story and https://gameinformer.com/games/golf_story/b/switch/archive/2017/09/21/rpgs-and-sports-merge
  - **UNVERIFIED:** any art-process detail. The Red Bull interview page would not load.
- **UNVERIFIED: Wii Sports Resort golf cameras.** I found no source on whether it has a hole-view or aerial camera.
- **How art is checked against cameras.**
  - The only sourced method is scouting the actual player views and composing for them (Arechiga, above).
  - PGA's authored camera-sequence tools point the same way.
  - Recommendation: build a capture harness that renders every hole from every camera in the set and gates each frame. A frame fails if it has no subject, if the void is visible, if flat empty area exceeds the limit, or if objects pop in during the flyover.

---

## Applied checklist for our holes (synthesis, not sourced)

1. **Camera table per hole.** List tee, flight-follow at 3 points, landing, fairway lie, approach, green, green looking back to the tee, and the intro flyover path. Name one subject per row.
2. **Four layers.**
   - Near: play corridor dressing.
   - Mid: tree lines and water.
   - Far: landmark plus terrain or card ring.
   - Sky: dome with clouds.
   - At least one landmark per quadrant. The look-back camera must have a subject.
3. **Dressing gradient.**
   - Clusters of 3–7.
   - Every object grounded with a base patch.
   - Few foliage species per course, with pushed colour values (the Ghost of Tsushima rule).
   - No empty flat area wider than a screen in any gameplay camera.
4. **Budget.**
   - Grass on a short detail distance with long crossfades.
   - Trees as mesh, then billboard or impostor.
   - Per-layer cull distances with `layerCullSpherical`.
   - Merged far proxies (HLOD), baked AO and lighting, atlased far cards.
   - Foliage shaders that are SRP Batcher compatible.
5. **Edges.** Skirt, water or card ring, plus height fog matched to the horizon, plus camera clamps on the free cameras.
6. **Gate.** Capture frames from every camera; check the flyover frame by frame for pop-in; hold frame-time stable before adding detail.
