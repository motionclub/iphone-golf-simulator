from pathlib import Path
p=Path(__file__).parent
f=p/'Unity/Assets/Resources/Tennis/Shaders/TennisVolcanicSky.shader'
f.write_text('''Shader "GolfArcade/TennisVolcanicSky"
{
 Properties { _Panorama("Volcanic dusk panorama",2D)="white"{} _Rotation("Heading",Float)=-55 _Exposure("Exposure",Float)=1 _CloudCompression("Cloud band altitude",Float)=1.75 }
 SubShader {
  Tags {"Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" "RenderPipeline"="UniversalPipeline"}
  Cull Off ZWrite Off
  Pass {
   HLSLPROGRAM
   #pragma target 3.0
   #pragma vertex vert
   #pragma fragment frag
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   TEXTURE2D(_Panorama);SAMPLER(sampler_Panorama);
   CBUFFER_START(UnityPerMaterial)float _Rotation,_Exposure,_CloudCompression;CBUFFER_END
   struct A{float4 p:POSITION;};struct V{float4 p:SV_POSITION;float3 d:TEXCOORD0;};
   V vert(A a){V o;o.p=TransformObjectToHClip(a.p.xyz);o.d=a.p.xyz;return o;}
   half4 frag(V i):SV_Target{
    float3 d=normalize(i.d);float longitude=atan2(d.z,d.x)/6.2831853+.5+_Rotation/360;
    float latitude=clamp(.5+asin(clamp(d.y,-1,1))/3.14159265*_CloudCompression,.001,.999);
    float denominator=max(dot(d.xz,d.xz),.00001)*6.2831853;
    float2 gx=float2((d.x*ddx(d.z)-d.z*ddx(d.x))/denominator,ddx(latitude));
    float2 gy=float2((d.x*ddy(d.z)-d.z*ddy(d.x))/denominator,ddy(latitude));
    float u=frac(longitude);half3 sky=SAMPLE_TEXTURE2D_GRAD(_Panorama,sampler_Panorama,float2(u,latitude),gx,gy).rgb;
    half3 edges=(SAMPLE_TEXTURE2D_GRAD(_Panorama,sampler_Panorama,float2(.012,latitude),gx,gy).rgb+SAMPLE_TEXTURE2D_GRAD(_Panorama,sampler_Panorama,float2(.988,latitude),gx,gy).rgb)*.5;
    sky=lerp(edges,sky,smoothstep(0,.035,min(u,1-u)));
    // A small ash veil shares the distant rock hue, while retaining bright cloud edges.
    sky=lerp(sky,half3(.23,.18,.24),.06*(1-saturate(d.y)));
    return half4(sky*_Exposure,1);
   }
   ENDHLSL
  }
 }
 Fallback Off
}
''')

f=p/'Unity/Assets/Scripts/Tennis/TennisVenueBuilder.Volcano.cs';s=f.read_text()
a=s.index('                float[] edge =',s.index('            static void Sky(Transform root)'))
b=s.index('\n            static Texture2D VolcanoSun()',a)
s=s[:a]+'''                // The original CPU-baked striped dome and ring sun are replaced by
                // the authored panorama in Light. It has no scene geometry or gameplay effect.
            }
''' + s[b:]
s=s.replace('var material=TennisVenueArt.Surface(name,colour,.14f,0,.065f,.004f);','''var material=TennisVenueArt.Surface(name,colour,.22f,0,.09f,.005f);''')
s=s.replace('material.SetFloat("_WorldMapWeight",.34f);material.SetFloat("_WorldMapScale",.024f);','''// Basalt albedo is charcoal already; normalize around its measured
                // midtone instead of multiplying two dark colours into a black wall.
                material.SetFloat("_WorldMapWeight",.72f);material.SetFloat("_WorldMapReference",.075f);
                material.SetFloat("_WorldMapScale",.055f);
                material.SetTexture("_WorldNormal",Resources.Load<Texture2D>("Course/Resort/ResortBasalt_N"));
                material.SetFloat("_WorldNormalStrength",.65f);''')
