from pathlib import Path
R=Path(__file__).resolve().parents[3]
for name,cap in [('GolferClay', '.12'), ('HeroKit','.10')]:
 p=R/f'Unity/Assets/Shaders/{name}.shader';s=p.read_text()
 s=s.replace('= 0.85','= '+cap).replace('= 0.45','= '+cap) if name=='GolferClay' else s.replace('Range(0, 1)) = 0.45','Range(0, 1)) = '+cap)
 anchor='_Wrap ("Light wrap", Range(0, 1)) = '
 line=next(l for l in s.splitlines() if anchor in l)
 s=s.replace(line,line+'\n        _SurfaceSmoothness ("Surface smoothness", Range(0,1)) = 0.28\n        _SurfaceSpecular ("Surface highlight", Range(0,2)) = 0.8\n        _SurfaceSheen ("Fabric grazing sheen", Range(0,1)) = 0\n        _SurfaceWarmth ("Skin warmth", Color) = (0.12,0.035,0.02,1)')
 # Legacy built-in preview retains same deliberate low matcap influence.
 s=s.replace('float _MatCapGain,','float _SurfaceSmoothness, _SurfaceSpecular, _SurfaceSheen; float4 _SurfaceWarmth;\n        float _MatCapGain,') if name=='GolferClay' else s.replace('float _UseAtlas,','float _SurfaceSmoothness, _SurfaceSpecular, _SurfaceSheen; float4 _SurfaceWarmth;\n        float _UseAtlas,')
 s=s.replace('c.rgb = s.Albedo * gi.light.color * lit;', 'c.rgb = s.Albedo * gi.light.color * lit;\n            half3 h = normalize(gi.light.dir + viewDir);\n            half spec = pow(saturate(dot(s.Normal,h)), 16 + _SurfaceSmoothness * 80) * _SurfaceSpecular * .08 * saturate(nl * 3);\n            c.rgb += gi.light.color * spec;')
 s=s.replace('c.rgb = s.Albedo * (gi.light.color * lit + _Fill);','c.rgb = s.Albedo * (gi.light.color * lit + _Fill);\n            half3 h = normalize(gi.light.dir + viewDir);\n            half spec = pow(saturate(dot(s.Normal,h)), 16 + _SurfaceSmoothness * 80) * _SurfaceSpecular * .08 * saturate(nl * 3);\n            c.rgb += gi.light.color * spec;')
 if name=='GolferClay':
  begin=s.index('// The golfer,');end=s.index('Shader ')
  s='// Legacy golfer compatibility surface. Scene lights describe the form, with distinct\n// restrained skin highlights and cloth sheen; the old studio matcap is a small fill only.\n'+s[end:]
 else:
  end=s.index('Shader ');s='// Modular golf compatibility surface. The shared MatchHeroLook path is preferred;\n// this surface keeps legacy spectators, optional hair and painted parts grounded in scene light.\n'+s[end:]
 p.write_text(s)
p=R/'Unity/Assets/Shaders/GolfLegacyURP.hlsl';s=p.read_text()
s=s.replace('float _MatCapGain, _KnitTile, _Fabric, _KitOn, _ShirtOn;','float _MatCapGain, _KnitTile, _Fabric, _KitOn, _ShirtOn;\nfloat _SurfaceSmoothness, _SurfaceSpecular, _SurfaceSheen; float4 _SurfaceWarmth;')
s=s.replace('half3 colour = albedo * lighting;', '''half3 colour = albedo * lighting;
    #if defined(GOLF_HERO) || defined(GOLF_CLAY)
    half3 view = SafeNormalize(GetWorldSpaceViewDir(i.positionWS));
    half3 reflected;
    // Keep the semantic old material API; replace its diffuse-only clay response.
    half3 direct = HeroCharacterShade(light, n, view, albedo, wrap, _SurfaceSmoothness, _SurfaceWarmth.rgb, _SurfaceSpecular, reflected);
    half3 diffuse = albedo * light.color * HeroWrapped(n, light.direction, wrap) * light.shadowAttenuation;
    colour += direct - diffuse;
    half graze = pow(1 - saturate(dot(n, view)), 4) * _SurfaceSheen;
    colour += sqrt(max(albedo, 0)) * graze * saturate(dot(n, light.direction)) * light.color * light.shadowAttenuation * .12h;
    #endif''')
