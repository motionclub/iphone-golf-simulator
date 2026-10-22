from pathlib import Path
import hashlib,json
root=Path.cwd();out=root/'work/reference-rebuild/tennis-resort-material1'
files=['Unity/Assets/Scripts/Tennis/TennisVenueArt.cs','Unity/Assets/Scripts/Tennis/TennisEnvironmentV4.cs','Unity/Assets/Scripts/Tennis/TennisLook.cs','Unity/Assets/Resources/Tennis/Shaders/TennisWorldSurface.shader','Unity/Assets/Resources/Tennis/Shaders/TennisBotanical.shader']
baseline={}
def save(path,s):
 target=out/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(s)
for path in files:baseline[path]=hashlib.sha256((root/path).read_bytes()).hexdigest()
p=files[0];s=(root/p).read_text();s=s.replace('if (surfaces.TryGetValue(key, out var old) && old) return old;','if (surfaces.TryGetValue(key, out var old) && old) { TennisResortMaterials.Surface(old, key); return old; }')
s=s.replace('return surfaces[key] = m;','TennisResortMaterials.Surface(m, key);\n            return surfaces[key] = m;',1)
s=s.replace('                Renderer BuildCell(Transform parent,string name,Vector2Int key,Cell cell,bool shadows=true)','                TennisResortMaterials.Botanical(material);\n                Renderer BuildCell(Transform parent,string name,Vector2Int key,Cell cell,bool shadows=true)')
s=s.replace('var colour=Palette[role];colour.a=', 'var colour=TennisResortMaterials.BotanicalColour(Palette[role],role);colour.a=')
save(p,s)
p=files[1];s=(root/p).read_text();a='roles[i].SetFloat("_ReflectionWeight",.46f);roles[i].SetFloat("_ReflectionHeading",-45);\n                        }';b=a+'\n                        TennisResortMaterials.Surface(roles[i], "Clubhouse role " + cell);';assert a in s;s=s.replace(a,b);save(p,s)
p=files[2];s=(root/p).read_text();a='sea.SetVector("_ShoreBounds",new Vector4(-242.5f,-187.5f,477.5f,632.5f));\n                }';assert a in s;s=s.replace(a,a+'\n                TennisResortMaterials.Sea(sea);');save(p,s)
p=files[3];s=(root/p).read_text();s=s.replace('_Smoothness("Surface polish", Range(0,1)) = .22','_Smoothness("Surface polish", Range(0,1)) = .22\n        _ResortResponse("Resort material response", Range(0,1)) = 0\n        _TimberGrain("Fine timber grain", Range(0,.2)) = 0')
s=s.replace('#pragma multi_compile_fragment _ _SHADOWS_SOFT','#pragma multi_compile_fragment _ _SHADOWS_SOFT\n            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION')
a='#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"'
b='''// Keep URP's automatic screen AO disabled for this material. The resort
            // consumes only a bounded indirect factor below, never sun/direct AO.
            #if defined(_SCREEN_SPACE_OCCLUSION)
                #define TENNIS_RESORT_SCREEN_AO 1
                #undef _SCREEN_SPACE_OCCLUSION
            #endif
            '''+a
s=s.replace(a,b)
s=s.replace('half _Smoothness, _Metallic, _Variation, _Grain;','half _Smoothness, _Metallic, _Variation, _Grain, _ResortResponse, _TimberGrain;')
a='colour *= 1 + broad * _Variation * 2 + fine * _Grain * 2;'
b=a+'''
                if (_TimberGrain > .001)
                {
                    float3 normal=abs(normalize(i.normalWS));
                    float2 plane=normal.y>.65?i.positionWS.xz:(normal.x>normal.z?i.positionWS.zy:i.positionWS.xy);
                    float timber=Noise(float3(plane.x*.7,plane.y*18,3.7))-.5;
                    colour *= 1+timber*_TimberGrain;
                }'''
s=s.replace(a,b)
a='surface.albedo = colour; surface.alpha = 1; surface.occlusion = 1;'
b=a+'''
                #if defined(TENNIS_RESORT_SCREEN_AO)
                    half ambientAO=saturate(SampleAmbientOcclusion(input.normalizedScreenSpaceUV)+(1-_AmbientOcclusionParam.x));
                    surface.occlusion=lerp(1,ambientAO,.30h*_ResortResponse);
                #endif'''
s=s.replace(a,b);save(p,s)
p=files[4];s=(root/p).read_text();s=s.replace('_Leaf("Leaf translucency",Range(0,1))=1','_Leaf("Leaf translucency",Range(0,1))=1\n  _ResortResponse("Resort leaf response",Range(0,1))=0')
s=s.replace('half4 _BaseColor;half _Gloss,_Leaf,_VertexPalette;','half4 _BaseColor;half _Gloss,_Leaf,_VertexPalette,_ResortResponse;')
s=s.replace('#pragma multi_compile_fragment _ _SHADOWS_SOFT','#pragma multi_compile_fragment _ _SHADOWS_SOFT\n   #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION')
s=s.replace('half wrapped=saturate((dot(n,sun.direction)+.60h)/1.60h);','half wrap=lerp(.60h,.32h,_ResortResponse);\n    half wrapped=saturate((dot(n,sun.direction)+wrap)/(1+wrap));')
s=s.replace('half3 ambient=SampleSH(n)+half3(.06h,.07h,.055h)*_Leaf;','''half3 ambient=SampleSH(n)+half3(.06h,.07h,.055h)*_Leaf;
    AmbientOcclusionFactor ao=GetScreenSpaceAmbientOcclusion(GetNormalizedScreenSpaceUV(i.p));
    ambient*=lerp(1,ao.indirectAmbientOcclusion,.30h*_ResortResponse);''')
