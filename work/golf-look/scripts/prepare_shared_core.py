"""Prepare shared shader candidates from frozen post-cloth source; no live install."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parents[1];B=W/'inputs/post_cloth';C=W/'candidate'
S='Unity/Assets/Resources/Tennis/Shaders/'
def write(rel,s):
    p=C/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
def extract(s,signature):
    start=s.index(signature);a=s.index('{',start);depth=1;i=a+1
    while depth:
        if s[i]=='{':depth+=1
        elif s[i]=='}':depth-=1
        i+=1
    return s[start:i],s[:start]+s[i:]
lighting='''#ifndef GOLF_ARCADE_HERO_LIGHTING_INCLUDED
#define GOLF_ARCADE_HERO_LIGHTING_INCLUDED
// Profile 0 is the unchanged tennis lighting path. Golf uses the same surface
// functions, actual course lights/shadows and a hue-preserving highlight knee.
float _HeroProfile;
half4 _HeroKeyColor, _HeroAmbientSky, _HeroAmbientEquator, _HeroAmbientGround;
half _HeroKeyStrength, _HeroRim, _HeroExposure, _HeroShoulderKnee, _HeroShoulderCeiling;
half3 _HeroClothBalance;
half _HeroClothExposure;
Light HeroMain(Light light)
{
    if (_HeroProfile > .5) light.color = _HeroKeyColor.rgb * _HeroKeyStrength;
    return light;
}
half3 HeroAmbient(half3 n)
{
    if (_HeroProfile < .5) return SampleSH(n);
    return n.y >= 0 ? lerp(_HeroAmbientEquator.rgb,_HeroAmbientSky.rgb,saturate(n.y))
                    : lerp(_HeroAmbientEquator.rgb,_HeroAmbientGround.rgb,saturate(-n.y));
}
half3 HeroHighlightRoll(half3 c,half knee,half ceiling)
{
    half peak=max(max(c.r,c.g),max(c.b,1e-4h));
    half span=max(ceiling-knee,.001h);
    half excess=max(peak-knee,0);
    // A late rational shoulder preserves highlight contrast instead of rapidly
    // flattening every bright surface to a single value.
    half rolled=peak<=knee ? peak : knee+span*excess/(span+excess);
    return c*(rolled/peak);
}
half3 HeroFinish(half3 c)
{
    if (_HeroProfile < .5) return c;
    return HeroHighlightRoll(c*_HeroExposure,_HeroShoulderKnee,_HeroShoulderCeiling);
}
half3 HeroClothFinish(half3 c)
{
    if (_HeroProfile < .5) return c;
    return HeroHighlightRoll(c*.88h,.60h,.82h);
}
half3 HeroCharacterFinish(half3 c,half3 reflection)
{
    if (_HeroProfile < .5) return c;
    half3 base=HeroHighlightRoll(max(c-reflection,0)*.95h,.70h,.90h);
    half3 room=max(.985h-base,.001h);
    // Retain the authored specular/rim shape after diffuse highlight handling.
    // Each channel approaches its remaining display headroom without clipping.
    reflection=max(reflection,0);
    return base+reflection*room/(room+reflection);
}
half HeroWrapped(half3 n,half3 direction,half wrap)
{ return saturate((dot(n,direction)+wrap)/(1+wrap)); }
'''
char=(B/(S+'TennisCharacter.shader')).read_text()
fn,char=extract(char,'half3 Shade (Light light, half3 n, half3 v, half3 albedo)')
fn=fn.replace('half3 Shade (Light light, half3 n, half3 v, half3 albedo)',
              'half3 HeroCharacterShade (Light light, half3 n, half3 v, half3 albedo, half _Wrap, half _Smoothness, half3 _Subsurface, out half3 reflection)')
fn=fn.replace('_Subsurface.rgb','_Subsurface')
fn=fn.replace('return (albedo * wrapped', 'reflection=spec*light.color*atten;\n                return (albedo * wrapped')
lighting+=fn+'\n#endif\n'
char=char.replace('#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"',
                  '#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"\n            #include "HeroLighting.hlsl"')
char=char.replace('half3 colour = Shade(main, n, v, c.rgb);','half3 reflection;\n                half3 colour = HeroCharacterShade(main, n, v, c.rgb, _Wrap, _Smoothness, _Subsurface.rgb, reflection);')
char=char.replace('colour += Shade(extra, n, v, c.rgb);','half3 extraReflection;\n                    colour += HeroCharacterShade(extra, n, v, c.rgb, _Wrap, _Smoothness, _Subsurface.rgb, extraReflection);\n                    reflection += extraReflection;')
char=char.replace('Light main = GetMainLight(TransformWorldToShadowCoord(i.positionWS));','Light main = HeroMain(GetMainLight(TransformWorldToShadowCoord(i.positionWS)));')
char=char.replace('SampleSH(n) * c.rgb','HeroAmbient(n) * c.rgb')
char=char.replace('colour *= ao.directAmbientOcclusion;','colour *= ao.directAmbientOcclusion; reflection *= ao.directAmbientOcclusion;')
char=char.replace('colour += ambient + _RimColor.rgb * rim * (0.35 + 0.65 * c.rgb) * main.color;', 'half3 rimLight = _RimColor.rgb * rim * (0.35 + 0.65 * c.rgb) * main.color;\n                colour += ambient + rimLight; reflection += rimLight;')
char=char.replace('MixFog(colour, i.fog)','MixFog(HeroCharacterFinish(colour, reflection), i.fog)')
char=char.replace('pow(1 - saturate(dot(v, n)), _RimPower) * _RimStrength',
                  'pow(1 - saturate(dot(v, n)), _RimPower) * _RimStrength * (_HeroProfile > .5h ? _HeroRim : 1)')
face=(B/(S+'TennisFace.shader')).read_text()
face=face.replace('#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"',
                  '#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"\n            #include "HeroLighting.hlsl"')
face=face.replace('Light main = GetMainLight(TransformWorldToShadowCoord(i.positionWS));','Light main = HeroMain(GetMainLight(TransformWorldToShadowCoord(i.positionWS)));')
face=face.replace('saturate((dot(n, main.direction) + _Wrap) / (1 + _Wrap))','HeroWrapped(n, main.direction, _Wrap)')
face=face.replace('SampleSH(n)','HeroAmbient(n)').replace('MixFog(lit, i.fog)','MixFog(HeroFinish(lit), i.fog)')
cloth=(B/(S+'TennisCloth.shader')).read_text();core='''#ifndef GOLF_ARCADE_HERO_CLOTH_INCLUDED
#define GOLF_ARCADE_HERO_CLOTH_INCLUDED
// Shared cloth surface core. v1 map bytes and the tennis branch stay unchanged.
'''
for signature in ['half ClothShadow(float3 world)','half3 Shade(Light light, half3 n, half3 v, half3 albedo, half smoothness, half sheenStrength, half ao)',
                  'void Fabric(half id, out half smoothness, out half sheen, out half knit, out float2 quadrant, out half frequency)',
                  'half3 SoftShoulder (half3 c)']:
    fn,cloth=extract(cloth,signature);core+=fn+'\n'
core+='\n#endif\n'
core=core.replace('else if (id > 4.5h) { smoothness = .10h; sheen = .18h; knit = 0; quadrant = float2(1,0); }', '''else if (id > 4.5h) { smoothness = .10h; sheen = .18h; knit = 0; quadrant = float2(1,0); }
                // Version 2 extends the decoder. Version 1 keeps its six IDs and bytes.
                if (_FabricVersion > 1.5h && id > 5.5h) {
                    if (id < 6.5h) { smoothness=.09h;sheen=.24h;knit=0;quadrant=float2(0,0);frequency=8; }
                    else if (id < 7.5h) { smoothness=.12h;sheen=.32h;knit=1;quadrant=float2(1,0);frequency=10; }
                    else if (id < 8.5h) { smoothness=.18h;sheen=.10h;knit=0;quadrant=float2(0,1);frequency=8; }
                    else { smoothness=.08h;sheen=.18h;knit=0;quadrant=float2(1,1);frequency=8; }
                }''')
cloth=cloth.replace('_UseGarmentMaps ("Use garment construction", Float) = 0','_UseGarmentMaps ("Use garment construction", Float) = 0\n        _FabricVersion ("Fabric encoding: 1 tennis, 2 golf", Float) = 1')
cloth=cloth.replace('half _UseGarmentMaps, _NormalStrength, _AOStrength;','half _UseGarmentMaps, _NormalStrength, _AOStrength;\n                half _FabricVersion;')
cloth=cloth.replace('floor(mask.a * 5 + .5h)','floor(mask.a * (_FabricVersion > 1.5h ? 9 : 5) + .5h)')
cloth=cloth.replace('#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"',
                    '#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"\n            #include "HeroLighting.hlsl"\n            #include "HeroCloth.hlsl"')
cloth=cloth.replace('Light main = GetMainLight();','Light main = HeroMain(GetMainLight());')
cloth=cloth.replace('SampleSH(n) * albedo * ao','HeroAmbient(n) * albedo * ao')
cloth=cloth.replace('MixFog(colour, i.fog)','MixFog(HeroClothFinish(colour), i.fog)')
cloth=cloth.replace('half rim = pow(1 - ndv, _RimPower) * _RimStrength;',
                    'half rim = pow(1 - ndv, _RimPower) * _RimStrength * (_HeroProfile > .5h ? _HeroRim : 1);')
cloth=cloth.replace('colour = SoftShoulder(colour * _Exposure) * lerp(.68h, 1, aoVisibility) * lerp(.75h, 1, mask.g);', '''if (_HeroProfile > .5h) {
                    // Neutral construction maps retain the palette under warm postcard keys.
                    // A cloth exposure controls white reflectance; trim keeps its measured dark value.
                    half neutralWhite = smoothstep(.4h,.8h,dot(albedo,half3(.2126h,.7152h,.0722h)));
                    half clothGain = lerp(min(_HeroClothExposure,3),_HeroClothExposure,neutralWhite);
                    colour *= _HeroClothBalance * lerp(clothGain, 1, mask.b);
                    colour *= lerp(.68h, 1, aoVisibility) * lerp(.75h, 1, mask.g);
                    colour = max(colour, albedo * lerp(.35h,4.0h,mask.b));
                } else {
                    colour = SoftShoulder(colour * _Exposure) * lerp(.68h, 1, aoVisibility) * lerp(.75h, 1, mask.g);
                }''')
for name,s in [('HeroLighting.hlsl',lighting),('HeroCloth.hlsl',core),('TennisCharacter.shader',char),('TennisFace.shader',face),('TennisCloth.shader',cloth)]:
    write(S+name,s)
(W/'data/shared_core_candidate.json').write_text(json.dumps({'source':'frozen post-cloth baseline','installed':False,
    'files':[S+n for n in ['HeroLighting.hlsl','HeroCloth.hlsl','TennisCharacter.shader','TennisFace.shader','TennisCloth.shader']],
    'tennis':'same original math through profile 0; requires fresh image diffs, not certified by source inspection'},indent=2)+'\n')
print('Shared shader candidate prepared; no live install')
