# Full golf and tennis visual overhaul plan

Planning date: October 7 2026  
Direction: Premium stylized sports resort  
Scope: The entire game across golf and tennis: characters, skeletons, deformation, clothing, equipment, animation, mannerisms, every course/venue, effects, cameras, menus, controller and TV presentation. New collectible skins remain excluded; existing golf and tennis clothes receive a substantial construction and material overhaul.

## 1 The target

Make the game feel like a place people want to visit: inviting resort spaces, expressive athletes, beautifully maintained golf surfaces, and fantasy courses with unmistakable identities. Aim for the craft of polished console sports games within the current iPhone renderer and asset pipeline.

The visual language is rounded but purposeful geometry, broad readable shading, restrained surface detail, saturated focal colors, and believable material differences. Grass should feel groomed, stone should feel substantial, water should feel inviting, and characters should feel alive. Every course should have a memorable silhouette and a clear visual reveal.

The GPT Image projections in [the comparison gallery](comparison-gallery.html) illustrate that direction, including a dedicated tennis resort view and male/female character, garment and pose boards. Keep the richer resort direction as the ambition. Camera angles are malleable: reframe for stronger reveals, appealing characters and useful play visibility while preserving controls and gameplay geometry.

These images are concept targets rather than finished game screenshots or exact geometry specifications. Their major features have practical implementation paths below. Exact facial details, foliage density, small rock shapes, reflections, and shadows must be resolved using the real assets and device measurements. Conservative variants are supporting implementation references rather than the desired quality ceiling.

See [Character animation clothing and equipment](character-animation-clothing-equipment.md) and [Swarm execution plan](swarm-execution-plan.md) for the expanded character/performance scope, skeleton migration rules and agent assignments.

This is a plan and concept package. The overhaul itself has not been implemented.

## 2 What the project actually needs

The inspected project uses Unity 6000.3.24f1 and URP 17.3.0, Blender course/export scripts, SwiftUI menus, and SceneKit character/environment presentation.

The current course captures show very bright, noisy turf; simple tree silhouettes; abrupt terrain transitions; flat or repetitive rock treatment; and large HUD panels obscuring the destination. The shared lobby has an attractive resort backdrop, but its characters appear to float and feel disconnected from that backdrop's lighting.

The clay appearance has a concrete code path. `GolferView.Clay` constructs `GolfArcade/GolferClay`, and `HeroKit` also uses MatCap form shading. Their shared URP fragment path multiplies albedo by wrapped scene lighting; the explicit specular branch there is for the ball. Improving only the tennis character shader would miss these golf paths. Resolve which character branch each real entry point uses before replacing materials.

The October 6 course standardization notes report a completed shared-material migration. Build on that infrastructure. This overhaul raises the quality of the asset forms, lighting, composition, and presentation together; it should not repeat the migration as though it had never happened.

A fresh Unity capture attempted for this package stopped at existing compile errors in `NativeSessionTests`, `PlayerBaseTests`, and `StandardCharacterGameplayTests`. They reference removed members including `UsesStandardCharacter`, `SetFloatingHandsPreview`, and older `GolferStyle` fields. The before images therefore use the saved October 6 course captures and October 5 lobby capture. They are genuine game captures, but they cannot establish the exact appearance of the current unbuildable checkout.

## 3 Rules that keep the overhaul coherent

