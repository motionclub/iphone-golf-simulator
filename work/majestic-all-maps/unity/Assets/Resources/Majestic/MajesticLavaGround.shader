// Chat 10 (work/majestic-all-maps): Magma Open's ash rough as cracked basalt plates with glowing lava seams
// (targets refs/holes/h21_offL.jpg, h10_tee.jpg: charcoal plates, thin orange-red cracks, hotter in patches).
// World-mapped (xz, yards), no textures: a Voronoi of plates, the seam = distance to the cell edge, anti-aliased
// with fwidth and averaged out with distance so it never shimmers. Glow is emission (bloom picks the cores up).
// Replaces the "Course N Ash" material on Magma holes only (MajesticLavaGround.Apply), reversibly.
Shader "GolfArcade/MajesticLavaGround"
{
    Properties
    {
        _Plate("Plate size (yd)", Float) = 2.4
        _Seam("Seam width (yd)", Float) = .06
        _GlowWidth("Glow falloff (yd)", Float) = .16
        _Basalt("Basalt", Color) = (.055,.05,.055,1)
        _BasaltHi("Basalt high", Color) = (.12,.105,.11,1)
        _Hot("Seam core", Color) = (1,.42,.08,1)
        _Ember("Seam glow", Color) = (.75,.12,.02,1)
        _Glow("Glow strength", Float) = 2.2
        _Patch("Hot patch scale (yd)", Float) = 26
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        CBUFFER_START(UnityPerMaterial)
            float _Plate, _Seam, _GlowWidth, _Glow, _Patch;
            half4 _Basalt, _BasaltHi, _Hot, _Ember;
        CBUFFER_END
        ENDHLSL
        Pass
        {
            Name "ForwardLit" Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            struct A { float4 p:POSITION; float3 n:NORMAL; };
            struct V { float4 p:SV_POSITION; float3 w:TEXCOORD0; half3 n:TEXCOORD1; half fog:TEXCOORD2; };

            float2 hash2(float2 c) { c = float2(dot(c, float2(127.1, 311.7)), dot(c, float2(269.5, 183.3))); return frac(sin(c) * 43758.5453); }
            float hash1(float2 c) { return frac(sin(dot(c, float2(41.3, 289.1))) * 15731.743); }
            float vnoise(float2 p)
            {
                float2 i = floor(p), f = frac(p); f = f * f * (3 - 2 * f);
                return lerp(lerp(hash1(i), hash1(i + float2(1, 0)), f.x), lerp(hash1(i + float2(0, 1)), hash1(i + 1), f.x), f.y);
            }
            // distance to the nearest Voronoi edge (2-pass, Quilez) + the owning cell id
            float voronoiEdge(float2 x, out float2 cell)
            {
                float2 n = floor(x), f = frac(x), mg = 0, mr = 0; float md = 8;
                for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++)
                {
                    float2 g = float2(i, j), o = hash2(n + g) * .85 + .075, r = g + o - f; float d = dot(r, r);
                    if (d < md) { md = d; mr = r; mg = g; }
                }
                md = 8;
                for (int j2 = -1; j2 <= 1; j2++) for (int i2 = -1; i2 <= 1; i2++)   // 3x3, not 5x5: mobile cost
                {
                    float2 g = mg + float2(i2, j2), o = hash2(n + g) * .85 + .075, r = g + o - f;
                    if (dot(mr - r, mr - r) > .00001) md = min(md, dot(.5 * (mr + r), normalize(r - mr)));
                }
                cell = n + mg; return md;
            }

            V vert(A a)
            {
                V o; o.w = TransformObjectToWorld(a.p.xyz); o.p = TransformWorldToHClip(o.w);
                o.n = TransformObjectToWorldNormal(a.n); o.fog = ComputeFogFactor(o.p.z); return o;
            }
            half4 frag(V i) : SV_Target
            {
                float2 uv = i.w.xz / _Plate;
                // a little domain warp so the plates are not a regular honeycomb
                uv += (float2(vnoise(uv * .35), vnoise(uv * .35 + 19.7)) - .5) * .7;
                float2 cell; float edge = voronoiEdge(uv, cell) * _Plate;       // yards to the seam
                float px = max(fwidth(uv.x), fwidth(uv.y)) * _Plate;            // yards per pixel here
                float far = saturate((px - .05) / .25);                         // seams below a pixel: average them out
                float core = (1 - smoothstep(_Seam - px, _Seam + px, edge)) * (1 - far);
                float glow = exp(-edge / _GlowWidth) * (1 - far * .6);
                // hot patches: some seams run bright, most smoulder; each plate pulses a little on its own
                float patch = smoothstep(.35, .8, vnoise(i.w.xz / _Patch) * .7 + vnoise(i.w.xz / (_Patch * .37)) * .3);
                float pulse = .8 + .2 * sin(_Time.y * (.6 + hash1(cell) * .8) + hash1(cell + 7) * 6.283);
                float heat = (.12 + .88 * patch) * pulse;   // round 17: most seams smoulder, a few run hot (targets)
                // plates: charcoal, a little value per plate, darker toward the seam (the bevel)
                half3 albedo = lerp(_Basalt.rgb, _BasaltHi.rgb, hash1(cell) * .8 + vnoise(i.w.xz * .9) * .2);
                albedo *= lerp(.55, 1, saturate(edge / .5));
                half3 n = normalize(i.n);
                Light sun = GetMainLight(TransformWorldToShadowCoord(i.w));
                half3 lit = albedo * (SampleSH(n) + sun.color * saturate(dot(n, sun.direction)) * sun.shadowAttenuation);
                half3 emit = (_Hot.rgb * core * 1.6 + _Ember.rgb * glow * .3) * heat * _Glow
                           + _Ember.rgb * far * .06 * heat * _Glow;                  // far: the seams' average glow
                half3 col = MixFog(lit + emit, i.fog);
                return half4(col, 1);
            }
            ENDHLSL
        }
        Pass
        {
            Name "DepthOnly" Tags { "LightMode"="DepthOnly" }
            ColorMask R
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            float4 vert(float4 p:POSITION) : SV_POSITION { return TransformObjectToHClip(p.xyz); }
            half4 frag() : SV_Target { return 0; }
            ENDHLSL
        }
        Pass
        {
            Name "ShadowCaster" Tags { "LightMode"="ShadowCaster" }
            ColorMask 0
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            float3 _LightDirection;
            struct A { float4 p:POSITION; float3 n:NORMAL; };
            float4 vert(A a) : SV_POSITION
            {
                float3 w = TransformObjectToWorld(a.p.xyz); float3 n = TransformObjectToWorldNormal(a.n);
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
