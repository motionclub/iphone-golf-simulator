Shader "GolfArcade/LuminousCoastLandscape"
{
 Properties { _BaseColor("Tint",Color)=(1,1,1,1) }
 SubShader {
  Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" }
  Pass {
   Tags { "LightMode"="UniversalForward" }
   HLSLPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_fog
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
   CBUFFER_START(UnityPerMaterial) half4 _BaseColor; CBUFFER_END
   struct A { float4 p:POSITION; float3 n:NORMAL; half4 c:COLOR; };
   struct V { float4 p:SV_POSITION; float3 w:TEXCOORD0; half3 n:TEXCOORD1; half4 c:COLOR; float fog:TEXCOORD2; };
   V vert(A a) { V o; o.w=TransformObjectToWorld(a.p.xyz);o.p=TransformWorldToHClip(o.w);o.n=TransformObjectToWorldNormal(a.n);o.c=a.c;o.fog=ComputeFogFactor(o.p.z);return o; }
   half4 frag(V i):SV_Target {
    half3 n=normalize(i.n); Light sun=GetMainLight();
    half diffuse=saturate(dot(n,sun.direction));
    half3 ambient=half3(.28,.40,.47);
    half3 albedo=SRGBToLinear(i.c.rgb);
    half3 c=albedo*_BaseColor.rgb*(ambient+sun.color*(.18+diffuse*.82));
    float dist=distance(i.w,_WorldSpaceCameraPos);
    half haze=saturate((dist-450)/1800)*.22;
    c=lerp(c,half3(.29,.48,.58),haze);
    return half4(MixFog(c,lerp(1,i.fog,.22)),1);
   }
   ENDHLSL
  }
 }
}
