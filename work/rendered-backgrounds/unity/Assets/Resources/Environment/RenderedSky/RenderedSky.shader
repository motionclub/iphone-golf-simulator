Shader "GolfArcade/RenderedSky"
{
    // A sky we render ourselves: single-scattering LUT (RenderedSky.cs, from the real light), a sun /
    // moon disc in the light's direction, procedural cirrus, stars, and the open sea below the horizon
    // with the same aerial perspective as the distant scenery. No painted texture.
    // _Day/_Sunset/_Cloud/_Magma/_Ice keep DreamEnvironment's names so it drives this material unchanged.
    Properties
    {
        _Day("Daylight",Range(0,1))=1 _Sunset("Sunset",Range(0,1))=0 _Cloud("Cloud cover",Range(0,1))=0
        _Magma("Magma",Float)=0 _Ice("Aurora",Float)=0
        _Cirrus("Cirrus amount",Range(0,1))=.45 _CirrusScale("Cirrus scale",Float)=1
        _Stars("Stars",Range(0,1))=1 _SeaBelow("Open sea below the horizon",Float)=1
        _MagmaTint("Magma glow",Color)=(.9,.32,.10,1)
        _UpperTint("Stylised zenith tint",Color)=(1,1,1,1)
        [HideInInspector] _Equirect("Equirect output (reflection pass)",Float)=0
    }
    SubShader
    {
        Tags { "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" "RenderPipeline"="UniversalPipeline" }
        Cull Off ZWrite Off
        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        #include "RenderedSkyCommon.hlsl"
        CBUFFER_START(UnityPerMaterial)
        float _Day,_Sunset,_Cloud,_Magma,_Ice,_Cirrus,_CirrusScale,_Stars,_SeaBelow,_Equirect;
        half4 _MagmaTint,_UpperTint;
        CBUFFER_END

        float RS_Hash(float3 p) { p = frac(p * float3(443.897, 441.423, 437.195)); p += dot(p, p.yzx + 19.19); return frac((p.x + p.y) * p.z); }

        half3 SkyColor(float3 d, bool withSea, float camHeight)
        {
            half3 c;
            float3 sunD = _RSkySunDir.xyz;
            float night = _RSkyParams.y;
            if (d.y >= 0 || !withSea)
            {
                float3 du = d; du.y = max(du.y, 0);
                c = RS_SkyNoSun(normalize(du + float3(0, 1e-4, 0)));
                c *= lerp(half3(1, 1, 1), _UpperTint.rgb, saturate(d.y * 1.5));
                // cirrus on a plane ~8 km up, lit by the light, forward-scattering near it
                float up = max(d.y, 0);
                if (_Cirrus > .001 && up > .01)
                {
                    float2 p = d.xz / (up + .06) * .09 * _CirrusScale + float2(_RSkyParams.w * .0011, _RSkyParams.w * .0004);
                    float2 q = float2(p.x * .55 + p.y * .25, p.y * 1.8 - p.x * .2);   // streaky
                    half n = SAMPLE_TEXTURE2D_LOD(_RSkyNoise, sampler_RSkyNoise, q, 0).r * .65
                           + SAMPLE_TEXTURE2D_LOD(_RSkyNoise, sampler_RSkyNoise, q * 3.1 + .37, 0).g * .35;
                    half cover = saturate((n - (1 - _Cirrus * .62)) * 3.2) * smoothstep(.02, .22, up) * (1 - _RSkyParams.z * .6);
                    float mu = saturate(dot(d, sunD));
                    half3 lit = _RSkySunColor.rgb * (1 - night * .85) * (.11 + .55 * pow(mu, 12)) + _RSkyAmbientUp.rgb * .55;
                    c = lerp(c, lit, cover * .62);
                }
                // stars + aurora at night
                if (night > .01)
                {
                    float3 cell = floor(d * 420);
                    float h = RS_Hash(cell);
                    float3 centre = (cell + .5 + (float3(RS_Hash(cell + 7.1), RS_Hash(cell + 3.3), RS_Hash(cell + 1.9)) - .5) * .7) / 420;
                    float star = step(.992, h) * saturate(1 - length(d - normalize(centre)) * 420 * 1.6);
                    c += star * night * _Stars * (1 - _RSkyParams.z) * smoothstep(.03, .25, d.y) * (.6 + 2.5 * frac(h * 91.7));
                    float ribbon = exp(-pow((d.y - (.25 + .08 * sin(d.x * 8 + _RSkyParams.w * .025) + .06 * sin(d.z * 13))) * 18, 2));
                    float curtains = .55 + .45 * sin(atan2(d.z, d.x) * 80 + sin(d.x * 15) * 3 + _RSkyParams.w * .08);
                    c += ribbon * curtains * _Ice * night * (1 - _RSkyParams.z) * lerp(half3(.05, .5, .35), half3(.3, .15, .5), saturate(d.y * 2));
                }
                // the light's own disc (sun by day, moon by night) with a soft corona
                float cosD = dot(d, sunD), r = _RSkySunDir.w;
                float disc = smoothstep(cos(r * 1.08), cos(r * .92), cosD);
                float limb = lerp(1, sqrt(saturate(1 - (1 - cosD) / max(1 - cos(r), 1e-6))), .55);
                half3 discColor = _RSkySunColor.rgb * _RSkySunColor.a * limb * (1 - _RSkyParams.z * .9) * smoothstep(-.01, .02, d.y);
                c += disc * discColor + _RSkySunColor.rgb * pow(saturate(cosD), 900) * .35 * (1 - _RSkyParams.z) * (1 - night * .8);
            }
            else
            {
                // the open sea: deep water + Fresnel sky reflection + glitter, then the same aerial perspective
                float dist = max(camHeight, 1) / max(-d.y, 1e-4);
                float3 r = float3(d.x, -d.y, d.z);
                float f = .02 + .98 * pow(1 - saturate(-d.y), 5);
                half3 refl = RS_SkyNoSun(normalize(r + float3(0, .02, 0)));
                half3 sea = _RSkySea.rgb * (_RSkyAmbientUp.rgb * .9 + _RSkySunColor.rgb * .08) + refl * f * _RSkySea.a;
                float g = pow(saturate(dot(r, sunD)), 220) * (1 - _RSkyParams.z);
                sea += _RSkySunColor.rgb * g * 1.6;
                c = RS_Aerial(sea, d, dist);
            }
            c = lerp(c, c * .7 + _MagmaTint.rgb * .35 * pow(1 - saturate(abs(d.y)), 3), _Magma * .6);
            return c;
        }
        ENDHLSL
        Pass
        {
            Name "Sky"
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            struct A { float4 p : POSITION; float2 uv : TEXCOORD0; };
            struct V { float4 p : SV_POSITION; float3 d : TEXCOORD0; float2 uv : TEXCOORD1; };
            V vert(A a)
            {
                V o;
                o.uv = a.uv;
                if (_Equirect > .5) { o.p = float4(a.uv * 2 - 1, .5, 1);
                #if UNITY_UV_STARTS_AT_TOP
                    o.p.y = -o.p.y;
                #endif
                } else o.p = TransformObjectToHClip(a.p.xyz);
                // the view direction from the camera: right for the skybox, and for a dome mesh even when it was
                // static-batched into world space (the hub rooms' domes)
                o.d = TransformObjectToWorld(a.p.xyz) - _WorldSpaceCameraPos; return o;
            }
            half4 frag(V i) : SV_Target
            {
                float3 d;
                if (_Equirect > .5)
                {
                    // the convention every sky-reflecting shader in the project uses (heading 0)
                    float lon = (i.uv.x - .5) * 6.2831853, lat = (i.uv.y - .5) * 3.14159265;
                    d = float3(cos(lat) * cos(lon), sin(lat), cos(lat) * sin(lon));
                    return half4(SkyColor(d, true, 30), 1);
                }
                d = normalize(i.d);
                float camHeight = _WorldSpaceCameraPos.y - _RSkyAerial.y;
                return half4(SkyColor(d, _SeaBelow > .5, camHeight), 1);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