| Area | Art rule | Implementation rule |
| --- | --- | --- |
| Forms | Strong primary silhouettes, generous curves or deliberate stone facets, restrained small detail | Shape the Blender mesh first; use normals for detail that does not affect silhouette |
| Color | Emerald and jade play surfaces, navy and ivory UI, citrus accents; each biome owns a supporting palette | Store reusable palettes and lighting profiles, avoiding per-object guesses |
| Materials | Skin, fabric, leather, rubber, metal, rock, sand and water visibly differ | Separate roughness, normal strength and highlight response by material family |
| Lighting | Bright readable midtones, warm/cool separation, grounded contact, controlled highlights | Bake static bounce where useful; use a limited sun/shadow setup and baked reflections |
| Composition | Ball, lie, target and flight corridor remain immediately readable | Keep decorative density at boundaries and landmarks; reserve open space for play |
| Detail | Large forms and color masses first, fine texture only where the camera can resolve it | Mips, distance fades, LODs and controlled texture frequency |
| Motion | Subtle life in the world, confident character poses, restrained celebrations | Reuse rigs and clips; clean up transitions before adding complexity |
| UI | One component language from onboarding to results | Match SwiftUI and Unity tokens, metrics, icons and states |

Proposed UI tokens: navy `#10243D`, ivory `#FFF9EE`, muted blue `#8096A9`, citrus `#D7F044`, turquoise `#35B8C7`. These are starting art decisions; confirm their appearance on the actual display. Semantic power, warning and success colors must also have labels or shapes.

## 4 Characters and existing equipment

Keep the approved male and female head/body identities, proportions, and silhouettes. Repository locks require roughly 1.65–1.75 m height, 35–50k base triangles, and bald silhouette comparisons within about 5 percent. Follow the existing base plates and proof gates; GPT Image faces never replace those references.

Upgrade the base characters in this order:

1. Audit the actual golf, tennis, lobby, locker and spectator model/material branches. Establish a single material specification that each renderer can reproduce.
2. Replace the dominant MatCap look with controlled scene lighting, broad skin highlights, restrained warm shadow color, and baked reflection response. Retain only a small art-directed MatCap contribution if it improves the final image.
3. Refine skin color variation and soft normal response without noisy pores. Test every existing complexion under coastal sun, volcanic dusk, jungle shade and neutral locker lighting.
4. Improve eyes, brows, mouth contrast and face decals at gameplay size. Preserve the approved face design. Fix atlas alignment, seams and swimming projections before adding detail.
5. Finish the existing shirts, trousers, skirts, shorts, socks and shoes: readable seams and folds, subtle cloth sheen, rubber soles, leather panels and controlled white highlights. No new wardrobe content.
6. Repair hands, grip contact, elbow/shoulder deformation and feet where the real pose exposes problems. Avoid changes that alter the locked body identity.
7. Preserve currently available hair and accessories as separate assets. Respect opaque-volume hair requirements where applicable; do not introduce new styles.
8. Upgrade the skeleton and deformation where the audit demonstrates a need: joint roll/rest alignment, weights, forearm/upper-arm twist, shoulder/hip handling, fingers, foot roll, grip sockets and corrective shapes. Keep a versioned shared rig contract and rebuild all affected Unity/native exports together.
9. Refine the full locomotion and performance library: walk, starts/stops, turns, directional runs, recovery, address, backswing, impact, follow-through, idles, intros, all equipped emotes, score/match reactions and spectator behavior.
10. Add coherent eye focus, blinking, brows, smiles, concentration and small weight/hand adjustments. Coordinate face and body timing so characters have warm, athletic mannerisms rather than mannequin posing.

The current tennis driver declares 33 clip slots; the examined golf metadata lists Drive, IronSwing, HalfSwing, Chip, Putt, Idle, Wave, Cheer and FistPump. Existing emote routing also references Scuba, Thrust, Spike, Wave, Bring It and Push-ups. Audit actual availability for both bodies and all renderers before declaring any clip complete.

Skeleton changes are explicitly part of this overhaul. Earlier narrow task briefs that froze bone counts should not exclude this requested work. Preserve approved identity and gameplay authority, then version and migrate the rig deliberately. Animation and garment agents begin final baking/weighting only after the integration owner freezes that contract.

Existing clubs need separate shaft, head and grip finishes, correct reflection response, and reliable hand attachment. The ball needs restrained dimple shading, legibility on every surface, stable highlights and a controlled visibility aid. Finish the cup, flagstick, flag fabric, tee markers, bags and spectator props using the same material library.

