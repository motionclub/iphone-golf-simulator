#!/usr/bin/env python3
"""Majestic weather (chat W): the shared-file edits, for chat 6 (integration) or a clone.

  patch_shared.py apply  <Unity dir>   # idempotent
  patch_shared.py remove <Unity dir>   # exact rollback of what apply added
  patch_shared.py check  <Unity dir>   # exit 0 if fully applied, 1 if not, 2 if half-applied

Edits (every inserted line carries the marker MAJESTIC_WEATHER_HOOK):
1. Resources/Environment/Shaders/EnvironmentSurface.hlsl: include Majestic/MajesticWeather.hlsl and route
   EnvironmentFog / EnvironmentBackdrop / EnvironmentTurfWeather through it while _MajWeatherOn > .5.
   With the layer off the original code runs unchanged.
2. Scripts/Course/RoundEvents.cs, Weathers.SkyOf: holes 10 and 16 (Magma Open) draw the ash family
   (Ashfall / Eruption / Volcanic Smoke) - Adnan's decision 10-17 (PLAN.md 4.5 #1).
3. Course/Shaders/GolfRock.shader, Course/Shaders/GolfBotanical.shader, Environment/LuminousCoast/CoastalPine.shader:
   include MajesticWeather.hlsl and end in MajesticWeatherMixFog(...) instead of MixFog(...) (== MixFog when off),
   so rocks, bushes and pines get wet, snow / ash on top and the weather's fog too.
4. Resources/Majestic/MajesticWeatherHook.txt (+ .meta): the marker that wakes the weather layer
   (MajesticWeather.ShadersReady); without it the layer stays dormant and WeatherView draws as before.
"""
import os, sys

MARK = "MAJESTIC_WEATHER_HOOK"
HOOK_GUID = "6d1f0a3c9b7e4c2a8f5e1d0b7a9c3e21"

SURFACE = "Assets/Resources/Environment/Shaders/EnvironmentSurface.hlsl"
ROUND = "Assets/Scripts/Course/RoundEvents.cs"
MARKER = "Assets/Resources/Majestic/MajesticWeatherHook.txt"
OLD_INC = "#include \"Assets/Resources/Majestic/MajesticWeather.hlsl\" // " + MARK + "\n"
INC = "#define MAJESTIC_WEATHER_LITE 1 // " + MARK + " (no extra texture in these shaders)\n#include \"Assets/Resources/Majestic/MajesticWeather.hlsl\" // " + MARK + "\n"
# (file, [(anchor, replacement)]): replacement contains the anchor's new form; remove() swaps back
SHADERS = [
    ("Assets/Resources/Course/Shaders/GolfRock.shader", [
        ('#include "../../Tennis/Shaders/HeroLighting.hlsl"\n', '#include "../../Tennis/Shaders/HeroLighting.hlsl"\n' + INC),
        (' return half4(MixFog(colour,i.fog),1);\n', ' return half4(MajesticWeatherMixFog(colour,i.fog,i.w),1); // ' + MARK + '\n')]),
    ("Assets/Resources/Course/Shaders/GolfBotanical.shader", [
        ('  #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"\n', '  #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"\n' + INC),
        ('    return half4(MixFog(c,InitializeInputDataFog(float4(i.w,1),0)),1);\n', '    return half4(MajesticWeatherMixFog(c,InitializeInputDataFog(float4(i.w,1),0),i.w),1); // ' + MARK + '\n')]),
    ("Assets/Resources/Course/Shaders/GolfOcean.shader", [
        ('    return half4(EnvironmentFog(colour*lerp(half3(1,1,1),half3(.35,.55,.75),_DreamNight),fog,i.w),1);\n',
         '    return half4(EnvironmentFog(MajesticWeatherWater(colour*lerp(half3(1,1,1),half3(.35,.55,.75),_DreamNight)),fog,i.w),1); // ' + MARK + '\n')]),
    ("Assets/Resources/Environment/LuminousCoast/CoastalPine.shader", [
        ('  #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"\n', '  #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"\n' + INC),
        ('    return half4(MixFog(color,i.fog),1);\n', '    return half4(MajesticWeatherMixFog(color,i.fog,i.w),1); // ' + MARK + '\n')]),
]

