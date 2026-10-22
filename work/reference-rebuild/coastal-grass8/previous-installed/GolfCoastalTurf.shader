Shader "GolfArcade/GolfCoastalTurf"
{
 Properties {
  _RootColor("Dense cut grass root",Color)=(.15,.34,.065,1)
  _TipColor("Fresh cut blade",Color)=(.36,.55,.12,1)
  _Smoothness("Blade sheen",Range(0,1))=.12
 }
 SubShader {
  Tags {"RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry"}
  Cull Off
  Pass {
   Name "ForwardLit" Tags {"LightMode"="UniversalForward"}
   HLSLPROGRAM
   #pragma target 3.0
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_instancing
   #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
   #pragma multi_compile_fragment _ _SHADOWS_SOFT
   #pragma multi_compile_fog
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
   #include "../../Tennis/Shaders/HeroLighting.hlsl"
   CBUFFER_START(UnityPerMaterial)
    half4 _RootColor,_TipColor;half _Smoothness;
   CBUFFER_END
   float4 _GolfWind;
   struct A {float4 p:POSITION;float3 n:NORMAL;float2 role:TEXCOORD0;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct V {float4 p:SV_POSITION;float3 w:TEXCOORD0;half3 n:TEXCOORD1;half2 role:TEXCOORD2;half fog:TEXCOORD3;UNITY_VERTEX_INPUT_INSTANCE_ID};
   V vert(A a) {
    V o=(V)0;UNITY_SETUP_INSTANCE_ID(a);UNITY_TRANSFER_INSTANCE_ID(a,o);
    o.w=TransformObjectToWorld(a.p.xyz);
    // A few millimeters of motion keep short groomed grass quiet in wind.
    o.w.xz+=_GolfWind.xz*a.role.y*.010*(.5+.5*sin(_GolfWind.w*1.9+dot(o.w.xz,float2(.73,.51))));
    o.p=TransformWorldToHClip(o.w);o.n=TransformObjectToWorldNormal(a.n);o.role=a.role;o.fog=ComputeFogFactor(o.p.z);return o;
   }
   half4 frag(V i,FRONT_FACE_TYPE face:FRONT_FACE_SEMANTIC):SV_Target {
    UNITY_SETUP_INSTANCE_ID(i);
    half3 normal=normalize(i.n)*IS_FRONT_VFACE(face,1,-1);
    Light sun=HeroMain(GetMainLight());
    #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
    sun.shadowAttenuation=MainLightRealtimeShadow(ComputeScreenPos(TransformWorldToHClip(i.w)));
    #elif defined(MAIN_LIGHT_CALCULATE_SHADOWS)
    sun.shadowAttenuation=MainLightRealtimeShadow(TransformWorldToShadowCoord(i.w));
    #endif
    half3 albedo=lerp(_RootColor.rgb,_TipColor.rgb,saturate(i.role.y))*(.82h+.18h*i.role.x);
    half rooted=lerp(.92h,1.0h,saturate(i.role.y*2));
    // Thin grass transmits light from both faces. The previous one-sided
    // blade response made the same groomed field look like black stubble.
    half wrapped=saturate((abs(dot(normal,sun.direction))+.35h)/1.35h);
    half3 colour=albedo*(HeroAmbient(half3(0,1,0))+sun.color*wrapped*sun.shadowAttenuation)*rooted;
    // Restrained back-light transmission, no plastic-white highlight.
    colour+=albedo*sun.color*saturate(-dot(normal,sun.direction))*.14h*sun.shadowAttenuation;
    half3 halfVector=SafeNormalize(sun.direction+SafeNormalize(GetWorldSpaceViewDir(i.w)));
    colour+=sun.color*pow(saturate(dot(normal,halfVector)),24.0h)*_Smoothness*.025h*sun.shadowAttenuation;
    return half4(MixFog(colour,i.fog),1);
   }
   ENDHLSL
  }
 }
 Fallback Off
}