Deliver male/female turntables, close face and hand proofs, garment proofs in extreme poses, a swing video per club family, tennis serve/rally/locomotion videos, intros/emotes and matching lobby/locker/gameplay captures. Existing clothes receive mesh construction, fitting, folds and material work; existing cosmetics improve without creating new collectible skins.

## 5 Environment overhaul

Build a compact authored Blender kit instead of decorating each hole from unrelated assets.

| Kit | Assets and treatments |
| --- | --- |
| Golf surfaces | Tee, fairway, rough, green and fringe; broad mowing direction; sand lips, paths, clean cup transition |
| Coastal | Layered limestone modules, shoreline skirts, pines, shrubs, bridge parts, lighthouse and clubhouse refinement |
| Volcanic | Basalt modules, obsidian variation, ash soil, restrained emissive fissures, lava edge shelves, sparse resilient planting |
| Jungle | Palm and broadleaf variants, clustered undergrowth, mossy stone, temple trims, waterfall and pool edge pieces |
| Alpine | Snow caps, cold rock, winter tree variants, readable ice edge, simple mountain backdrop |
| Desert | Sandstone layers, dry soil, cacti and scrub, warm cliff modules |
| Links | Soft grassy banks, tulip clusters, timber and masonry trims, canal edges, windmill finishing |

Playable terrain remains stable. Visual skirts and dressing may refine its appearance, but preserve the exact fairway routing, elevation, bunker and hazard boundaries, collision behavior and shortcut options. Decorations must be excluded from both colliders and the project's mesh-based obstacle collection; removing a Collider alone may not be sufficient.

Grass receives lower-frequency color variation, restrained normals, consistent scale, broad mowing bands, and sparse edge geometry. Stop filling the playable surface with glittering texture detail. Distant grass should resolve to pleasing color masses.

Rock receives designed silhouettes, broad layers, softened or deliberately faceted edges, believable roughness, and localized dirt/moss. Ensure the rock shader actually samples any normal map assigned to it. Water receives calm broad highlights, depth/shallow color, coherent shoreline foam and animated surface normals. Avoid a busy grid of sparkles. Lava receives flowing broad forms, crust variation and restrained emission; its brightness must not erase the hazard boundary or nearby turf.

Foliage receives varied but coherent trunk/canopy shapes, clear leaf masses, subtle wind and predictable LODs. Prefer opaque shaped leaves where suitable and use limited masked cards where needed. Palms need complete trunks and readable fronds; broadleaf trees need designed clusters rather than polygon balls. Bake or approximate small leaf contact instead of casting costly shadows from every leaf.

Refine all buildings, bridges, railings, signs, benches, planters, fences, docks and landmark props. Use reusable trim sheets for repeated architecture. Finish skies, distant islands/mountains, horizon transitions and background water, including the runtime-created backdrop paths.

## 6 Every course gets a specific identity

The selectable catalog has 16 holes. The three procedural Meadow holes also receive shared visual/fallback treatment without changing their availability.

