from pathlib import Path
p=Path(__file__).parent
f=p/'Unity/Assets/Resources/Tennis/Shaders/TennisWorldSurface.shader'
s=f.read_text().replace('_WorldMapScale("World albedo scale", Float) = .12','''_WorldMapScale("World albedo scale", Float) = .12
        _WorldMapReference("World albedo reference", Float) = 1
        _WorldNormal("Mineral relief", 2D) = "bump" {}
        _WorldNormalStrength("Mineral relief strength", Range(0,2)) = 0
        _MicroMap("Metre-scale micro aggregate",2D) = "gray" {}
        _MicroScale("Micro aggregate tiles per metre",Float) = 1
        _MicroStrength("Aggregate normal strength",Range(0,1)) = 0
        _Paving("Cut limestone paving joints",Float) = 0''')
s=s.replace('TEXTURE2D(_WorldMap); SAMPLER(sampler_WorldMap);','''TEXTURE2D(_WorldMap); SAMPLER(sampler_WorldMap);
            TEXTURE2D(_WorldNormal); SAMPLER(sampler_WorldNormal);
            TEXTURE2D(_MicroMap); SAMPLER(sampler_MicroMap);''')
s=s.replace('float _WorldMapWeight, _WorldMapScale, _CoastBlend, _CourtFinish;', 'float _WorldMapWeight, _WorldMapScale, _WorldMapReference, _WorldNormalStrength, _MicroScale, _MicroStrength, _Paving, _CoastBlend, _CourtFinish;')
s=s.replace('else colour *= lerp(half3(1,1,1),mapped,_WorldMapWeight);','''else colour *= lerp(half3(1,1,1),clamp(mapped/max(_WorldMapReference,.01),.35,1.8),_WorldMapWeight);''')
s=s.replace('input.normalWS = masonryNormal;', '''input.normalWS = masonryNormal;
                if (_WorldNormalStrength > .001)
                {
                    float3 weights=pow(abs(normalize(i.normalWS)),4); weights/=max(dot(weights,1),.001);
                    float3 p=i.positionWS*_WorldMapScale;
                    half3 nx=UnpackNormalScale(SAMPLE_TEXTURE2D(_WorldNormal,sampler_WorldNormal,p.yz),_WorldNormalStrength);
                    half3 ny=UnpackNormalScale(SAMPLE_TEXTURE2D(_WorldNormal,sampler_WorldNormal,p.xz),_WorldNormalStrength);
                    half3 nz=UnpackNormalScale(SAMPLE_TEXTURE2D(_WorldNormal,sampler_WorldNormal,p.xy),_WorldNormalStrength);
                    half3 relief=half3(0,nx.x,nx.y)*weights.x + half3(ny.x,0,ny.y)*weights.y + half3(nz.x,nz.y,0)*weights.z;
                    input.normalWS=normalize(input.normalWS+relief);
                }
                if (_MicroStrength > .001 && abs(i.normalWS.y) > .65)
                {
                    half4 micro=SAMPLE_TEXTURE2D(_MicroMap,sampler_MicroMap,i.positionWS.xz*_MicroScale);
                    input.normalWS=normalize(input.normalWS+half3(micro.r*2-1,0,micro.g*2-1)*_MicroStrength);
                    // Small retained pigment variation; mipmaps integrate real millimetre aggregate.
                    colour *= 1+(micro.a-.5)*.028;
                }
                if (_Paving > .5 && i.normalWS.y > .65)
                {
                    float2 uv=i.positionWS.xz/float2(1.2,.6);
                    uv.x+=step(.5,frac(floor(uv.y)*.5))*.5;
                    float2 cell=frac(uv), edge=min(cell,1-cell)*float2(1.2,.6);
                    float distance=min(edge.x,edge.y);
                    float width=max(fwidth(distance),.0005);
                    half joint=1-smoothstep(.001-width,.003+width,distance);
                    colour *= 1-joint*.18;
                    colour *= .975+Hash(float3(floor(uv),17))*.05;
                }''')
f.write_text(s)

f=p/'Unity/Assets/Resources/Tennis/Shaders/TennisCoastalSky.shader';s=f.read_text()
s=s.replace('_DayHaze("Daylight haze",Range(0,1))=0','_DayHaze("Daylight haze",Range(0,1))=0 _AirColorShare("Clear-sky colour calibration",Range(0,1))=.58')
s=s.replace('_LongitudeScale,_DayHaze;', '_LongitudeScale,_DayHaze,_AirColorShare;')
s=s.replace('sky=lerp(sky,half3(.31,.49,.63),_DayHaze*(1-saturate(d.y)*.45));','''// Keep actual cloud radiance and silhouette; calibrate only clear blue toward airy coastal cyan.
    half cloud=smoothstep(.16,.65,min(sky.r,sky.g));
    half3 clear=lerp(half3(.34,.56,.76),half3(.085,.30,.58),pow(saturate(d.y),.42));
    sky=lerp(sky,clear,_AirColorShare*(1-cloud));
    sky=lerp(sky,half3(.40,.58,.71),_DayHaze*(1-saturate(d.y)*.65)*(1-cloud*.65));''')
f.write_text(s)

