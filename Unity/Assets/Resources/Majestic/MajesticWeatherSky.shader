// Majestic weather (chat W): the sky pieces. One shader, four modes (material float _Mode):
// 0 rainbow (additive; uv.x across the band, uv.y along it, uv2.x = 1 the faint secondary bow),
// 1 sunbeams (additive; uv.x along the ray from the sun, uv.y across),
// 2 storm wall (alpha; uv.x azimuth 0..1, uv.y -3°..30°: billowing dark mass, rain shafts below its base, lit by lightning),
// 3 lava bombs + their trails (additive orange glow).
// Camera-attached pieces at ~60 % of the far clip: behind the course, in front of the far-field sky; no depth reads.
Shader "GolfArcade/MajesticWeatherSky"
{
    Properties
    {
        _Mode("Mode", Float) = 0
        _Amount("Amount", Range(0,2)) = 0
        _Color("Colour", Color) = (1,1,1,1)
        _Flash("Flash", Range(0,1)) = 0
        _Glow("Underglow (lava)", Color) = (0,0,0,0)
        [Enum(UnityEngine.Rendering.BlendMode)] _SrcBlend("Src", Float) = 1
        [Enum(UnityEngine.Rendering.BlendMode)] _DstBlend("Dst", Float) = 1
        [Enum(UnityEngine.Rendering.CompareFunction)] _ZTest("ZTest", Float) = 4
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent-380" "IgnoreProjector"="True" }
        Blend [_SrcBlend] [_DstBlend] ZWrite Off ZTest [_ZTest] Cull Off
        Pass
        {
            Name "WeatherSky" Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial) half4 _Color, _Glow; float _Mode, _Amount, _Flash, _SrcBlend, _DstBlend, _ZTest; CBUFFER_END
            struct A { float4 p : POSITION; float2 uv : TEXCOORD0; float2 uv2 : TEXCOORD1; half4 c : COLOR; };
            struct V { float4 p : SV_POSITION; float2 uv : TEXCOORD0; float2 uv2 : TEXCOORD1; half4 c : COLOR; };
            V vert(A a) { V o; o.p = TransformObjectToHClip(a.p.xyz); o.uv = a.uv; o.uv2 = a.uv2; o.c = a.c; return o; }

            float H(float2 p) { p = frac(p * float2(127.1, 311.7)); p += dot(p, p + 19.19); return frac(p.x * p.y); }
            float N(float2 p) { float2 i = floor(p), f = frac(p); f = f * f * (3 - 2 * f);
                return lerp(lerp(H(i), H(i + float2(1, 0)), f.x), lerp(H(i + float2(0, 1)), H(i + 1), f.x), f.y); }
            float Fbm(float2 p) { return N(p) * .62 + N(p * 2.3 + 1.7) * .38; }
            half3 Spectrum(float x) // 0 violet .. 1 red
            {
                float h = (1 - saturate(x)) * .78;
                return saturate(abs(frac(h + float3(0, 2.0 / 3, 1.0 / 3)) * 6 - 3) - 1);
            }

            half4 frag(V i) : SV_Target
            {
                float t = _Time.y;
                if (_Mode < .5)
                {
                    float x = i.uv.x; bool second = i.uv2.x > .5;
                    float band = sin(3.14159 * x); band *= band;
                    float ends = smoothstep(0, .3, i.uv.y) * smoothstep(1, .7, i.uv.y);
                    half3 c = Spectrum(second ? 1 - x : x);
                    float a = band * ends * _Amount * (second ? .3 : 1);
                    return half4(c * a, 0);
                }
                if (_Mode < 1.5)
                {
                    float along = saturate(i.uv.x), across = i.uv.y;
                    float a = pow(1 - along, 1.6) * exp(-across * across * 2.5) * (.75 + .25 * sin(t * .7 + i.uv.x * 3));
                    return half4(_Color.rgb * a * _Amount, 0);
                }
                if (_Mode < 2.5)
                {
                    float u = i.uv.x, v = i.uv.y;
                    float top = .5 + .32 * N(float2(u * 6 + t * .004, 1.3));
                    float body = Fbm(float2(u * 9 + t * .006, v * 3.5 - t * .01));
                    float mass = smoothstep(top, top - .22, v) * (.75 + .25 * body);
                    float base = .22 + .06 * N(float2(u * 14, 2));
                    float shafts = smoothstep(.45, .8, N(float2(u * 34 + v * 3 - t * .05, 5))) * smoothstep(base + .02, base - .12, v) * smoothstep(-.02, .1, v);
                    float edge = smoothstep(0, .22, u) * smoothstep(1, .78, u);
                    float a = saturate(mass * .94 + shafts * .45) * edge * saturate(_Amount);
                    half3 c = _Color.rgb * (.7 + .55 * body) * (1 + .5 * smoothstep(top - .2, top, v));
                    float inner = _Flash * smoothstep(.35, .75, body) * (1 - v * .5);
                    c += half3(.75, .78, 1) * inner * 1.6;
                    c += _Glow.rgb * pow(saturate(1 - v * 1.6), 2) * (.6 + .4 * body);   // lit from below (lava, eruption)
                    return half4(c, a);
                }
                return half4(half3(1, .45, .12) * 2.2 * _Amount * i.c.a, 0);
            }
            ENDHLSL
        }
    }
}