| Hole | Distinct visual target | Critical preservation check |
| --- | --- | --- |
| 7 Cliffside | Bright coastal club grounds, finished clubhouse, sculpted rock and strong sea horizon | Island geometry, paths and playable ground |
| 8 Postcards Needle | Elegant narrow island, broad sea color, restrained planting framing the route | Narrow fairway and shoreline |
| 9 Postcards Split | Contrasting island masses, clean water gap, strong green reveal | Split routing and carry options |
| 10 Postcards Crater | Jewel-like volcanic course, cool rock against warm lava | Crater route and hazard edges |
| 12 Island Carry | Limestone cliff, clear blue carry, handsome timber bridge and conifers | Islands, bridge path and carry |
| 13 The Spiral | Pine garden with sweeping mowing bands that describe the spiral | Elevation and shortcut behavior |
| 14 The Witch's Lair | Shaded storybook crater, mossy stone and a clearly revealed recessed green | Entrance, crater rim and pin access |
| 15 The Steps | Clean terraced coastal green with readable tier edges | Every tier and the pin's step |
| 16 Volcano Rim | Ash-and-basalt landscape with a controlled lava river and smoky distant silhouette | Lava penalty boundary |
| 17 Frostbite Fjord | Clear icy blue water, snow-softened rock and winter foliage | Playable sliding ice |
| 18 Mesa Canyon | Warm sandstone strata, quiet dry turf/soil contrast and dramatic existing canyon carry | Both mesas and carry geometry |
| 19 Temple Falls | Jade garden, warm temple stone and a beautiful blue-green waterfall pool | Stone step, bridge and pool hazard |
| 20 Windmill Links | Soft pastoral grass, polished canal banks, tulips and warm timber | Sail motion and collision timing |
| 21 Obsidian Slab | Cool charcoal rock, coral dusk and bright readable lava gaps | Slab obstacles and lava footprint |
| 22 Ember Causeway | Thin emerald route clearly cut through dark rock and orange lava | Narrow winding route |
| 23 Caldera Crown | Broad caldera vista with a strong horseshoe silhouette | Horseshoe and across-lagoon options |
| Meadow 1–3 | Calm parkland with the same finished grass, trees and surface edges | Procedural behavior and existing availability |

Use one memorable landmark or silhouette per hole. Add intentional framing at tee, approach and green viewpoints. The same course must look good while aiming, during ball flight, when putting, and in its overhead preview.

The same app exposes three tennis venues. They also receive a complete visual pass so the broader game retains one quality standard:

| Venue | Visual target | Preserve |
| --- | --- | --- |
| Resort | Finished tropical court, rich but quiet court surface, net/lines, warm clubhouse and lush boundary planting | Court dimensions, line positions, visibility and rally behavior |
| Skyscraper | Clean rooftop court, convincing glass/metal and railings, layered skyline and airy cloud atmosphere | Court/platform bounds, ball visibility against sky and existing fall behavior |
| Volcano | Refined obsidian court, readable ivory lines, cool basalt against controlled lava and warm dusk | Court bounds, lava/fall behavior and ball contrast |

Finish rackets, strings, nets, umpire/spectator props, score overlays, rally feedback and sport-specific camera transitions with the shared material, UI and motion rules. Do not change tennis rules or controls. Enumerate any additional reachable practice venues during phase 0 rather than relying only on the current selection enum.

## 7 Lighting and rendering

Author environment profiles for coastal morning, jungle warmth, volcanic dusk, alpine clarity, desert afternoon and pastoral links. Each profile owns sun direction/color, ambient contribution, reflection data, fog, sky, wind, exposure and grading. Tune the character with the environment rather than illuminating it from an unrelated studio.

Riot's production breakdown demonstrates artist-controlled diffuse gradients, simplified skin response, prefiltered environment reflections, and baked lighting as practical tools for stylized clarity. Adapt those principles to the existing shader families; do not copy their engine-specific texture packing blindly. [Riot shader breakdown](https://www.riotgames.com/en/news/valorant-shaders-and-gameplay-clarity)

Bake static lighting where the scene architecture allows it. Evaluate conventional probes first, then APV on one representative scene if it provides a measured improvement within memory and frame budgets. Unity documents APV in URP, but custom shader paths require deliberate support. The examined character helpers use `SampleSH`; enabling a project checkbox does not establish correct sampling. [Unity URP probe volumes](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/probevolumes.html), [Unity indirect lighting shader methods](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/use-built-in-shader-methods-indirect-lighting.html)