f=p/'Unity/Assets/Resources/Tennis/Shaders/TennisRooftopSky.shader'
f.write_text('''Shader "GolfArcade/TennisRooftopSky"
{
 Properties { _Panorama("Authored upper sky / cirrus",2D)="white"{} _Rotation("Heading",Float)=0 _Exposure("Exposure",Float)=.9 }
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
   CBUFFER_START(UnityPerMaterial)float _Rotation,_Exposure;CBUFFER_END
   struct A{float4 p:POSITION;};struct V{float4 p:SV_POSITION;float3 d:TEXCOORD0;};
   V vert(A a){V o;o.p=TransformObjectToHClip(a.p.xyz);o.d=a.p.xyz;return o;}
   half4 frag(V i):SV_Target{
    float3 d=normalize(i.d);
    float longitude=atan2(d.z,d.x)/6.2831853+.5+_Rotation/360;
    // Only the photograph's sky above its cloud horizon maps to the dome.
    // Lower cloud shapes remain the existing horizontal cloud plane, never a spherical ground.
    float latitude=clamp(.535+asin(max(d.y,0))/3.14159265*.88,.535,.975);
    float denominator=max(dot(d.xz,d.xz),.00001)*6.2831853;
    float2 gx=float2((d.x*ddx(d.z)-d.z*ddx(d.x))/denominator,ddx(latitude));
    float2 gy=float2((d.x*ddy(d.z)-d.z*ddy(d.x))/denominator,ddy(latitude));
    float u=frac(longitude);
    half3 sky=SAMPLE_TEXTURE2D_GRAD(_Panorama,sampler_Panorama,float2(u,latitude),gx,gy).rgb;
    half3 edges=(SAMPLE_TEXTURE2D_GRAD(_Panorama,sampler_Panorama,float2(.012,latitude),gx,gy).rgb+SAMPLE_TEXTURE2D_GRAD(_Panorama,sampler_Panorama,float2(.988,latitude),gx,gy).rgb)*.5;
    sky=lerp(edges,sky,smoothstep(0,.035,min(u,1-u)));
    half3 lower=half3(.34,.34,.46);
    sky=lerp(lower,sky,smoothstep(-.12,.015,d.y));
    return half4(sky*_Exposure,1);
   }
   ENDHLSL
  }
 }
 Fallback Off
}
''')

f=p/'Unity/Assets/Resources/Tennis/Shaders/TennisTowerAtmosphere.shader';s=f.read_text()
s=s.replace('_CloudTops("Cloud base atmosphere"', '_SkyPanorama("Reflected upper sky",2D)="white"{} _SkyRotation("Sky reflection heading",Float)=15\n  _CloudTops("Cloud base atmosphere"')
s=s.replace('TEXTURE2D(_CloudTops);SAMPLER(sampler_CloudTops);','TEXTURE2D(_CloudTops);SAMPLER(sampler_CloudTops);TEXTURE2D(_SkyPanorama);SAMPLER(sampler_SkyPanorama);')
s=s.replace('float _CloudScale;','float _CloudScale,_SkyRotation;')
s=s.replace('SurfaceData s=(SurfaceData)0;s.albedo=SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,i.uv).rgb*_BaseColor.rgb;', '''half4 facade=SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,i.uv);
    half glass=facade.a;
    SurfaceData s=(SurfaceData)0;s.albedo=facade.rgb*_BaseColor.rgb;''')
s=s.replace('s.smoothness=_Smoothness;s.metallic=_Metallic;', 's.smoothness=lerp(.22,_Smoothness,glass);s.metallic=_Metallic;')
s=s.replace('half3 colour=UniversalFragmentPBR(d,s).rgb;', '''half3 colour=UniversalFragmentPBR(d,s).rgb;
    float3 reflected=reflect(-d.viewDirectionWS,d.normalWS);
    float2 skyUV=float2(frac(atan2(reflected.z,reflected.x)/6.2831853+.5+_SkyRotation/360),clamp(.535+asin(max(reflected.y,0))/3.14159265*.88,.535,.975));
    half3 sky=SAMPLE_TEXTURE2D_LOD(_SkyPanorama,sampler_SkyPanorama,skyUV,3).rgb;
    half fresnel=pow(1-saturate(dot(d.normalWS,d.viewDirectionWS)),5);
    // A bounded sky reflection on glazing only. Wall/stone mullions keep their diffuse finish.
    colour=lerp(colour,sky*.72,glass*(.13+fresnel*.42));''')
f.write_text(s)

f=p/'Unity/Assets/Scripts/Tennis/TennisVenueBuilder.Skyscraper.cs';s=f.read_text()
s=s.replace('new Vector3(.32f, .40f, .57f)', 'new Vector3(.48f, .48f, .60f)')
s=s.replace('return cell(cu - cx, cv - cy, cx, cy);', '''var result=cell(cu - cx, cv - cy, cx, cy);
                        var a=result.a;
                        // Facade alpha stores glazing membership, not transparency.
                        bool glazed=(a.b>a.r*1.08f || a.g>a.r*1.20f) && Mathf.Max(a.r,Mathf.Max(a.g,a.b))<.91f;
                        a.a=glazed?1:0;return (a,result.e);''')
s=s.replace('wrapped.SetFloat("_Smoothness",smooth);', 'wrapped.SetFloat("_Smoothness",smooth);wrapped.SetTexture("_SkyPanorama",Resources.Load<Texture2D>("Tennis/Premium/SkyRooftop"));wrapped.SetFloat("_SkyRotation",-90);')
s=s.replace('RenderSettings.ambientEquatorColor = new Color(.38f, .43f, .53f);', 'RenderSettings.ambientEquatorColor = new Color(.30f, .35f, .46f);')
s=s.replace('RenderSettings.fogStartDistance = 230; RenderSettings.fogEndDistance = 5200;', 'RenderSettings.fogStartDistance = 150; RenderSettings.fogEndDistance = 2300;')
s=s.replace('sky.SetFloat("_Rotation",15);sky.SetFloat("_Exposure",.88f);', 'sky.SetFloat("_Rotation",-90);sky.SetFloat("_Exposure",.90f);')
f.write_text(s)
