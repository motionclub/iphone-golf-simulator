// Chat 10 island shore: turquoise shallows fading to the deep sea + an animated foam ring at the coastline.
// Vertex colour r = foam weight, g = shallows alpha; uv.x = metres along the coast / 6, uv.y = metres out / foam width.
Shader "GolfArcade/MajesticFoam"
{
    Properties
    {
        _Shallow("Shallows colour", Color) = (.12, .8, .8, 1)
        _FoamColor("Foam colour", Color) = (1, 1, 1, 1)
        _ShallowAlpha("Shallows strength", Range(0, 1)) = .72
        _FoamSpeed("Foam speed", Float) = .35
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent-10" "RenderPipeline"="UniversalPipeline" }
        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off
        Pass
        {
            Name "ForwardLit" Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            CBUFFER_START(UnityPerMaterial)
                half4 _Shallow, _FoamColor; half _ShallowAlpha, _FoamSpeed;
            CBUFFER_END
            struct A { float4 p:POSITION; half4 c:COLOR; float2 uv:TEXCOORD0; };
            struct V { float4 p:SV_POSITION; half4 c:COLOR; float2 uv:TEXCOORD0; half fog:TEXCOORD1; };
            V vert(A a) { V o; o.p = TransformObjectToHClip(a.p.xyz); o.c = a.c; o.uv = a.uv; o.fog = ComputeFogFactor(o.p.z); return o; }
            float h1(float x) { return frac(sin(x * 127.1) * 43758.5453); }
            float n1(float x) { float i = floor(x), f = frac(x); f = f * f * (3 - 2 * f); return lerp(h1(i), h1(i + 1), f); }
            half4 frag(V i) : SV_Target
            {
                float t = _Time.y * _FoamSpeed;
                float wob = n1(i.uv.x * 1.7) * .6 + n1(i.uv.x * 5.3 + 3) * .25;
                // two soft bands rolling outward from the coast, plus a steady lip at the waterline
                float bands = smoothstep(.55, .9, sin((i.uv.y * 2.1 - t * 2.0 + wob) * 6.2832) * .5 + .5) * (1 - saturate(i.uv.y));
                float lip = 1 - smoothstep(0, .28, abs(i.uv.y - .05 + wob * .08));
                float foam = saturate(lip * .95 + bands * .7) * i.c.r;
                Light sun = GetMainLight();
                half3 lit = _Shallow.rgb * (sun.color * .55 + SampleSH(half3(0, 1, 0)) * .65);
                half3 foamLit = _FoamColor.rgb * (sun.color * .6 + SampleSH(half3(0, 1, 0)) * .7);
                half a = i.c.g * _ShallowAlpha;
                half3 col = lerp(lit, foamLit, foam);
                half alpha = saturate(a + foam * .9);
                col = MixFog(col, i.fog);
                return half4(col, alpha);
            }
            ENDHLSL
        }
    }
}
