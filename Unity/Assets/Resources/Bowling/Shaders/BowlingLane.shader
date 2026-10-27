// Lacquered lane wood: URP PBR (albedo, normal, metallic/smoothness map like Lit) plus the planar mirror
// BowlingLaneMirror renders into _BowlingLaneReflection (a proper camera under the floor, so its image is the
// mirror flipped left-right: sampled at 1 - u). Fresnel-weighted, rippled a little by the board normals.
Shader "GolfArcade/BowlingLane"
{
 Properties
 {
  _BaseMap("Albedo", 2D) = "white" {}
  _BaseColor("Tint", Color) = (1,1,1,1)
  _BumpMap("Normal", 2D) = "bump" {}
  _BumpScale("Normal strength", Float) = .35
  _MetallicGlossMap("Metallic (R) Smoothness (A)", 2D) = "white" {}
  _Smoothness("Smoothness", Range(0,1)) = .95
  _Mirror("Mirror strength", Range(0,2)) = .6
  _MirrorDistort("Mirror ripple", Range(0,.05)) = .006
  _MirrorStreak("Mirror streak (screen v per tap)", Range(0,.02)) = .006
 }
 SubShader
 {
  Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
  Pass
  {
   Name "ForwardLit" Tags { "LightMode"="UniversalForward" }
   HLSLPROGRAM
   #pragma target 3.0
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
   #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
   #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
   #pragma multi_compile_fragment _ _SHADOWS_SOFT
   #pragma multi_compile_fragment _ _REFLECTION_PROBE_BOX_PROJECTION
   #pragma multi_compile_fog
   #pragma multi_compile_instancing
   #define _NORMALMAP 1
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

   TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
   TEXTURE2D(_BumpMap); TEXTURE2D(_MetallicGlossMap);
   TEXTURE2D(_BowlingLaneReflection); SAMPLER(sampler_BowlingLaneReflection);
   CBUFFER_START(UnityPerMaterial)
    float4 _BaseMap_ST; half4 _BaseColor; half _BumpScale, _Smoothness, _Mirror, _MirrorDistort, _MirrorStreak;
   CBUFFER_END

   struct A { float4 p:POSITION; float3 n:NORMAL; float4 t:TANGENT; float2 uv:TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };
   struct V { float4 p:SV_POSITION; float2 uv:TEXCOORD0; float3 w:TEXCOORD1; half3 n:TEXCOORD2; half4 t:TEXCOORD3; half fog:TEXCOORD4; };

   V vert(A a)
   {
    UNITY_SETUP_INSTANCE_ID(a); V o;
    o.w = TransformObjectToWorld(a.p.xyz); o.p = TransformWorldToHClip(o.w);
    VertexNormalInputs ni = GetVertexNormalInputs(a.n, a.t);
    o.n = ni.normalWS; o.t = half4(ni.tangentWS, a.t.w * GetOddNegativeScale());
    o.uv = TRANSFORM_TEX(a.uv, _BaseMap); o.fog = ComputeFogFactor(o.p.z);
    return o;
   }

   half4 frag(V i) : SV_Target
   {
    half4 alb = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv) * _BaseColor;
    half3 nts = UnpackNormalScale(SAMPLE_TEXTURE2D(_BumpMap, sampler_BaseMap, i.uv), _BumpScale);
    half4 mg = SAMPLE_TEXTURE2D(_MetallicGlossMap, sampler_BaseMap, i.uv);
    half3 bit = i.t.w * cross(i.n, i.t.xyz);
    half3 nws = normalize(TransformTangentToWorld(nts, half3x3(i.t.xyz, bit, i.n)));

    InputData d = (InputData)0;
    d.positionWS = i.w; d.normalWS = nws; d.viewDirectionWS = SafeNormalize(GetWorldSpaceViewDir(i.w));
    d.shadowCoord = TransformWorldToShadowCoord(i.w); d.fogCoord = i.fog; d.bakedGI = SampleSH(nws);
    d.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.p); d.shadowMask = half4(1,1,1,1);

    SurfaceData s = (SurfaceData)0;
    s.albedo = alb.rgb; s.metallic = mg.r; s.smoothness = mg.a * _Smoothness; s.normalTS = nts; s.occlusion = 1; s.alpha = 1;
    half4 c = UniversalFragmentPBR(d, s);

    // the mirror: what stands on the lane, seen in the lacquer
    float2 suv = d.normalizedScreenSpaceUV; suv.x = 1 - suv.x;
    suv += nts.xy * _MirrorDistort;
    // lacquer smears what it mirrors along the lane: a short vertical blur on screen
    half3 refl = 0;
    [unroll] for (int k = -2; k <= 3; k++)
        refl += SAMPLE_TEXTURE2D(_BowlingLaneReflection, sampler_BowlingLaneReflection, suv + float2(0, k * _MirrorStreak)).rgb;
    refl /= 6;
    half nv = saturate(dot(nws, d.viewDirectionWS));
    half fres = .08 + .92 * pow(1 - nv, 4);
    c.rgb += refl * _Mirror * fres * s.smoothness;
    c.rgb = MixFog(c.rgb, i.fog);
    return c;
   }
   ENDHLSL
  }
  UsePass "Universal Render Pipeline/Lit/ShadowCaster"
  UsePass "Universal Render Pipeline/Lit/DepthOnly"
  UsePass "Universal Render Pipeline/Lit/DepthNormals"
 }
 FallBack "Universal Render Pipeline/Lit"
}
