// Majestic weather (chat W): the wet court's mirror. A flat sheet laid just over the tennis deck, drawn after the
// opaques: screen-space reflections of what stands on and around the court (players, net, umpire chair, lamps,
// buildings, lights) traced in the depth texture and read from the opaque colour copy, stretched vertically the way
// light streaks on wet acrylic, broken by raindrop rings in the puddles. Where the ray finds nothing the sheet adds
// nothing: the court's own material already mirrors the sky (MajesticWeather.hlsl). Only on while the court is wet.
Shader "GolfArcade/MajesticWeatherReflect"
{
    Properties { _Strength("Strength", Range(0,1)) = 1 }
    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent-200" "IgnoreProjector"="True" }
        Blend SrcAlpha OneMinusSrcAlpha ZWrite Off ZTest LEqual Cull Off
        Pass
        {
            Name "WetMirror" Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareOpaqueTexture.hlsl"
            #define MAJESTIC_WEATHER_ON 1   // this sheet only exists while the weather is on
            #include "Assets/Resources/Majestic/MajesticWeather.hlsl"
            CBUFFER_START(UnityPerMaterial) float _Strength; CBUFFER_END
            struct A { float4 p : POSITION; };
            struct V { float4 p : SV_POSITION; float3 w : TEXCOORD0; };
            V vert(A a) { V o; o.w = TransformObjectToWorld(a.p.xyz); o.p = TransformWorldToHClip(o.w); return o; }

            float2 ScreenUV(float3 q, out float eye)
            {
                float4 cs = TransformWorldToHClip(q);
                eye = -TransformWorldToView(q).z;
                float4 sp = ComputeScreenPos(cs);
                return sp.xy / max(sp.w, 1e-5);
            }

            half4 frag(V i) : SV_Target
            {
                float wet = _MajWet.x;
                if (_MajWeatherOn < .5h || wet < .02) return 0;
                float3 w = i.w;
                float3 toCam = _WorldSpaceCameraPos - w; float dist = length(toCam); float3 Vd = toCam / dist;
                float2 wm = w.xz * _MajUnit;
                float puddle = MajPuddles(wm, _MajWet.y, 1).x;
                // water normal: flat, broken by raindrop rings near the camera while it rains
                float3 N = float3(0, 1, 0);
                if (_MajWet.z > 0 && dist < 30)
                {
                    float2 g = MajRipple(wm * 2.3, _MajTime.x * 1.15, 0) + .8 * MajRipple(wm * 3.1 + 17.3, _MajTime.x * 1.4, 1);
                    N = normalize(N + float3(g.x, 0, g.y) * .3 * _MajWet.z * (1 - dist / 30) * (.4 + .6 * puddle));
                }
                float3 R = reflect(-Vd, N);
                if (R.y <= .005) return 0;
                // march along the reflected ray in the depth texture
                float t = .25, prevT = 0; bool hit = false; float2 uv = 0;
                [loop] for (int k = 0; k < 10; k++)
                {
                    float eye; float2 s = ScreenUV(w + R * t, eye);
                    if (any(s < 0) || any(s > 1)) break;
                    float scene = LinearEyeDepth(SampleSceneDepth(s), _ZBufferParams);
                    if (eye > scene + .02 && eye - scene < max(.5, t * .25)) { hit = true; uv = s; break; }
                    prevT = t; t *= 1.62;
                }
                if (!hit) return 0;
                // refine: three halvings between the last miss and the hit
                float lo = prevT, hi = t;
                [unroll] for (int b = 0; b < 3; b++)
                {
                    float mid = (lo + hi) * .5; float eye; float2 s = ScreenUV(w + R * mid, eye);
                    float scene = LinearEyeDepth(SampleSceneDepth(s), _ZBufferParams);
                    if (eye > scene + .02) { hi = mid; uv = s; } else lo = mid;
                }
                // light on wet acrylic streaks toward the viewer: blur the reflection vertically, more where there is no puddle
                float streak = lerp(.035, .012, puddle) * saturate(hi / 12);
                half3 col = SampleSceneColor(uv) * .5 + SampleSceneColor(uv + float2(0, streak * 1.6)) * .25 + SampleSceneColor(uv - float2(0, streak * 1.6)) * .25;
                float edge = smoothstep(0, .08, uv.x) * smoothstep(1, .92, uv.x) * smoothstep(1, .9, uv.y) * smoothstep(0, .05, uv.y);
                float fres = .02 + .98 * pow(1 - saturate(dot(N, Vd)), 5);
                // a wet hard court is a thin sheet of water: strongly mirror-like at the low gameplay angle
                float a = saturate(fres * 2.6 + .22 + puddle * .35) * saturate(wet * 1.4 - _MajWet.w) * edge * (1 - smoothstep(25, 60, hi)) * _Strength;
                return half4(col * .95, a * lerp(.7, .95, puddle));
            }
            ENDHLSL
        }
    }
}
