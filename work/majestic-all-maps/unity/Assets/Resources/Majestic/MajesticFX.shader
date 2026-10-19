// Chat 10: FX cards of the landmark kit (waterfalls, lava falls, plumes, smoke, lighthouse beam, foam strips).
// Vertex colour = colour + alpha, UV0 = card uv (y scrolls), UV2.x = glow. Transparent, double-sided, fogged.
Shader "GolfArcade/MajesticFX"
{
    Properties { _Scroll("Scroll speed", Float) = .35 _Glow("Glow", Float) = 1.6 _Tint("Tint", Color) = (1,1,1,1) }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "RenderPipeline"="UniversalPipeline" }
        Blend SrcAlpha OneMinusSrcAlpha ZWrite Off Cull Off
        Pass
        {
            Name "ForwardLit" Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            CBUFFER_START(UnityPerMaterial) half _Scroll, _Glow; half4 _Tint; CBUFFER_END
            struct A { float4 p:POSITION; half4 c:COLOR; float2 uv:TEXCOORD0; float2 uv2:TEXCOORD2; };
            struct V { float4 p:SV_POSITION; half4 c:COLOR; float2 uv:TEXCOORD0; half glow:TEXCOORD1; half fog:TEXCOORD2; };
            V vert(A a) { V o; o.p = TransformObjectToHClip(a.p.xyz); o.c = a.c; o.uv = a.uv; o.glow = a.uv2.x; o.fog = ComputeFogFactor(o.p.z); return o; }
            float h(float2 p) { return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453); }
            float n(float2 p) { float2 i = floor(p), f = frac(p); f = f * f * (3 - 2 * f); return lerp(lerp(h(i), h(i + float2(1, 0)), f.x), lerp(h(i + float2(0, 1)), h(i + 1), f.x), f.y); }
            half4 frag(V i) : SV_Target
            {
                float2 uv = i.uv; uv.y -= _Time.y * _Scroll;
                float s = n(uv * float2(6, 3)) * .6 + n(uv * float2(14, 7)) * .4;           // streaks / billows
                half a = i.c.a * _Tint.a * saturate(.45 + s * .9);
                Light sun = GetMainLight();
                half3 col = i.c.rgb * _Tint.rgb * (sun.color * .5 + SampleSH(half3(0, 1, 0)) * .7 + i.glow * _Glow);   // glow tinted too (round 13: orange lava falls)
                return half4(MixFog(col, i.fog), a);
            }
            ENDHLSL
        }
    }
}
