from pathlib import Path
R=Path(__file__).resolve().parents[3]
p=R/'Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader'
s=p.read_text().replace('// Soft-toy look from the art targets: wrapped diffuse so light bleeds gently past the\n// terminator, a warm subsurface tint in that transition, a restrained specular, a rim that\n// separates the silhouette from the court, and screen-space AO where limbs meet the body.','// Resort athlete surface: scene lighting describes the form; skin, eyes and equipment\n// have distinct controlled highlights. The approved geometry and paint remain intact.')
s=s.replace('_Saturation ("Saturation", Range(0,1.5)) = 0.82','_Saturation ("Saturation", Range(0,1.5)) = 0.96')
s=s.replace('_Smoothness ("Smoothness", Range(0,1)) = 0.2','_Smoothness ("Smoothness", Range(0,1)) = 0.28\n        _SpecularStrength ("Surface highlight strength", Range(0,2)) = 1\n        _EnvironmentStrength ("Scene reflection strength", Range(0,1)) = 0.12')
s=s.replace('_BumpTriplanar; float _BumpTile;','_BumpTriplanar, _SpecularStrength, _EnvironmentStrength; float _BumpTile;')
s=s.replace('_Smoothness, _Subsurface.rgb, reflection)', '_Smoothness, _Subsurface.rgb, _SpecularStrength, reflection)')
s=s.replace('_Smoothness, _Subsurface.rgb, extraReflection)', '_Smoothness, _Subsurface.rgb, _SpecularStrength, extraReflection)')
s=s.replace('half3 ambient = HeroAmbient(n) * c.rgb;', '''// Real probe reflections are restrained on skin and clear on varnished eyes/frames.
                // One shared reflection sample, no screen-space reflections or new render pass.
                half roughness = max(1 - _Smoothness, .08h);
                half fresnel = .04h + .10h * pow(1 - saturate(dot(n, v)), 5);
                half3 environment = GlossyEnvironmentReflection(reflect(-v, n), i.positionWS, roughness, 1) * fresnel * _EnvironmentStrength;
                colour += environment; reflection += environment;
                half3 ambient = HeroAmbient(n) * c.rgb;''')
p.write_text(s)
p=R/'Unity/Assets/Resources/Tennis/Shaders/HeroLighting.hlsl';s=p.read_text();start=s.index('half3 HeroCharacterShade');s=s[:start]+'''// A normalized broad lobe for skin plus a narrower varnish lobe for smooth eyes/equipment.
// Grazing reflectance and direct-light visibility prevent the flat clay/plastic silhouette.
half3 HeroCharacterShade (Light light, half3 n, half3 v, half3 albedo, half wrap, half smoothness, half3 subsurface, half specularStrength, out half3 reflection)
{
    half ndl = dot(n, light.direction), nl = saturate(ndl);
    half wrapped = saturate((ndl + wrap) / (1 + wrap));
    half edge = saturate(wrapped - nl) * 1.35h;
    half3 h = SafeNormalize(light.direction + v);
    half nh = saturate(dot(n, h));
    half broad = pow(nh, 10 + smoothness * 30) * .045h;
    half varnish = pow(nh, 24 + smoothness * smoothness * 200) * smoothness * .25h;
    half fresnel = 1 + pow(1 - saturate(dot(v, h)), 5) * 1.5h;
    half spec = (broad + varnish) * specularStrength * fresnel * saturate(ndl * 3);
    half atten = light.distanceAttenuation * light.shadowAttenuation;
    reflection = spec * light.color * atten;
    return (albedo * wrapped + subsurface * edge * albedo) * light.color * atten + reflection;
}
#endif
''';p.write_text(s)
p=R/'Unity/Assets/Scripts/Tennis/MatchHeroLook.cs';s=p.read_text()
s=s.replace('SkinSmoothness = .2f, SkinWrap = .55f, SkinRim = .35f, EyeSmoothness = .85f, FrameSmoothness = .65f, FrameRim = .2f','SkinSmoothness = .28f, SkinWrap = .32f, SkinRim = .075f, EyeSmoothness = .85f, FrameSmoothness = .72f, FrameRim = .075f')
s=s.replace('SkinBump = .18f','SkinBump = .10f').replace('ClothWrap = .5f, ClothRim = .2f','ClothWrap = .34f, ClothRim = .065f')
s=s.replace('new Color(.18f, .06f, .03f, 1)','new Color(.12f, .035f, .02f, 1)')
s=s.replace('m.SetColor("_Subsurface", SkinSubsurface);','m.SetColor("_Subsurface", SkinSubsurface);\n                m.SetFloat("_Saturation", .96f); m.SetFloat("_SpecularStrength", .8f); m.SetFloat("_EnvironmentStrength", .12f);')
s=s.replace('if (m.shader == CharacterShader) m.SetFloat("_Smoothness", EyeSmoothness);','''if (m.shader == CharacterShader) {
                // Sclera/iris and existing catchlights keep their authored colours. A restrained
                // corneal highlight gives depth without bleaching the face paint.
                m.SetFloat("_Smoothness", EyeSmoothness); m.SetFloat("_Wrap", .18f);
                m.SetFloat("_RimStrength", 0); m.SetFloat("_Saturation", 1);
                m.SetFloat("_SpecularStrength", .55f); m.SetFloat("_EnvironmentStrength", .5f);
            }''')
s=s.replace('m.SetFloat("_Wrap", DecalWrap); m.SetFloat("_RimStrength", .1f);','m.SetFloat("_Wrap", DecalWrap); m.SetFloat("_RimStrength", 0);\n                m.SetFloat("_SpecularStrength", .25f); m.SetFloat("_EnvironmentStrength", 0);')
s=s.replace('m.SetFloat("_RimStrength", FrameRim); }','m.SetFloat("_RimStrength", FrameRim); m.SetFloat("_Wrap", .18f); m.SetFloat("_Saturation", 1); m.SetFloat("_SpecularStrength", 1.2f); m.SetFloat("_EnvironmentStrength", .65f); }')
s=s.replace('m.SetFloat("_Wrap", .2f); m.SetFloat("_RimStrength", .1f);','m.SetFloat("_Wrap", .2f); m.SetFloat("_RimStrength", 0); m.SetFloat("_SpecularStrength", .45f); m.SetFloat("_EnvironmentStrength", .1f);')
s=s.replace('m.SetFloat("_Wrap", ClothWrap); m.SetFloat("_RimStrength", .1f);','m.SetFloat("_Wrap", ClothWrap); m.SetFloat("_RimStrength", 0);')
p.write_text(s)
print('Updated shared active character materials and shader roles')
