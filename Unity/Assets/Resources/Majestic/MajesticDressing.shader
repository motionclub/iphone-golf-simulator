// Chat 9 majestic dressing: bunting, pennants, sails, blossoms and birds. Vertex-coloured, lit by the
// main light + SH ambient, fogged like the venue, double-sided. Motion is all in the vertex shader:
//   uv0.x = sway weight (0 at the fixed edge, 1 at the free tip), uv0.y = phase,
//   uv1.x = flap weight (birds' wing tips), uv1.y = flap speed.
//   uv2.x = glow (emission multiplier, for lava, bulbs, lit windows; bloom picks it up).
// Wind is the venue's one global breeze (_GolfWind: xz push, w time), shared with palms and grass.
Shader "GolfArcade/MajesticDressing"
{
    Properties
    {
        _Flutter("Flutter amount", Range(0,1)) = .35
        _Sheen("Fabric sheen", Range(0,1)) = .15
        _Translucency("Back-light glow", Range(0,1)) = .35
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        Cull Off
        Pass
        {
            Name "ForwardLit" Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            CBUFFER_START(UnityPerMaterial)
                half _Flutter, _Sheen, _Translucency;
            CBUFFER_END
            float4 _GolfWind;
            struct A { float4 p:POSITION; float3 n:NORMAL; half4 c:COLOR; float2 uv:TEXCOORD0; float2 uv1:TEXCOORD1; float2 uv2:TEXCOORD2; };
            struct V { float4 p:SV_POSITION; float3 w:TEXCOORD0; half3 n:TEXCOORD1; half3 c:TEXCOORD2; half fog:TEXCOORD3; half glow:TEXCOORD4; };

            float3 Move(float3 w, float2 uv, float2 uv1)
            {
                float t = _GolfWind.w;
                float2 push = _GolfWind.xz * 18;                      // metres of lean per unit wind at the tip
                float wave = sin(t * 5.3 + uv.y * 6.28 + w.x * .7) * .5 + .5;
                w.xz += push * uv.x * (.55 + .45 * wave);
                w.y += (sin(t * 7.9 + uv.y * 11.0) * _Flutter * .06 - length(push) * .25) * uv.x;
                w.y += sin(t * uv1.y + uv.y * 6.28) * uv1.x;           // wing flap
                return w;
            }
            V vert(A a)
            {
                V o;
                float3 w = TransformObjectToWorld(a.p.xyz);
                w = Move(w, a.uv, a.uv1);
                o.w = w; o.p = TransformWorldToHClip(w);
                o.n = TransformObjectToWorldNormal(a.n);
                o.c = a.c.rgb; o.glow = a.uv2.x;
                o.fog = ComputeFogFactor(o.p.z);
                return o;
            }
            half4 frag(V i, bool front:SV_IsFrontFace) : SV_Target
            {
                half3 n = normalize(i.n) * (front ? 1 : -1);
                Light sun = GetMainLight(TransformWorldToShadowCoord(i.w));
                half nl = dot(n, sun.direction);
                half lit = saturate(nl) * sun.shadowAttenuation;
                half back = saturate(-nl) * _Translucency * sun.shadowAttenuation;   // thin cloth glows from behind
                half3 ambient = SampleSH(n);
                half3 v = normalize(GetWorldSpaceViewDir(i.w));
                half sheen = pow(1 - saturate(dot(n, v)), 3) * _Sheen;
                half3 col = i.c * (ambient + sun.color * (lit + back)) + sun.color * sheen * .25 + i.c * i.glow;
                col = MixFog(col, i.fog);
                return half4(col, 1);
            }
            ENDHLSL
        }
        Pass
        {
            Name "ShadowCaster" Tags { "LightMode"="ShadowCaster" }
            ColorMask 0
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            float3 _LightDirection;
            float4 _GolfWind;
            struct A { float4 p:POSITION; float3 n:NORMAL; float2 uv:TEXCOORD0; float2 uv1:TEXCOORD1; };
            float4 vert(A a) : SV_POSITION
            {
                float3 w = TransformObjectToWorld(a.p.xyz);
                float2 push = _GolfWind.xz * 18;
                w.xz += push * a.uv.x * .8;
                float3 n = TransformObjectToWorldNormal(a.n);
                float4 p = TransformWorldToHClip(ApplyShadowBias(w, n, _LightDirection));
                #if UNITY_REVERSED_Z
                    p.z = min(p.z, UNITY_NEAR_CLIP_VALUE);
                #else
                    p.z = max(p.z, UNITY_NEAR_CLIP_VALUE);
                #endif
                return p;
            }
            half4 frag() : SV_Target { return 0; }
            ENDHLSL
        }
    }
}
