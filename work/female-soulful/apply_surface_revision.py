"""Apply the reviewed female-only shader branch in the disposable Unity project."""
from pathlib import Path
p=Path('/private/tmp/female-soulful-UnityClone/Assets/Resources/Tennis/Shaders')
s=(p/'HeroLighting.hlsl').read_text();s=s.replace('return _HeroLightingEnabled > .5h && skinFinish > .5h ? HeroHighlightRoll(c,.35h,.75h)*_HeroSkinLightExposure : c;','''if (_HeroLightingEnabled > .5h && skinFinish > 1.5h)
        return HeroHighlightRoll(c,.60h,.90h)*_HeroSkinLightExposure;
    return _HeroLightingEnabled > .5h && skinFinish > .5h ? HeroHighlightRoll(c,.35h,.75h)*_HeroSkinLightExposure : c;''')
func='''
// Female athlete: clean diffuse form with a restrained satin lobe and a warm
// terminator. No extra light, screen pass, pore texture or fixed skin-tone paint.
half3 HeroFemaleSkinShade(Light light, half3 n, half3 v, half3 albedo, half smoothness, out half3 reflection)
{
    half ndl=dot(n,light.direction), nl=saturate(ndl);
    half wrapped=saturate((ndl+.26h)/1.26h);
    half nh=saturate(dot(n,SafeNormalize(light.direction+v)));
    half lobe=pow(nh,12+smoothness*12)*.035h+pow(nh,32+smoothness*24)*.018h;
    half visibility=smoothstep(-.04h,.28h,ndl);
    half attenuation=light.distanceAttenuation*lerp(light.shadowAttenuation,1,.08h);
    reflection=lobe*.65h*visibility*light.color*attenuation;
    half3 diffuse=wrapped*.88h+half3(.30h,.12h,.08h)*saturate(wrapped-nl);
    return albedo*diffuse*light.color*attenuation+reflection;
}
'''
s=s.replace('\n#endif',func+'\n#endif') if '\n// Female athlete:' not in s else s
# This file has only its terminal include guard.
assert s.count('half3 HeroFemaleSkinShade(')==1
(p/'HeroLighting.hlsl').write_text(s)
s=(p/'HeroFaceSkin.shader').read_text();needle='''                half3 previousReflection;
                half3 previous = HeroSkinShade''';s=s.replace(needle,'''                if (_SkinFinish > 1.5h) return HeroFemaleSkinShade(light,n,v,albedo,smoothness,reflection);
                half3 previousReflection;
                half3 previous = HeroSkinShade''')
s=s.replace('half3(1.08h,1.09h,1.04h),faceAmount)','half3(1.0h,1.0h,1.0h),faceAmount)')
s=s.replace('if (_SkinFinish > .5h && _FaceRole < .5h) {','if (_SkinFinish > .5h && _SkinFinish < 1.5h && _FaceRole < .5h) {')
s=s.replace('ambient *= lerp(.82h,.97h,faceAmount) * half3(1.0h,.86h,.72h);','ambient *= _SkinFinish > 1.5h ? lerp(.86h,.94h,faceAmount)*half3(1.0h,.98h,.97h) : lerp(.82h,.97h,faceAmount)*half3(1.0h,.86h,.72h);')
s=s.replace('ambient+=c.rgb*half3(.17h,.13h,.11h)*noseUnderside;','ambient+=c.rgb*(_SkinFinish>1.5h?half3(.08h,.035h,.025h):half3(.17h,.13h,.11h))*noseUnderside;')
(p/'HeroFaceSkin.shader').write_text(s)
s=(p/'TennisCloth.shader').read_text().replace('if (_UseGarmentMaps < .5h) { smoothness = _Smoothness; sheen = _SheenStrength; }','''if (_UseGarmentMaps < .5h) { smoothness = _Smoothness; sheen = _SheenStrength; }
                else if (_FabricVersion > 2.5h) { smoothness *= .80h; sheen *= .65h; }''')
s=s.replace('albedo *= lerp(.40h, 1, mask.g);','albedo *= lerp(_FabricVersion>2.5h?.72h:.40h, 1, mask.g);')
(p/'TennisCloth.shader').write_text(s)
print('Female skin and cloth shader branches written')
