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
half3 HeroFinish(half3 c)
{
    if (_HeroProfile < .5) return c;
    c *= _HeroExposure;
    half peak=max(max(c.r,c.g),max(c.b,1e-4h));
    half span=max(_HeroShoulderCeiling-_HeroShoulderKnee,.001h);
    half rolled=peak<=_HeroShoulderKnee ? peak : _HeroShoulderKnee+span*(1-exp(-(peak-_HeroShoulderKnee)/span));
    return c*(rolled/peak);
}
half HeroWrapped(half3 n,half3 direction,half wrap)
{ return saturate((dot(n,direction)+wrap)/(1+wrap)); }
'''
char=(B/(S+'TennisCharacter.shader')).read_text()
fn,char=extract(char,'half3 Shade (Light light, half3 n, half3 v, half3 albedo)')
fn=fn.replace('half3 Shade (Light light, half3 n, half3 v, half3 albedo)',
              'half3 HeroCharacterShade (Light light, half3 n, half3 v, half3 albedo, half _Wrap, half _Smoothness, half3 _Subsurface)')
fn=fn.replace('_Subsurface.rgb','_Subsurface')
lighting+=fn+'\n#endif\n'
char=char.replace('#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"',
                  '#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"\n            #include "HeroLighting.hlsl"')
char=char.replace('Shade(main, n, v, c.rgb)','HeroCharacterShade(main, n, v, c.rgb, _Wrap, _Smoothness, _Subsurface.rgb)')
char=char.replace('Shade(extra, n, v, c.rgb)','HeroCharacterShade(extra, n, v, c.rgb, _Wrap, _Smoothness, _Subsurface.rgb)')
char=char.replace('Light main = GetMainLight(TransformWorldToShadowCoord(i.positionWS));','Light main = HeroMain(GetMainLight(TransformWorldToShadowCoord(i.positionWS)));')
char=char.replace('SampleSH(n) * c.rgb','HeroAmbient(n) * c.rgb')
char=char.replace('MixFog(colour, i.fog)','MixFog(HeroFinish(colour), i.fog)')
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
cloth=cloth.replace('#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"',
                    '#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"\n            #include "HeroLighting.hlsl"\n            #include "HeroCloth.hlsl"')
cloth=cloth.replace('Light main = GetMainLight();','Light main = HeroMain(GetMainLight());')
cloth=cloth.replace('SampleSH(n) * albedo * ao','HeroAmbient(n) * albedo * ao')
cloth=cloth.replace('MixFog(colour, i.fog)','MixFog(HeroFinish(colour), i.fog)')
for name,s in [('HeroLighting.hlsl',lighting),('HeroCloth.hlsl',core),('TennisCharacter.shader',char),('TennisFace.shader',face),('TennisCloth.shader',cloth)]:
    write(S+name,s)
(W/'data/shared_core_candidate.json').write_text(json.dumps({'source':'frozen post-cloth baseline','installed':False,
    'files':[S+n for n in ['HeroLighting.hlsl','HeroCloth.hlsl','TennisCharacter.shader','TennisFace.shader','TennisCloth.shader']],
    'tennis':'same original math through profile 0; requires fresh image diffs, not certified by source inspection'},indent=2)+'\n')
print('Shared shader candidate prepared; no live install')
