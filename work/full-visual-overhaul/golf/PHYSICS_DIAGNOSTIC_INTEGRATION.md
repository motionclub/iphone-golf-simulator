# Opt-in runtime contract for all 19 course routes

Installed in checkpoint 9: Unity/Assets/Scripts/Course/GolfVisualPhysicsGate.cs with UNITY_EDITOR-only hooks in GolfCourseLook. Root must compile and execute; no runtime PASS is inferred from installation. The entire diagnostic is wrapped in UNITY_EDITOR; it changes no game data and contributes no player code.

GolfCourseLook.FinishModel captures a token at entry, immediately before GolfLandmarkFinish.Apply, then ends it after GolfPlantInstances.Apply. DressProcedural begins before material assignment and ends immediately after GolfResortDress.Apply. Both hooks are wrapped in UNITY_EDITOR.

```csharp
#if UNITY_EDITOR
var physicsToken = GolfVisualPhysicsGate.Begin(model,hole); // root in DressProcedural
#endif
// existing visual work
#if UNITY_EDITOR
GolfVisualPhysicsGate.End(physicsToken,model,hole); // root in DressProcedural
#endif
```

Set GolfVisualPhysicsGate.Enabled=true and clear Reports before capture, or set GOLF_VISUAL_PHYSICS_GATE=1 in the editor process. After each HoleView.Build returns, export Reports[hole.Number] with JsonUtility.ToJson(report,true) to holeNN_dressing_physics.json. Keep the original HEAD pilot hash comparisons alongside these records.

The diagnostic hashes full original MeshCollider vertex/index/submesh data and exact world matrices before/after, collider identity/type/enabled/active/trigger/contact/material/primitive-shape state, obstacle structs, complete HeightGrid private values or Contours features, surface height/gradient samples and actual ground rays. It checks that original ground MeshFilters retain the same source mesh references and new visual mesh filters do not reuse collision source meshes. Ground/surface/obstacle/windmill references must remain intact. Every record includes raw before/after collider contracts and binary gates; no screenshot count is interpreted as completion.

Synchronous source byte equality and this runtime contract complement each other. The source HEAD audit proves canonical FBX/blend/core code preservation; this contract proves the visual finishing step preserves the actual imported physics in that process. Root must compile and execute the staged diagnostic before claiming PASS. Disabled diagnostic performs no capture work.
