Shader "GolfArcade/GolfResortSky"
{
 Properties { _Panorama("Authored equirectangular sky",2D)="white"{} _Rotation("Heading",Float)=0 _Exposure("Exposure",Float)=1 _CloudCompression("Cloud altitude compression",Float)=1 _LongitudeScale("Cloud angular size",Float)=1 _DayHaze("Daylight haze",Range(0,1))=0 }
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
   CBUFFER_START(UnityPerMaterial) float _Rotation,_Exposure,_CloudCompression,_LongitudeScale,_DayHaze; CBUFFER_END
   struct A {float4 p:POSITION;};struct V {float4 p:SV_POSITION;float3 direction:TEXCOORD0;};
   V vert(A a){V o;o.p=TransformObjectToHClip(a.p.xyz);o.direction=a.p.xyz;return o;}
   half4 frag(V i):SV_Target {
    float3 d=normalize(i.direction);
    float longitude=(atan2(d.z,d.x)/6.2831853+.5+_Rotation/360.0)*_LongitudeScale;
    float latitude=clamp(.5+asin(clamp(d.y,-1.0,1.0))/3.14159265*_CloudCompression,.001,.999);
    // Analytic longitude gradients do not jump at atan2 or frac seams. Implicit
    // gradients created the one-pixel bright dashed stripe in actual hole17.
    float denominator=max(dot(d.xz,d.xz),.00001)*6.2831853;
    float duX=(d.x*ddx(d.z)-d.z*ddx(d.x))/denominator*_LongitudeScale;
    float duY=(d.x*ddy(d.z)-d.z*ddy(d.x))/denominator*_LongitudeScale;
    float2 gradientX=float2(duX,ddx(latitude)),gradientY=float2(duY,ddy(latitude));
    float2 uv=float2(frac(longitude),latitude);
    half3 sky=SAMPLE_TEXTURE2D_GRAD(_Panorama,sampler_Panorama,uv,gradientX,gradientY).rgb;
    half3 edges=(SAMPLE_TEXTURE2D_GRAD(_Panorama,sampler_Panorama,float2(.012,latitude),gradientX,gradientY).rgb
               +SAMPLE_TEXTURE2D_GRAD(_Panorama,sampler_Panorama,float2(.988,latitude),gradientX,gradientY).rgb)*.5;
    sky=lerp(edges,sky,smoothstep(0,.035,min(uv.x,1-uv.x)));
    // Apply daylight treatment to clear blue pixels. Authored white cloud
    // highlights keep their luminance rather than taking a blue haze tint.
    half blueOnly=saturate((sky.b-sky.r)*3)*(1-smoothstep(.38h,.68h,min(sky.r,sky.g)));
    half altitude=smoothstep(0,.65,saturate(d.y));
    half3 haze=lerp(half3(.32h,.54h,.72h),half3(.055h,.245h,.57h),altitude);
    sky=lerp(sky,haze,_DayHaze*blueOnly);
    return half4(sky*_Exposure,1);
   }
   ENDHLSL
  }
 }
 Fallback Off
}
