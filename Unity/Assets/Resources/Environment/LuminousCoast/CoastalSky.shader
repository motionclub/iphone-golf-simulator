Shader "GolfArcade/LuminousCoastSky"
{
 Properties { _Panorama("Distant coastal panorama",2D)="white"{} _Rotation("Heading",Float)=0 _Exposure("Exposure",Float)=1 _LongitudeScale("Longitude scale",Float)=1 _AltitudeScale("Altitude scale",Float)=1 _LatitudeOffset("Horizon registration",Float)=0 }
 SubShader {
  Tags {"Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" "RenderPipeline"="UniversalPipeline"}
  Cull Off ZWrite Off
  Pass {
   HLSLPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   TEXTURE2D(_Panorama);SAMPLER(sampler_Panorama);
   CBUFFER_START(UnityPerMaterial) float _Rotation,_Exposure,_LongitudeScale,_AltitudeScale,_LatitudeOffset; CBUFFER_END
   struct A {float4 p:POSITION;};struct V {float4 p:SV_POSITION;float3 d:TEXCOORD0;};
   V vert(A a){V o;o.p=TransformObjectToHClip(a.p.xyz);o.d=a.p.xyz;return o;}
   half4 frag(V i):SV_Target {
    float3 d=normalize(i.d);
    float u=frac(atan2(d.z,d.x)/6.2831853*_LongitudeScale+.5+_Rotation/360);
    float v=clamp(.5+asin(clamp(d.y,-1,1))/3.14159265*_AltitudeScale+_LatitudeOffset,.002,.998);
    float den=max(dot(d.xz,d.xz),.00001)*6.2831853;
    float2 gx=float2((d.x*ddx(d.z)-d.z*ddx(d.x))/den*_LongitudeScale,ddx(v));
    float2 gy=float2((d.x*ddy(d.z)-d.z*ddy(d.x))/den*_LongitudeScale,ddy(v));
    half3 c=SAMPLE_TEXTURE2D_GRAD(_Panorama,sampler_Panorama,float2(u,v),gx,gy).rgb;
    half3 edges=(SAMPLE_TEXTURE2D_GRAD(_Panorama,sampler_Panorama,float2(.01,v),gx,gy).rgb+SAMPLE_TEXTURE2D_GRAD(_Panorama,sampler_Panorama,float2(.99,v),gx,gy).rgb)*.5;
    c=lerp(edges,c,smoothstep(0,.025,min(u,1-u)));
    return half4(c*_Exposure,1);
   }
   ENDHLSL
  }
 }
}
