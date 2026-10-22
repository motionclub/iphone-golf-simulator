from pathlib import Path
import re,uuid,shutil
shader=Path('Unity/Assets/Resources/Tennis/Shaders/TennisWorldSurface.shader');s=shader.read_text()
s=s.replace('        [Enum(UnityEngine.Rendering.CullMode)]', '''        _CoastBlend("Coast sand / meadow blend", Float) = 0
        _SandColor("Shore sand", Color) = (.83,.77,.63,1)
        _GrassColor("Meadow", Color) = (.13,.30,.09,1)
        [Enum(UnityEngine.Rendering.CullMode)]''')
s=s.replace('float _WorldMapWeight, _WorldMapScale;', 'float _WorldMapWeight, _WorldMapScale, _CoastBlend; half4 _SandColor, _GrassColor;')
s=s.replace('float2 uv:TEXCOORD0; };','float2 uv:TEXCOORD0; half4 colour:COLOR; };').replace('half3 vertexLight:TEXCOORD4; };','half3 vertexLight:TEXCOORD4; half4 colour:TEXCOORD5; };')
s=s.replace('o.uv = TRANSFORM_TEX(v.uv, _BaseMap);','o.uv = TRANSFORM_TEX(v.uv, _BaseMap); o.colour = v.colour;')
s=s.replace('                if (_WorldMapWeight > .001)', '''                if (_CoastBlend > .5)
                    colour = lerp(_SandColor.rgb, _GrassColor.rgb, smoothstep(.03,.95,i.colour.r));
                if (_WorldMapWeight > .001)''')
s=s.replace('                    colour *= lerp(half3(1,1,1),mapped,_WorldMapWeight);', '''                    if (_CoastBlend > .5)
                    {
                        half steep = (1-smoothstep(.70,.93,abs(normalize(i.normalWS).y))) * i.colour.b;
                        colour = lerp(colour,mapped * _BaseColor.rgb,steep);
                    }
                    else colour *= lerp(half3(1,1,1),mapped,_WorldMapWeight);''')
shader.write_text(s)
p=Path('Unity/Assets/Scripts/Tennis/TennisVenueArt.cs');s=p.read_text()
s=s.replace('                    if (role.Contains("GRASS"))', '''                    if (role.Contains("TERRAIN"))
                    {
                        materials[i] = Surface("Coast blended meadow and beach", new Color(.94f,.94f,.88f), .10f, 0, .105f, .008f);
                        materials[i].SetFloat("_CoastBlend",1);
                        materials[i].SetColor("_SandColor",new Color(.78f,.75f,.63f));
                        materials[i].SetColor("_GrassColor",new Color(.13f,.30f,.09f));
                        materials[i].SetTexture("_WorldMap",Resources.Load<Texture2D>("Course/Resort/Limestone_C"));
                        materials[i].SetFloat("_WorldMapWeight",1); materials[i].SetFloat("_WorldMapScale",.12f);
                    }
                    else if (role.Contains("GRASS"))''')
s=s.replace('QueuePlant(parts[1], marker.position', 'QueuePlant(parts[1] == "BUSH" ? "BUSH_BROAD" : parts[1], marker.position')
p.write_text(s)
p=Path('Unity/Assets/Resources/Tennis/Shaders/TennisWater.shader');s=p.read_text()
s=s.replace('        _DeepDistance', '''        _ShoreMap("Actual coast shallow depth",2D)="black"{}
        _UseShoreMap("Authored shoreline",Float)=0
        _ShoreBounds("Coast bounds x z width depth",Vector)=(-242.5,-187.5,477.5,632.5)
        _DeepDistance''',1)
s=s.replace('            CBUFFER_START(UnityPerMaterial)', '            TEXTURE2D(_ShoreMap); SAMPLER(sampler_ShoreMap);\n            CBUFFER_START(UnityPerMaterial)')
s=s.replace('float _DeepDistance, _WaveScale, _Sparkle;', 'float _DeepDistance, _WaveScale, _Sparkle, _UseShoreMap; float4 _ShoreBounds;')
s=s.replace('                half fresnel', '''                if (_UseShoreMap > .5)
                {
                    float2 shoreUV=(i.positionWS.xz-_ShoreBounds.xy)/_ShoreBounds.zw;
                    float inside=step(0,shoreUV.x)*step(shoreUV.x,1)*step(0,shoreUV.y)*step(shoreUV.y,1);
                    half shallow=SAMPLE_TEXTURE2D(_ShoreMap,sampler_ShoreMap,saturate(shoreUV)).r*inside;
                    water=lerp(_Deep.rgb,_Shallow.rgb,shallow);
                }
                half fresnel''')
p.write_text(s)
p=Path('Unity/Assets/Scripts/Tennis/TennisLook.cs');s=p.read_text()
s=s.replace('resortSky.SetFloat("_Rotation", 35)', 'resortSky.SetFloat("_Rotation", 88)').replace('resortSky.SetFloat("_CloudCompression", 1.35f)', 'resortSky.SetFloat("_CloudCompression", .85f)')
s=s.replace('                sea.SetFloat("_Sparkle", 1.4f);', '''                sea.SetFloat("_Sparkle", 1.0f);
                var shore = Resources.Load<Texture2D>("Tennis/Premium/CoastShallows");
                if (shore && sea.HasProperty("_ShoreMap"))
                {
                    sea.SetTexture("_ShoreMap",shore); sea.SetFloat("_UseShoreMap",1);
                    sea.SetVector("_ShoreBounds",new Vector4(-242.5f,-187.5f,477.5f,632.5f));
                }''')
p.write_text(s)
meta=Path('Unity/Assets/Resources/Course/Resort/SkyCoastal.png.meta').read_text();meta=re.sub(r'guid: \w+',f'guid: {uuid.uuid4().hex}',meta).replace('sRGBTexture: 1','sRGBTexture: 0').replace('wrapU: 0','wrapU: 1').replace('wrapV: 0','wrapV: 1')
Path('Unity/Assets/Resources/Tennis/Premium/CoastShallows.png.meta').write_text(meta)
shutil.copy2('/Users/adnanyonathan/.codex/generated_images/01a114cb-8312-7363-a7bc-a81a6ff7ce35/exec-32a6b6dd-aa93-4b6b-ba8a-fb4c4a044697.png','Unity/Assets/Resources/Tennis/Premium/SkyRooftop.png')
meta=Path('Unity/Assets/Resources/Course/Resort/SkyCoastal.png.meta').read_text();meta=re.sub(r'guid: \w+',f'guid: {uuid.uuid4().hex}',meta);Path('Unity/Assets/Resources/Tennis/Premium/SkyRooftop.png.meta').write_text(meta)