SURFACE_EDITS = [
    # (anchor, inserted text, where: 'after' | 'before'). Everything inserted only exists in the MAJESTIC_WEATHER_ON
    # variant; without the keyword the file compiles to its original code.
    ("half _EnvironmentWetness, _EnvironmentSnow, _EnvironmentStorm;\n",
     "// " + MARK + " (chat W, work/majestic-weather): weather inside the world materials, in the MAJESTIC_WEATHER_ON variant only.\n"
     "#include \"Assets/Resources/Majestic/MajesticWeather.hlsl\"\n", "after"),
    ("half3 EnvironmentFog(half3 color,half fogFactor,float3 world)\n",
     "#if defined(MAJESTIC_WEATHER_ON) // " + MARK + ": the venue's own fog amount, composed by max with the weather's\n"
     "half MajesticVenueFogAmount(half fogFactor,float3 world)\n"
     "{\n"
     "    half venueAmount=MajesticVenueFog(fogFactor);\n"
     "    return _EnvironmentDepthEnabled>.5h?max(venueAmount,EnvironmentLayerAmount(world)):venueAmount;\n"
     "}\n"
     "#endif\n", "before"),
    ("    if(_EnvironmentDepthEnabled<.5h)return MixFog(color,fogFactor);\n",
     "    #if defined(MAJESTIC_WEATHER_ON) // " + MARK + "\n"
     "    if(_MajWeatherOn>.5h)return MajesticWeatherFinish(color,world,MajesticVenueFogAmount(fogFactor,world),unity_FogColor.rgb);\n"
     "    #endif\n", "before"),
    ("    return _EnvironmentDepthEnabled>.5h ? lerp(color,_EnvironmentHazeColor.rgb,EnvironmentLayerAmount(world)) : color;\n",
     "    #if defined(MAJESTIC_WEATHER_ON) // " + MARK + "\n"
     "    if(_MajWeatherOn>.5h)color=MajesticWeatherBackdrop(color,world);\n"
     "    #endif\n", "before"),
    ("    half wet=_EnvironmentWetness*_EnvironmentWeatherEnabled;\n",
     "    #if defined(MAJESTIC_WEATHER_ON) // " + MARK + "\n"
     "    if(_MajWeatherOn>.5h)return MajesticWeatherTurf(color);\n"
     "    #endif\n", "before"),
]
# the keyword, once per world shader's forward pass (fragment stage only); hub shaders have no weather and stay single-variant
PRAGMA = "   #pragma multi_compile_fragment _ MAJESTIC_WEATHER_ON // " + MARK + "\n"
KEYWORD_SHADERS = [
    ("Assets/Resources/Course/Shaders/GolfGround.shader", "#pragma multi_compile_fog\n"),
    ("Assets/Resources/Course/Shaders/GolfLava.shader", "            #pragma multi_compile_fog\n"),
    ("Assets/Resources/Course/Shaders/GolfOcean.shader", "   #pragma multi_compile_fog\n"),
    ("Assets/Resources/Course/Shaders/GolfCoastalFoliage.shader", "   #pragma multi_compile_fog\n"),
    ("Assets/Resources/Course/Shaders/GolfRock.shader", "#pragma multi_compile_fog\n"),
    ("Assets/Resources/Course/Shaders/GolfBotanical.shader", "   #pragma multi_compile_fog\n"),
    ("Assets/Resources/Environment/LuminousCoast/CoastalPine.shader", "   #pragma multi_compile_fog\n"),
    ("Assets/Resources/Tennis/Shaders/TennisWorldSurface.shader", "            #pragma multi_compile_fog\n"),
    ("Assets/Resources/Tennis/Shaders/TennisHorizon2.shader", "            #pragma multi_compile_fog\n"),
    ("Assets/Resources/Tennis/Shaders/TennisBotanical.shader", "   #pragma multi_compile_fog\n"),
    ("Assets/Resources/Course/Shaders/GolfDistantLand.shader", "   #pragma fragment frag\n"),
]