Blizzard's 2025 Overwatch presentation is a useful reference for precomputed probe lighting and reusable lighting scenarios. Treat it as inspiration for controlled baked data, not a requirement to recreate Blizzard's renderer. [Overwatch global illumination presentation](https://enginearchitecture.org/downloads/REAC_2025_Overwatch.pdf)

The project is already configured for linear color. Keep albedo tagged as color and normals/masks as data, validate tangent space and packed channels, and prevent double-applied ambient occlusion or incompatible roughness/smoothness conversions.

Use restrained bloom for lava and glints, subtle grading, stable antialiasing and an appropriate shadow distance. Gameplay should remain sharp. Depth of field is optional for controlled preview shots, subject to device cost and accessibility settings.

SceneKit previews need matching color conversion, roughness/highlight intent, environment lighting and exposure. Export shared material parameters and baked reflection/lighting approximations as needed. Seek perceptual parity with Unity; SceneKit does not run Unity shaders.

## 8 The entire presentation layer

The game world and every surrounding screen receive the same finish.

| Surface | Required visual work |
| --- | --- |
| Launch and loading | Existing brand treatment, attractive background, clean progress state and stable transition into the game |
| Onboarding | Account, character, sport selection, motion primer, connection and existing reward screens; consistent scale and illustration language |
| Home and sport selection | Inviting resort framing, clear primary action, attractive existing sport cards |
| Course selection | Matched course thumbnails, biome color, clear par/difficulty/status and a convincing preview |
| Lobby and party | Characters grounded on a shared stage, consistent lighting, clear ready/watching/host states, refined invite/settings controls |
| Locker and customization | Neutral flattering lighting, larger useful character preview, material parity with gameplay, clear selected colors and controls |
| Gameplay HUD | Smaller stats/minimap, clear wind and lie, accessible controls, gauge away from the character, restrained pin/landing markers |
| Phone controller | Clear aim/power/club controls, useful calibration states, no decorative interference with handling |
| TV or larger display | Dedicated landscape composition, distant readability, controller focus and instruction legend |
| Shot and round results | Clear score hierarchy, deliberate celebration, course context and readable replay/continue actions |
| Settings and help | Same component system, readable toggles, graphics/accessibility choices and motion guidance |
| Multiplayer states | Searching, connecting, ready, spectating, reconnecting, paused, match left, invite and error states |
| Practice and fallback views | Same material/lighting standard wherever reachable; deliberate missing-asset fallback |
| Tennis gameplay and screens | Complete the three venues, existing racket/net materials, score HUD, rally feedback and cameras using the shared quality standard |

Create matching SwiftUI and Unity component tokens for fonts, spacing, radius, icon weight, focus, selection, pressed and disabled states. Preserve existing navigation and real controls.

The generated gameplay HUDs still occupy more space than the final layout should. In code, target roughly 18–22 percent of portrait height for the top information area, with an expandable minimap and a smaller normal play state. Confirm against the smallest supported viewport and safe areas. Keep at least 44-point native touch targets where applicable, useful contrast and readable labels.

Move development connection details into a development-only panel. Long names, localization, larger text, reduced motion and color-vision differences must be tested. Avoid live full-screen blur as the default menu treatment.

## 9 Effects cameras and motion

Finish the full visual feedback chain: aiming arc, predicted landing, strike cue, ball trail, grass/sand/stone contact, water splash, lava response, flag/cup reaction, score badge and celebration.

Use small, purposeful effects with short lifetimes. Contact effects should identify the surface and support timing without hiding the ball. Keep the ball and hazard edges equally understandable across quality tiers.

Give each hole an authored introductory reveal using the existing route and landmark. Refine the address camera, ball-flight handoff, approach, putting, replay and return-to-player transitions. Preserve aiming behavior and motion-controller interpretation. Prevent clipping through vegetation and foreground props. Use a stable camera and reduced-motion alternatives.

World life includes gentle foliage wind, water movement, flag motion, turning windmill sails, small distant sailboats where already appropriate, and brief spectator reactions. Do not replace a readable environment with constant particles or moving distractions.

## 10 How each projection becomes real

| Projection feature | Concrete production path | Cost or limit to check |
| --- | --- | --- |
| Groomed turf | Revise grass albedo/normal frequency, author mowing direction and fringe masks, reuse shared turf shader | Shimmer, mip behavior and surface sampling |
| Sculpted coastal cliff | Blender visual rock modules/skirts, baked normals and one limestone trim/material family | Preserve collision shell and obstacle collection |
| Rich temple planting | A few authored palm/broadleaf variants, shared atlas, instanced clusters and LODs | Generated density is a composition target; reduce hidden foliage and overdraw |
| Pool and shoreline | Existing water geometry plus depth color, normals, foam masks and refined edge meshes | Sorting, shimmer, water blendshapes and hazard boundary |
| Lava and basalt contrast | Broad flow/emission textures, cool rock ambient, restrained bloom and warm underside tint/baked bounce | No real-time GI required; emission must retain scene detail |
| Grounded lobby athletes | Matched camera/light setup, stage floor/contact shadows, correct character scale and aligned perspective | Existing native terrace uses real baked-UV geometry; improve that path and exported textures rather than assuming a photograph backdrop |
| Improved characters | Keep locked meshes, replace/tune material branches, finish maps and deformation | Concept facial variations and accessories are not asset instructions |
| Cleaner HUD | Refactor existing layout/components, reuse minimap data and controls, consistent typography | Actual hit targets and state coverage outweigh concept text accuracy |

GPT Image may reinterpret small geometry or invent a detail. For example, the volcanic concept includes eyewear; it does not authorize adding eyewear to a bareheaded character look. Existing player configuration and locked assets take precedence. Use the concepts to match color, light, material contrast and overall craft.

Riot's map production account supports this sequence: preserve gameplay layouts, dress them with reusable architecture/material systems, and repeatedly judge the result in play. [Riot environment production](https://playvalorant.com/en-gb/news/dev/the-art-of-valorant-map-environments/)

## 11 Production sequence and gates

| Phase | Work | Required exit evidence |
| --- | --- | --- |
| 0 Recover the baseline | Restore compilation against current character APIs; audit reachable Unity/native paths; capture every course and screen | Clean compile, known revision, baseline captures, scene/material inventory and gameplay boundary/obstacle records |
| 1 Establish the visual system | Art bible, palette, shader/material specification, shared skeleton/socket contract, Blender asset kit, import/export rules and UI tokens | Neutral material test scene, rig/deformation proofs and consistent native/Unity characters |
| 2 Complete a representative slice | Hole 12 coastal, hole 21 volcanic, Resort tennis, male/female golf and tennis kits, walk/serve/swing/intro/emote, gameplay HUD, lobby and results | Real in-game stills and motion, contact/cloth checks and initial device measurements |
| 3 Build biome variants | Temple 19, alpine 17, desert 18 and links 20; finish their special materials and landmarks | Each biome works at tee, flight, approach, putt and aerial viewpoints |
| 4 Roll out the catalog | Remaining holes 7–10, 13–16, 22–23, procedural Meadow and all three tennis venues | Coverage matrix has no untreated course/venue or accidental legacy visual path |
| 5 Complete all presentation | Remaining native/Unity screens, controller/TV layouts, transitions, practice/fallback views and visual effects | End-to-end journeys and recordings covering normal, loading, multiplayer and error states |
| 6 Critique optimize and repair | Review real frames, fix weakest views, tune LODs/shadows/textures and verify asset parity | Clean builds, visual proof pack, supported-device performance results and truthful gate report |

Do not roll out a weak pilot to every course. Complete the slice, compare it against these targets, and iterate on the common causes before multiplying the work.

Use checkpoints after each phase and a persistent ledger recording finished assets, remaining defects, test results and the next concrete action. Overnight work can continue across phases until the quality gates pass; the clock should not define completion. A full catalog and presentation overhaul may need several runs and review loops. The first productive overnight milestone is a convincing representative slice plus the reusable system.

Use the swarm described in [Swarm execution plan](swarm-execution-plan.md). One integration owner controls shared contracts, merge order, scene integration and final evaluation. Dedicated workers own character forms, facial performance, rig/deformation, golf clothing, tennis clothing, equipment, golf animation, tennis locomotion/strokes, intros/emotes, environments, rendering, UI, camera/effects and validation. Work runs in dependency waves with separate source files or patch exports.

## 12 Asset pipeline and performance

Keep editable Blender sources, reusable generators, versioned exports, source textures and an asset manifest. A manifest records source file, output mesh, material family, units, pivots, UV/vertex channels, triangle count, LODs, texture formats and collision role.

Blender uses meters; golf runtime applies meters-to-yards scaling in existing paths. Preserve that conversion exactly once. Use stable naming and separate visual decoration from play/collision data. Rebuild affected animation and native exports from the same approved sources.

Prefer existing shader families and shared materials over a unique shader/material per prop. Use property blocks and instancing where appropriate; preserve animated parents such as windmill sails. Default to mipmapped, compressed textures with 512–1024 sizes for most props/surfaces, using higher resolution only when a visible proof justifies it. Preserve the character texture rules.

The previous course plan proposes approximately 300k visible scene triangles, 250 draw calls, and 32 MiB shared plus 8 MiB active-course texture budgets. Treat these as provisional course planning envelopes, not verified device limits or a total-app budget. Characters, UI, render targets, lightmaps, probes and engine memory need separate accounting.

The saved October 6 audits record 93,996–139,476 camera mesh triangles and 55–61 material passes for the three reference holes. Their aggregate editor counters report roughly 529–536 draw calls and 945k–979k triangles; those counters are not a clean phone-frame measurement and must be reconciled against the capture's cameras/passes. Do not assume unused performance headroom.

A separate [Blender construction proof](feasibility/feasibility-results.json) built 46 palms and 44 shrubs at existing markers from two shared replacement meshes, at 720 and 216 triangles respectively. The prototype's evaluated renderable scene has 83,766 triangles. This proves a compact authored plant kit can be built programmatically from the actual source. Its [EEVEE render](feasibility/temple-asset-feasibility.png) is an early asset/composition test, not a finished visual target, Unity integration result or iPhone performance pass.

Select supported devices in phase 0 and measure a repeatable workload after warm-up. Target stable 60 fps where the product supports it, roughly 16.7 ms per frame, while checking CPU/GPU timing, frame spikes, thermal behavior, memory and loading. Establish a deliberate lower quality tier if required. Device validation cannot be inferred from editor statistics.

Start with baked reflections, restrained shadows and the existing water approach. Add APV, extra shadow resolution, more foliage, post-processing or additional effects only when a pilot demonstrates a useful improvement and the device budget allows it.

## 13 Definition of complete

The overhaul is complete when:

- Every reachable golf course, tennis venue and visual screen is recorded in the coverage matrix and meets the shared style, including native previews and fallback states.
- Both locked base characters look appealing under every biome profile, retain identity, and pass face, silhouette, hand and deformation proofs. The upgraded skeleton, sockets, weights and facial controls work in Unity and native previews.
- Existing outfits and equipment retain their configuration and show the intended material differences.
- Tee, approach, green, aerial and actual HUD captures demonstrate finished terrain edges, scenery, water/lava, background and lighting for every hole.
- Gameplay geometry, scoring, lies, hazard boundaries, obstacle collection, windmill timing and tennis court/rally behavior match the baseline; intended visual-only changes are explicitly documented.
- Ball, pin, landing prediction and controls remain readable in the busiest and darkest scenes.
- Onboarding, home, selection, lobby, locker, controller, gameplay, results, settings and multiplayer/error journeys have coherent UI and working navigation.
- Walking, turns, directional runs, all stroke families, serves, golf swings, intros, equipped emotes, idles and reactions have readable weight, contact, face/hand timing and clean transitions on both bodies. Clothing retains volume without visible poke-through.
- New effects and reframed cameras are verified in motion, with reduced-motion and layout/accessibility checks.
- Compilation and relevant regression checks pass. Supported-device performance, memory and loading gates have real measurements.
- Source assets, export scripts, manifests, capture tools and an updated `GATE_RESULTS.md` make the result reproducible.

If a device or build dependency remains unavailable, mark that gate unverified and report the dependency. Do not mark the entire overhaul finished on the strength of concept art or editor stills.

## 14 The execution package

The implementation run should maintain these project deliverables:

1. `VISUAL_OVERHAUL_ART_BIBLE.md` with approved visual rules and material examples.
2. `VISUAL_OVERHAUL_COVERAGE.md` listing every hole, entry point, screen, state and renderer.
3. Shared character/environment material specification and matched native preview parameters.
4. Editable Blender asset kit, exports and asset manifests.
5. Finished course lighting profiles and revised scene dressing.
6. Matching SwiftUI/Unity UI components and screen layouts.
7. Camera, animation and visual feedback pass.
8. Real capture gallery and short motion proofs.
9. Performance measurements and the final `GATE_RESULTS.md`.
10. A concise remaining-defect ledger until every required gate passes.

Project anchors for the implementation audit:

| Work | Existing locations in the game repository |
| --- | --- |
| Golf characters | `Unity/Assets/Scripts/Game/GolferView.cs`, `HeroGolfer.cs`, `GolferStyle.cs` |
| Golf materials | `Unity/Assets/Shaders/GolferClay.shader`, `HeroKit.shader`, `GolfLegacyURP.hlsl` |
| Shared tennis character materials | `Unity/Assets/Resources/Tennis/Shaders/` |
| Tennis characters and motion | `Unity/Assets/Scripts/Tennis/TennisActor.cs`, `TennisHeroSetup.cs`, `HeroTennisDriver.cs`, `HeroFace.cs`, `HeroV6KneeCorrectives.cs` |
| Tennis venues and presentation | `Unity/Assets/Scripts/Tennis/TennisGame.cs`, `TennisLook.cs`, `TennisEnvironmentV4.cs`, `TennisVenue.cs`, `TennisVenueBuilder*.cs`, `TennisPresentation.cs` |
| Shared native motion | `GolfArcade/Unity/MatchHeroMotion.swift` and its exported bone tracks/inverse-bind data |
| Course visuals | `Unity/Assets/Scripts/Course/GolfLook.cs`, `GolfCourseLook.cs`, `GolfCourseAtmosphere.cs`, `HoleView.cs` and related surface/foliage/backdrop helpers |
| Course definitions | `Unity/Assets/Scripts/Course/Hole.cs` |
| Unity presentation | `Unity/Assets/Scripts/UI/` and `Game/CameraRig.cs` |
| Native presentation | `GolfArcade/Unity/IslandKit.swift`, `MotionClubMenus.swift`, `ClubEnvironmentView.swift`, `MatchHeroSurfaces.swift`, `Features/` and `Onboarding/` |
| Blender production | `blender/scripts/course_builder.py`, `course_extras.py`, individual hole scripts and existing character/export scripts |
| Proof capture | `Unity/Assets/Editor/GolfCourseStandardCapture.cs`, `GolfFlyoverCapture.cs` and native snapshot/flow tests |
| Character constraints | `AGENTS.md`, `PLAN_HeroBase_MaleFemale_Lock.md`, `ArtDir/hero/HERO.md` and approved base plates |

The repository is at `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator`.

For the earlier company-specific technical research, see [Game visuals technical research](technical-research.md). Exact environment prompts are in [Image prompts](image-prompts.md); character prompts are in [Character clothing and motion prompts](character-clothing-motion-prompts.md).
