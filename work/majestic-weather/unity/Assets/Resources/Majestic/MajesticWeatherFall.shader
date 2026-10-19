// Majestic weather (chat W): the camera-attached fall layer. One sphere round the lens; rain streaks, snow or ash in
// three depth layers computed from the view direction alone (columns = great circles through the zenith, so streaks
// converge like real falling rain), slanted by the wind, faded at the poles, and cut out of the ball corridor on
// screen (_CorridorSS: two viewport points, _CorridorR: radius). One pass, no textures, no depth reads.
Shader "GolfArcade/MajesticWeatherFall"
{
    Properties
    {
        _Amount("Amount", Range(0,1)) = 0
        _Kind("1 rain, 2 snow, 3 ash", Float) = 1
        _Color("Lit colour", Color) = (.8,.85,.9,1)
        _Slant("Wind slant", Float) = 0
        _Speed("Fall speed scale", Float) = 1
        _Glow("Ember share", Range(0,1)) = 0
        _CorridorSS("Corridor (viewport a.xy, b.xy)", Vector) = (0,0,0,0)
        _CorridorR("Corridor radius (viewport)", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent+60" "IgnoreProjector"="True" }
        Blend One OneMinusSrcAlpha ZWrite Off ZTest Always Cull Front
        Pass
        {
            Name "Fall" Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial)
                half4 _Color; float4 _CorridorSS; float _Amount, _Kind, _Slant, _Speed, _Glow, _CorridorR;
            CBUFFER_END
            struct A { float4 p : POSITION; };
            struct V { float4 p : SV_POSITION; float3 w : TEXCOORD0; };
            V vert(A a) { V o; o.w = TransformObjectToWorld(a.p.xyz); o.p = TransformWorldToHClip(o.w); return o; }

            float H(float2 p) { p = frac(p * float2(213.17, 371.53)); p += dot(p, p + 31.71); return frac(p.x * p.y); }

            // one layer of rain: N columns round the horizon, streaks of length L in a repeat of P cells
            float Rain(float az, float el, float t, float N, float P, float L, float w, float speed, float density, float seed)
            {
                float v = (el + t * speed) / 6.2831853 * N;
                float u = az * N + v * _Slant;
                float col = floor(u), fx = frac(u);
                float vv = v + H(float2(col, seed)) * 37.0;
                float rep = floor(vv / P), fy = frac(vv / P);
                float on = step(H(float2(col + seed * 13.1, rep)), density);
                float xc = .2 + .6 * H(float2(rep + seed, col * .37));
                float across = saturate(1 - abs(fx - xc) / w);
                float len = L / P;
                float along = fy < len ? sin(3.14159 * fy / len) : 0;
                return on * across * across * along;
            }

            // one layer of flakes (snow, ash): a flake per cell, swaying; x = alpha, y = ember
            float2 Flakes(float az, float el, float t, float N, float r, float speed, float density, float seed)
            {
                float v = (el + t * speed) / 6.2831853 * N;
                float u = az * N + v * _Slant * 1.5;
                float2 cell = floor(float2(u, v));
                float h = H(cell + seed);
                u += sin(t * 1.3 + h * 6.28 + v * .5) * .22;
                float2 f = frac(float2(u, v)) - .5 - (float2(H(cell + seed + 1.7), h) - .5) * .5;
                float d = length(f);
                float a = smoothstep(r, r * .35, d) * step(1 - density, H(cell * 1.31 + seed));
                return float2(a, a * step(1 - _Glow * .14, H(cell + seed + 9.1)));
            }

            half4 frag(V i) : SV_Target
            {
                float3 d = normalize(i.w - _WorldSpaceCameraPos);
                float az = atan2(d.x, d.z) / 6.2831853, el = d.y * (1 + .17 * d.y * d.y);   // ~asin, cheaper
                float t = _Time.y * _Speed;
                float a = 0, ember = 0;
                if (_Kind < 1.5)
                {
                    // two layers (near + far): the far one is dense enough to read as the third (cost, PLAN M4)
                    a += Rain(az, el, t, 150, 7, 2.6, .05, 3.0, .32 * _Amount, 1.0) * .45;
                    a += Rain(az, el, t, 420, 5, 2.2, .055, 1.7, .6 * _Amount, 2.0) * .34;
                    a *= 1 - smoothstep(.62, .9, abs(d.y));
                }
                else
                {
                    float2 f0 = Flakes(az, el, t, 120, .1, 1.1, .5 * _Amount, 1.0);
                    if (_Kind < 2.5)
                    {
                        float2 f1 = Flakes(az, el, t, 380, .13, .65, .75 * _Amount, 2.0);
                        a = f0.x * .9 + f1.x * .6; ember = f0.y + f1.y * .7;
                    }
                    else { a = f0.x * 1.1; ember = f0.y * 1.3; }   // ash: one layer (cost); the near particles add depth
                    a *= 1 - smoothstep(.8, .97, abs(d.y));
                }
                // never over the ball's line
                if (_CorridorR > 0)
                {
                    float2 s = GetNormalizedScreenSpaceUV(i.p);
                    float aspect = _ScreenParams.x / _ScreenParams.y;
                    float2 pa = (s - _CorridorSS.xy) * float2(aspect, 1), ba = (_CorridorSS.zw - _CorridorSS.xy) * float2(aspect, 1);
                    float k = saturate(dot(pa, ba) / max(dot(ba, ba), 1e-5));
                    float dist = length(pa - ba * k);
                    float keep = smoothstep(_CorridorR, _CorridorR * 1.7, dist);
                    a *= keep; ember *= keep;
                }
                a = saturate(a);
                half3 col = _Color.rgb * a + half3(1, .42, .1) * ember * 1.5;
                return half4(col, a * (_Kind < 1.5 ? .55 : .9));
            }
            ENDHLSL
        }
    }
}
