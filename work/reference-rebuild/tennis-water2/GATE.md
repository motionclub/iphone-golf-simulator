# Resort water2 actual gate

GATE: Unity compile PASS, matching root captures exist with no shader or C# errors.

GATE: Fragment fog restoration PASS. Matching reference16 actual/control comparison clearly changes the offshore plane from washed grey-blue to stronger blue. The source ocean is an8-vertex2400×1500m surface, and evaluating fog per fragment fixes interpolation of clamped corner depth values. Numerical region samples are preserved in manifest.json.

GATE: Reference visual quality PARTIAL / wave alias FAIL. Distant left-ocean horizontal stairs remain visible in actual16. Target shows broader sun shimmer and more varied calm color. Water3 isolates a derivative-filtered wave correction first; fog/palette/highlight strength remain unchanged. No global post adoption and no full reference match claim.
