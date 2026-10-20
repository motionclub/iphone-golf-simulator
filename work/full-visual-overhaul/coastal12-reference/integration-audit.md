# Reference Coastal12 integration audit

Read-only source review before first combined actual render.

1. ReferenceCliff02_N.exr.meta currently uses TextureImporter textureType0, sRGBTexture1. GolfRock _AuthoredUV decodes this through UnpackNormal; import as textureType1 / sRGBTexture0 with GL green convention.
2. GolfCoastalComposition.Model transforms Shore/Islets existing vertices only. Polygon edges crossing source-meter Y8,60,110 require inserted crossing vertices before warp. Source Shore edge (54.3,103.2)->(57.4,52.8) has expected transformed D15.307182yd at X56.612562, but current edge D32.541789yd:17.234607yd boundary disagreement.
3. ProjectSetup.RuntimeShaders lacks GolfArcade/GolfCoastalTurf. Parent has authorized the minimal whitelist addition after source freeze releases.

Source checks otherwise: ReferenceHole12 selected before BuildFromModel collider/ObstacleScan extraction; TEE/PIN unchanged; bunker metadata all lies beyond warp110m; scanned mesh UV0 retained by template.copy; tangent handedness corrected with GetOddNegativeScale in GolfSurface.hlsl. Actual visual, ground scoring, and budget approval still pending.
