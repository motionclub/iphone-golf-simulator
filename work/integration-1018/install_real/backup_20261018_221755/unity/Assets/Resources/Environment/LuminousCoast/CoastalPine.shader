Shader "GolfArcade/LuminousCoastalPine" {
 SubShader {
  Tags {"RenderType"="Opaque" "Queue"="Geometry" "RenderPipeline"="UniversalPipeline"}
  Cull Off ZWrite On
  HLSLINCLUDE
  #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
  #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
  float4 _GolfWind;
  struct A {float4 p:POSITION;float3 n:NORMAL;half4 c:COLOR;UNITY_VERTEX_INPUT_INSTANCE_ID};
  struct V {float4 p:SV_POSITION;float3 w:TEXCOORD0;half3 n:TEXCOORD1;half3 c:TEXCOORD2;half fog:TEXCOORD3;};
  V vert(A a) {UNITY_SETUP_INSTANCE_ID(a);V o;o.w=TransformObjectToWorld(a.p.xyz);o.w.xz+=_GolfWind.xz*a.c.a*.3*sin(_GolfWind.w*1.4+dot(o.w.xz,float2(.2,.17)));o.p=TransformWorldToHClip(o.w);o.n=TransformObjectToWorldNormal(a.n);o.c=a.c.rgb;o.fog=ComputeFogFactor(o.p.z);return o;}
  ENDHLSL
  Pass {
   Name "ForwardLit" Tags {"LightMode"="UniversalForward"}
   HLSLPROGRAM
   #pragma target 3.0
   #pragma multi_compile_instancing
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
   #pragma multi_compile_fragment _ _SHADOWS_SOFT
   #pragma multi_compile_fog
   half4 frag(V i):SV_Target {
    half3 n=normalize(i.n);Light sun=GetMainLight(TransformWorldToShadowCoord(i.w));
    half wrap=saturate((dot(n,sun.direction)+.3)/1.3);
    half3 ambient=max(SampleSH(n),half3(.14,.19,.18))*(.65+.35*saturate(n.y*.5+.5));
    half3 color=SRGBToLinear(i.c)*(ambient+sun.color*wrap*lerp(.28,1,sun.shadowAttenuation));
    return half4(MixFog(color,i.fog),1);
   }
   ENDHLSL
  }
  Pass {
   Name "ShadowCaster" Tags {"LightMode"="ShadowCaster"} ColorMask 0 ZTest LEqual
   HLSLPROGRAM
   #pragma multi_compile_instancing
   #pragma vertex shadow
   #pragma fragment frag
   float3 _LightDirection;
   V shadow(A a){V o=vert(a);o.p=TransformWorldToHClip(ApplyShadowBias(o.w,o.n,_LightDirection));
    #if UNITY_REVERSED_Z
    o.p.z=min(o.p.z,UNITY_NEAR_CLIP_VALUE*o.p.w);
    #else
    o.p.z=max(o.p.z,UNITY_NEAR_CLIP_VALUE*o.p.w);
    #endif
    return o;}
   half4 frag(V i):SV_Target{return 0;}
   ENDHLSL
  }
  Pass {Name "DepthOnly" Tags {"LightMode"="DepthOnly"} ColorMask R
   HLSLPROGRAM
   #pragma multi_compile_instancing
   #pragma vertex vert
   #pragma fragment frag
   half4 frag(V i):SV_Target{return 0;}
   ENDHLSL
  }
 }
}