s=s.replace('c+=albedo*sun.color*back*.22h*_Leaf*sun.shadowAttenuation;','''half leaf=saturate(i.weight*4);
    half transmission=lerp(.22h,.30h*leaf,_ResortResponse);
    c+=albedo*sun.color*back*transmission*_Leaf*sun.shadowAttenuation;''')
s=s.replace('c+=sun.color*pow(saturate(dot(n,h)),36.0h)*_Gloss*.075h*sun.shadowAttenuation;','''half sheen=lerp(.075h,.12h*leaf,_ResortResponse);
    c+=sun.color*pow(saturate(dot(n,h)),36.0h)*_Gloss*sheen*sun.shadowAttenuation;''');save(p,s)
new='Unity/Assets/Scripts/Tennis/TennisResortMaterials.cs'
save(new,'''using System;
using UnityEngine;

namespace GolfArcade.Tennis
{
    // One resort-only material calibration. No light, geometry, collider or
    // renderer setting is changed; the other venue responses stay at zero.
    public static class TennisResortMaterials
    {
        public static bool Active => TennisVenue.IsResort && Environment.GetEnvironmentVariable("TENNIS_RESORT_MATERIALS_OFF") != "1";
        static void Colour(Material m,Color c,float polish) { m.SetColor("_BaseColor",c);m.SetFloat("_Smoothness",polish); }
        public static void Surface(Material m,string role)
        {
            if(!m)return;
            if(m.HasProperty("_ResortResponse"))m.SetFloat("_ResortResponse",Active?1:0);
            if(!Active)return;
            if(role.StartsWith("TropicalV3_002") && !TennisVenue.CourtColorOverride.HasValue)
            { Colour(m,new Color(.036f,.47f,.51f),.22f);m.SetFloat("_Variation",.045f); }
            else if(role.StartsWith("TropicalV3_011") && !TennisVenue.CourtColorOverride.HasValue)
            { Colour(m,new Color(.045f,.34f,.315f),.19f);m.SetFloat("_Variation",.04f); }
            else if(role.StartsWith("TropicalV3_010"))Colour(m,new Color(.74f,.75f,.71f),.24f);
            else if(role=="Resort cut stone" || role=="Crafted resort limestone")Colour(m,new Color(.78f,.79f,.735f),.20f);
            else if(role=="Crafted resort ivory ceramic")Colour(m,new Color(.80f,.82f,.765f),.38f);
            else if(role=="Crafted resort sail canvas")Colour(m,new Color(.79f,.83f,.79f),.10f);
            else if(role=="Resort timber" || role=="Crafted resort oiled teak")
            { Colour(m,new Color(.43f,.28f,.135f),.29f);m.SetFloat("_TimberGrain",.10f); }
            else if(role.StartsWith("Clubhouse role ") && int.TryParse(role.Substring(15),out int cell))
            {
                // The source atlas keeps its authored height gradients. Multipliers
                // separate plaster, roof, timber and glass instead of flattening them.
                switch(cell)
                {
                    case 3: Colour(m,new Color(.88f,.93f,.985f),.16f);break;
                    case 4: Colour(m,new Color(.80f,.78f,.76f),.29f);break;
                    case 5: Colour(m,new Color(.78f,.95f,.92f),.34f);break;
                    case 6: Colour(m,new Color(.91f,.87f,.77f),.31f);m.SetFloat("_TimberGrain",.10f);break;
                    case 7: Colour(m,new Color(.65f,.77f,.87f),.78f);m.SetFloat("_ReflectionWeight",.62f);break;
                    case 11: Colour(m,new Color(.91f,.95f,.94f),.22f);break;
                    case 12: case 15: Colour(m,new Color(.88f,.94f,.96f),.27f);break;
                }
            }
        }
        public static void Botanical(Material m)
        {
            if(!m)return;
            m.SetFloat("_ResortResponse",Active?1:0);m.SetFloat("_Gloss",Active?.24f:.18f);
        }
        public static Color BotanicalColour(Color original,int role)
        {
            if(!Active)return original;
            switch(role)
            {
                case 1:return new Color(.05f,.225f,.075f);
                case 2:return new Color(.145f,.37f,.105f);
                case 3:return new Color(.36f,.51f,.155f);
                default:return original;
            }
        }
        public static void Sea(Material sea)
        {
            if(!Active||!sea)return;
            sea.SetColor("_Shallow",new Color(.018f,.63f,.61f));
            sea.SetColor("_Deep",new Color(.008f,.30f,.51f));
            sea.SetColor("_Sky",new Color(.08f,.54f,.76f));
            sea.SetFloat("_Sparkle",1.4f);sea.SetFloat("_WaveScale",.28f);
        }
    }
}
''')
manifest={'baseline':baseline,'newFiles':[new],'intent':['cyan matte acrylic vs grey teal','neutral ivory, warmer timber and distinct glazing','turquoise/blue sea and deeper warm leaf hierarchy'],'unchanged':['geometry/colliders/contact/net','HeroLighting','renderer/postprocess','other venues'],'actualGate':'PENDING matching captures, no compile or art claim'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Staged six sources off Assets; baseline hashes pinned.')
