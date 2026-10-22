Shader "GolfArcade/TennisWorldSurface"
{
    Properties
    {
        [MainTexture] _BaseMap("Albedo", 2D) = "white" {}
        [MainColor] _BaseColor("Colour", Color) = (1,1,1,1)
        _Smoothness("Surface polish", Range(0,1)) = .22
        _Metallic("Metal", Range(0,1)) = 0
        _Variation("Broad material variation", Range(0,.2)) = .04
        _Grain("Fine material grain", Range(0,.1)) = .012
        _WorldMap("World albedo detail", 2D) = "white" {}
        _WorldMapWeight("World albedo influence", Range(0,1)) = 0
        _WorldMapScale("World albedo scale", Float) = .12
        _CourtFinish("Fine acrylic sports surface", Float) = 0
        _CoastBlend("Coast sand / meadow blend", Float) = 0
        _SandColor("Shore sand", Color) = (.83,.77,.63,1)
        _GrassColor("Meadow", Color) = (.13,.30,.09,1)
        [Enum(UnityEngine.Rendering.CullMode)] _Cull("Cull", Float) = 2
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        Cull [_Cull]
        Pass
        {
            Name "ForwardLit" Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            TEXTURE2D(_WorldMap); SAMPLER(sampler_WorldMap);
            CBUFFER_START(UnityPerMaterial)
                float4 _BaseMap_ST;
                half4 _BaseColor;
                half _Smoothness, _Metallic, _Variation, _Grain;
                float _WorldMapWeight, _WorldMapScale, _CoastBlend, _CourtFinish; half4 _SandColor, _GrassColor;
            CBUFFER_END
            struct Attributes { float4 positionOS:POSITION; float3 normalOS:NORMAL; float2 uv:TEXCOORD0; half4 colour:COLOR; };
            struct Varyings { float4 positionCS:SV_POSITION; float3 positionWS:TEXCOORD0; half3 normalWS:TEXCOORD1; float2 uv:TEXCOORD2; half fog:TEXCOORD3; half3 vertexLight:TEXCOORD4; half4 colour:TEXCOORD5; };
            Varyings Vert(Attributes v)
            {
                Varyings o;
                o.positionWS = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap); o.colour = v.colour;
                o.fog = ComputeFogFactor(o.positionCS.z);
                o.vertexLight = VertexLighting(o.positionWS, o.normalWS);
                return o;
            }
            float Hash(float3 p) { p = frac(p * .1031); p += dot(p, p.yzx + 33.33); return frac((p.x + p.y) * p.z); }
            float Noise(float3 p)
            {
                float3 i = floor(p), f = frac(p); f = f * f * (3 - 2 * f);
                return lerp(lerp(lerp(Hash(i), Hash(i + float3(1,0,0)), f.x), lerp(Hash(i + float3(0,1,0)), Hash(i + float3(1,1,0)), f.x), f.y),
                            lerp(lerp(Hash(i + float3(0,0,1)), Hash(i + float3(1,0,1)), f.x), lerp(Hash(i + float3(0,1,1)), Hash(i + 1), f.x), f.y), f.z);
            }
            half4 Frag(Varyings i):SV_Target
            {
                half3 colour = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv).rgb * _BaseColor.rgb;
                if (_CoastBlend > .5)
                    colour = lerp(_SandColor.rgb, _GrassColor.rgb, smoothstep(.03,.95,i.colour.r));
                if (_WorldMapWeight > .001)
                {
                    float3 weights = pow(abs(normalize(i.normalWS)),4); weights /= max(.001,weights.x+weights.y+weights.z);
                    float3 p = i.positionWS * _WorldMapScale;
                    half3 mapped = SAMPLE_TEXTURE2D(_WorldMap,sampler_WorldMap,p.yz).rgb*weights.x
                        + SAMPLE_TEXTURE2D(_WorldMap,sampler_WorldMap,p.xz).rgb*weights.y
                        + SAMPLE_TEXTURE2D(_WorldMap,sampler_WorldMap,p.xy).rgb*weights.z;
                    if (_CoastBlend > .5)
                    {
                        half steep = (1-smoothstep(.70,.93,abs(normalize(i.normalWS).y))) * i.colour.b;
                        colour = lerp(colour,mapped * _BaseColor.rgb,steep);
                    }
                    else colour *= lerp(half3(1,1,1),mapped,_WorldMapWeight);
                }
                // Object-independent world grain works on the old untextured arena too.
                float broad = Noise(i.positionWS * .65) - .5;
                float fine = Noise(i.positionWS * 24) - .5;
                float grainFootprint = max(length(ddx(i.positionWS)),length(ddy(i.positionWS))) * 24;
                fine *= 1-smoothstep(.22,1.2,grainFootprint);
                colour *= 1 + broad * _Variation * 2 + fine * _Grain * 2;
                InputData input = (InputData)0;
                input.positionWS = i.positionWS;
                input.normalWS = normalize(i.normalWS);
                if (_CourtFinish > .5)
                {
                    // Restrained acrylic aggregate appears under close light;
                    // derivative filtering removes shimmering dots at phone distance.
                    float tiltX=(Noise(i.positionWS*24+float3(.4,0,0))-Noise(i.positionWS*24-float3(.4,0,0)))*.075;
                    float tiltZ=(Noise(i.positionWS*24+float3(0,0,.4))-Noise(i.positionWS*24-float3(0,0,.4)))*.075;
                    input.normalWS=normalize(input.normalWS+float3(tiltX,0,tiltZ)*(1-smoothstep(.22,1.2,grainFootprint)));
                }
                input.viewDirectionWS = SafeNormalize(GetWorldSpaceViewDir(i.positionWS));
                input.shadowCoord = TransformWorldToShadowCoord(i.positionWS);
                input.fogCoord = i.fog;
                input.vertexLighting = i.vertexLight;
                input.bakedGI = SampleSH(input.normalWS);
                input.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.positionCS);
                input.shadowMask = half4(1,1,1,1);
                SurfaceData surface = (SurfaceData)0;
                surface.albedo = colour; surface.alpha = 1; surface.occlusion = 1;
                surface.metallic = _Metallic;
                surface.smoothness = saturate(_Smoothness + broad * _Variation * .35 - _CourtFinish*fine*.035);
                surface.normalTS = half3(0,0,1);
                half4 result = UniversalFragmentPBR(input, surface);
                result.rgb = MixFog(result.rgb, i.fog);
                return result;
            }
            ENDHLSL
        }
        UsePass "Universal Render Pipeline/Lit/ShadowCaster"
        UsePass "Universal Render Pipeline/Lit/DepthOnly"
        UsePass "Universal Render Pipeline/Lit/DepthNormals"
    }
    Fallback "Universal Render Pipeline/Lit"
}