s=s.replace('new Color(.14f,.125f,.12f):a==b1?new Color(.115f,.12f,.13f):new Color(.16f,.16f,.17f)', 'new Color(.245f,.23f,.225f):a==b1?new Color(.235f,.245f,.27f):new Color(.29f,.29f,.305f)')
s=s.replace('new Color(.14f,.14f,.15f)', 'new Color(.26f,.265f,.28f)')
s=s.replace('RenderSettings.ambientEquatorColor = new Color(.27f, .30f, .38f);', 'RenderSettings.ambientEquatorColor = new Color(.31f, .32f, .40f);')
s=s.replace('RenderSettings.fogColor = new Color(.42f, .19f, .14f);', 'RenderSettings.fogColor = new Color(.36f, .29f, .34f);')
s=s.replace('RenderSettings.fogStartDistance = 350; RenderSettings.fogEndDistance = 3800;', 'RenderSettings.fogStartDistance = 115; RenderSettings.fogEndDistance = 1450;')
s=s.replace('''RenderSettings.skybox = null;
                camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = new Color(.42f, .19f, .14f);''','''var skyShader=Resources.Load<Shader>("Tennis/Shaders/TennisVolcanicSky");
                if(skyShader)
                {
                    var sky=new Material(skyShader){name="Volcanic dusk cloud panorama"};
                    sky.SetTexture("_Panorama",Resources.Load<Texture2D>("Course/Resort/SkyVolcanic"));
                    sky.SetFloat("_Rotation",-55);sky.SetFloat("_CloudCompression",1.75f);sky.SetFloat("_Exposure",.95f);
                    RenderSettings.skybox=sky;camera.clearFlags=CameraClearFlags.Skybox;
                }
                else {RenderSettings.skybox=null;camera.clearFlags=CameraClearFlags.SolidColor;}
                camera.backgroundColor = new Color(.36f,.29f,.34f);''')
f.write_text(s)

f=p/'Unity/Assets/Scripts/Tennis/TennisLook.cs';s=f.read_text()
s=s.replace('RenderSettings.ambientEquatorColor = new Color(.39f, .44f, .43f);', 'RenderSettings.ambientEquatorColor = new Color(.28f, .35f, .39f);')
s=s.replace('RenderSettings.ambientGroundColor = new Color(.19f, .23f, .20f);', 'RenderSettings.ambientGroundColor = new Color(.16f, .20f, .19f);')
s=s.replace('RenderSettings.fogColor = new Color(.45f, .68f, .81f);', 'RenderSettings.fogColor = new Color(.53f, .70f, .80f);')
s=s.replace('resortSky.SetFloat("_Rotation", 88); resortSky.SetFloat("_Exposure", 1);','''resortSky.SetFloat("_Rotation", 88); resortSky.SetFloat("_Exposure", 1);
                resortSky.SetFloat("_AirColorShare",.64f);resortSky.SetFloat("_DayHaze",.10f);''')
s=s.replace('result.SetFloat("_CourtFinish",1); result.SetFloat("_Grain",.012f);','''result.SetFloat("_CourtFinish",1); result.SetFloat("_Grain",.010f);
                            result.SetTexture("_MicroMap",Resources.Load<Texture2D>("Tennis/Premium/AcrylicAggregate"));result.SetFloat("_MicroStrength",.19f);result.SetFloat("_MicroScale",1);''')
s=s.replace('case "TropicalV3_011": result = Tinted(m, TennisVenue.RunoffColor, .22f); break;', '''case "TropicalV3_011": result = Tinted(m, TennisVenue.RunoffColor, .14f); result.SetFloat("_CourtFinish",1);
                            result.SetTexture("_MicroMap",Resources.Load<Texture2D>("Tennis/Premium/AcrylicAggregate"));result.SetFloat("_MicroStrength",.16f);result.SetFloat("_MicroScale",1);break;''')
s=s.replace('case "TropicalV3_010": result = Tinted(m, new Color(.78f, .70f, .56f), .15f); break;', '''case "TropicalV3_010": result = Tinted(m, new Color(.79f, .74f, .64f), .27f); result.SetFloat("_Paving",1);
                            result.SetTexture("_MicroMap",Resources.Load<Texture2D>("Tennis/Premium/AcrylicAggregate"));result.SetFloat("_MicroStrength",.10f);result.SetFloat("_MicroScale",.5f);break;''')
f.write_text(s)

f=p/'Unity/Assets/Scripts/Tennis/TennisVenueArt.cs';s=f.read_text()
s=s.replace('var m = new Material(shader) { name = key, enableInstancing = true };','''var m = new Material(shader) { name = key, enableInstancing = true };''')
# Do not silently enable micro maps on every old asset. Only measured court/stone materials opt in.
f.write_text(s)
print('World19 lighting + materials staged; geometry unchanged')