p.write_text(s)
p=R/'Unity/Assets/Scripts/Game/GolferView.cs';s=p.read_text()
s=s.replace('mats[i] = Clay(Color.Lerp(c, finish, 0.85f), false);','mats[i] = FinishedClub(original[i], Color.Lerp(c, finish, 0.85f));')
s=s.replace('m.SetFloat("_Fabric", cloth ? 0.6f : 0f);','''m.SetFloat("_MatCapStrength", .12f);
            m.SetFloat("_Wrap", cloth ? .34f : .32f);
            m.SetFloat("_Fabric", cloth ? .18f : 0f);
            m.SetFloat("_SurfaceSmoothness", cloth ? .12f : .28f);
            m.SetFloat("_SurfaceSpecular", cloth ? .25f : .8f);
            m.SetFloat("_SurfaceSheen", cloth ? .45f : 0f);
            m.SetColor("_SurfaceWarmth", cloth ? Color.black : new Color(.12f, .035f, .02f));''')
s=s.replace('m.SetFloat("_MatCapStrength", 0.6f);','m.SetFloat("_MatCapStrength", .08f);')
insert='''        static readonly Dictionary<(Material, Color), Material> finishedClubMaterials = new();
        static Material FinishedClub(Material source, Color tint)
        {
            if (finishedClubMaterials.TryGetValue((source, tint), out var cached) && cached) return cached;
            // A reward changes the finish colour, retaining the authored metal/carbon roughness.
            // The former clay replacement erased both sky reflections and the material identity.
            var m = new Material(source) { name = source.name + " (finish)" };
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", tint);
            if (m.HasProperty("_Color")) m.SetColor("_Color", tint);
            finishedClubMaterials[(source, tint)] = m;
            return m;
        }

'''
s=s.replace('        static readonly Dictionary<string, Material> clubMaterials = new();', '        static readonly Dictionary<string, Material> clubMaterials = new();\n\n'+insert)
p.write_text(s)
p=R/'Unity/Assets/Scripts/Game/HeroGolfer.cs';s=p.read_text()
s=s.replace('m.SetFloat("_MatCapStrength", capStrength);','''m.SetFloat("_MatCapStrength", Mathf.Min(capStrength, .12f));
            bool cloth = name.StartsWith("Kit_"), eye = name.Contains("Iris") || name.Contains("Sclera") || name.Contains("Pupil") || name.Contains("Catch");
            m.SetFloat("_SurfaceSmoothness", eye ? .82f : cloth ? .12f : .28f);
            m.SetFloat("_SurfaceSpecular", eye ? .55f : cloth ? .25f : .8f);
            m.SetFloat("_SurfaceSheen", cloth ? .45f : 0f);
            m.SetColor("_SurfaceWarmth", cloth || eye ? Color.black : new Color(.12f, .035f, .02f));''')
s=s.replace('m.SetFloat("_Wrap", 0.6f);','m.SetFloat("_Wrap", 0.32f);')
# Use the complete hand-pair mesh contract. Select visibility by handedness after materials.
s=s.replace(' || src.name == "Kit_Glove_R"','')
s=s.replace('            Root.SetActive(true);\n            Dress(look);','            Root.SetActive(true);\n            surface.SetGolfHand(GolferStyle.LeftHanded);\n            Dress(look);')
# Left-handed state actual property may differ; audited below before finalising.
p.write_text(s)
print('Upgraded legacy golf shading and preserved physical club finishes')