SKYOF_OLD = "            : hole.Theme == \"magma\" ? Sky.Ash\n"
SKYOF_NEW = ("            // " + MARK + ": Adnan 10-17 (majestic-all-maps PLAN 4.5 #1): the Magma Open's holes 10 and 16 draw the ash family.\n"
             "            : hole.Theme == \"magma\" || hole.Number == 10 || hole.Number == 16 ? Sky.Ash\n")


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def state(root):
    s = read(os.path.join(root, SURFACE)); r = read(os.path.join(root, ROUND))
    parts = [all(ins in s for _, ins, _ in SURFACE_EDITS), SKYOF_NEW in r, os.path.exists(os.path.join(root, MARKER))]
    for f, edits in SHADERS:
        t = read(os.path.join(root, f)); parts.append(all(new in t for _, new in edits))
    parts.append(all(PRAGMA in read(os.path.join(root, f)) for f, _ in KEYWORD_SHADERS))
    return parts


def apply(root):
    p = os.path.join(root, SURFACE); s = read(p)
    for anchor, ins, where in SURFACE_EDITS:
        if ins in s:
            continue
        if s.count(anchor) != 1:
            sys.exit(f"anchor not found exactly once in {SURFACE}: {anchor.strip()!r}")
        s = s.replace(anchor, anchor + ins if where == "after" else ins + anchor)
    write(p, s)
    p = os.path.join(root, ROUND); r = read(p)
    if SKYOF_NEW not in r:
        if r.count(SKYOF_OLD) != 1:
            sys.exit(f"Weathers.SkyOf anchor not found in {ROUND}")
        r = r.replace(SKYOF_OLD, SKYOF_NEW)
        write(p, r)
    for f, edits in SHADERS:
        fp = os.path.join(root, f); t = read(fp)
        for old, new in edits:
            if new in t:
                continue
            if t.count(old) != 1:
                sys.exit(f"anchor not found exactly once in {f}: {old.strip()!r}")
            t = t.replace(old, new)
        write(fp, t)
    for f, anchor in KEYWORD_SHADERS:
        fp = os.path.join(root, f); t = read(fp)
        if PRAGMA in t:
            continue
        if t.count(anchor) != 1:
            sys.exit(f"pragma anchor not found exactly once in {f}")
        write(fp, t.replace(anchor, anchor + PRAGMA))
    m = os.path.join(root, MARKER)
    os.makedirs(os.path.dirname(m), exist_ok=True)
    write(m, "Majestic weather shader hook installed (work/majestic-weather/tools/patch_shared.py).\n")
    write(m + ".meta", f"fileFormatVersion: 2\nguid: {HOOK_GUID}\nTextScriptImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n")
    print("applied", state(root))


def remove(root):
    p = os.path.join(root, SURFACE); s = read(p)
    for anchor, ins, where in SURFACE_EDITS:
        s = s.replace(ins, "")
    write(p, s)
    p = os.path.join(root, ROUND); r = read(p)
    write(p, r.replace(SKYOF_NEW, SKYOF_OLD))
    for f, edits in SHADERS:
        fp = os.path.join(root, f); t = read(fp)
        for old, new in edits:
            t = t.replace(new, old)
        t = t.replace(OLD_INC, "")   # the first version's include line (no LITE define)
        write(fp, t)
    for f, _ in KEYWORD_SHADERS:
        fp = os.path.join(root, f); write(fp, read(fp).replace(PRAGMA, ""))
    for f in (os.path.join(root, MARKER), os.path.join(root, MARKER) + ".meta"):
        if os.path.exists(f):
            os.remove(f)
    print("removed", state(root))


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("apply", "remove", "check"):
        sys.exit(__doc__)
    root = os.path.abspath(sys.argv[2])
    if sys.argv[1] == "apply":
        apply(root)
    elif sys.argv[1] == "remove":
        remove(root)
    else:
        st = state(root); print(st); sys.exit(0 if all(st) else 1 if not any(st) else 2)
