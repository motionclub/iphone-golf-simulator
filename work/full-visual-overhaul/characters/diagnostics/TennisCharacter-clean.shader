// Character surface for the tennis players and crowd (URP).
//
// Resort athlete surface: scene lighting describes the form; skin, eyes and equipment
// have distinct controlled highlights. The approved geometry and paint remain intact.
Shader "GolfArcade/TennisCharacter"
{
    Properties
    {
        [MainColor] _BaseColor ("Color", Color) = (1,1,1,1)
        [MainTexture] _BaseMap ("Albedo", 2D) = "white" {}
        [Normal] _BumpMap ("Normal map", 2D) = "bump" {}
        _BumpScale ("Normal strength", Range(0,2)) = 1
        [HideInInspector] _PaintLift ("Paint layer separation", Float) = 0
        [HideInInspector] _FaceRole ("Face: 1 eye, 2 iris, 3 lid, 4 brow", Float) = 0
        [HideInInspector] _Blink ("Blink", Range(0,1)) = 0
        [HideInInspector] _EyeNL ("Left closure normal and width", Vector) = (0,0,1,.03)
        [HideInInspector] _EyeNR ("Right closure normal and width", Vector) = (0,0,1,.03)
        [HideInInspector] _FaceSkin ("Fitted lid skin", Color) = (1,1,1,1)
        [HideInInspector] _Gaze ("Eye gaze", Vector) = (0,0,0,0)
        [HideInInspector] _EyeL ("Left eye centre", Vector) = (0,0,0,0)
        [HideInInspector] _EyeR ("Right eye centre", Vector) = (0,0,0,0)
        [HideInInspector] _FaceUp ("Face up", Vector) = (0,1,0,0)
        [HideInInspector] _FaceRight ("Face right", Vector) = (1,0,0,0)
        [HideInInspector] _BrowLift ("Brow lift", Float) = 0
        // The hero body has no UVs. With this on, _BumpMap is projected along the three axes from the BIND-POSE position carried in mesh channel 1
        // (MatchHeroLook writes it), so the soft break in the light stays on the skin as the body moves. _BumpTile = tiles per metre.
        _BumpTriplanar ("Bump from bind-pose position (meshes with no UVs)", Float) = 0
        _BumpTile ("Triplanar bump tiles per metre", Float) = 5
        _Saturation ("Saturation", Range(0,1.5)) = 0.96
        _Smoothness ("Smoothness", Range(0,1)) = 0.28
        _SpecularStrength ("Surface highlight strength", Range(0,2)) = 1
        _EnvironmentStrength ("Scene reflection strength", Range(0,1)) = 0.12
        _OcclusionStrength ("Character ambient occlusion strength", Range(0,1)) = 0.25
        _Wrap ("Wrap", Range(0,1)) = 0.35
        _Subsurface ("Subsurface warmth", Color) = (0,0,0,0)
        _RimColor ("Rim colour", Color) = (1,0.96,0.88,1)
        _RimPower ("Rim power", Range(0.5,8)) = 3.5
        _RimStrength ("Rim strength", Range(0,1)) = 0.22
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
            #pragma multi_compile _ _LIGHT_LAYERS
            #pragma multi_compile_fog
            // multi_compile, not shader_feature: the materials are made at runtime, so no
            // material asset would keep a shader_feature variant alive in the build.
            #pragma multi_compile_local _ _NORMALMAP
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "HeroLighting.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float4 _BaseColor; float4 _BaseMap_ST; half4 _Subsurface; half4 _RimColor;
                float4 _EyeL, _EyeR, _FaceUp, _FaceRight, _Gaze, _FaceSkin, _EyeNL, _EyeNR; half _PaintLift, _FaceRole, _Blink, _BrowLift;
                float4 _BumpMap_ST; half _Smoothness, _Wrap, _RimPower, _RimStrength, _BumpScale, _Saturation, _BumpTriplanar, _SpecularStrength, _EnvironmentStrength, _OcclusionStrength; float _BumpTile;
            CBUFFER_END
            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            TEXTURE2D(_BumpMap); SAMPLER(sampler_BumpMap);

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float4 tangentOS : TANGENT; float2 uv : TEXCOORD0; float3 bindPos : TEXCOORD1; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; float3 positionWS : TEXCOORD1; float3 normalWS : TEXCOORD2; half fog : TEXCOORD3; float4 tangentWS : TEXCOORD4; float3 bindPos : TEXCOORD5; float3 normalOS : TEXCOORD6; float2 eyeCoord : TEXCOORD7; };

            Varyings vert (Attributes i)
            {
                Varyings o;
                float3 facePos = i.positionOS.xyz;
                o.eyeCoord = 0;
                float3 faceNormal = i.normalOS;
                if (_FaceRole > .5h) {
                    float4 eye = dot(facePos - (_EyeL.xyz + _EyeR.xyz) * .5, _FaceRight.xyz) < 0 ? _EyeL : _EyeR;
                    if (_FaceRole < 3.5h || _FaceRole > 4.5h) {
                        float4 closeNormal = dot(facePos - (_EyeL.xyz + _EyeR.xyz) * .5, _FaceRight.xyz) < 0 ? _EyeNL : _EyeNR;
                        // The sclera is the fitted surface over a real eye cavity. Keep it
                        // intact: eyelid color sweeps over it rather than opening a hole.
                        if (_FaceRole > 1.5h && _FaceRole < 2.5h) facePos += (_FaceRight.xyz * _Gaze.x + _FaceUp.xyz * _Gaze.y) * (1 - _Blink);
                        float h = dot(facePos - eye.xyz, _FaceUp.xyz);
                        o.eyeCoord = float2(dot(facePos - eye.xyz, _FaceRight.xyz) / max(closeNormal.w,.0001), h / max(eye.w, .0001));
                        // The closure shell already carries the adjacent body normals.
                    } else facePos += _FaceUp.xyz * _BrowLift;
                }
                facePos += i.normalOS * _PaintLift;
                VertexPositionInputs p = GetVertexPositionInputs(facePos);
                o.positionCS = p.positionCS; o.positionWS = p.positionWS;
                VertexNormalInputs nrm = GetVertexNormalInputs(faceNormal, i.tangentOS);
                o.normalWS = nrm.normalWS;
                o.tangentWS = float4(nrm.tangentWS, i.tangentOS.w * GetOddNegativeScale());
                o.uv = TRANSFORM_TEX(i.uv, _BaseMap);
                o.bindPos = i.bindPos; o.normalOS = i.normalOS;
                o.fog = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            

            half4 frag (Varyings i) : SV_Target
            {
                half3 n = normalize(i.normalWS);
                #if defined(_NORMALMAP)
                if (_BumpTriplanar > 0.5)
                {
                    // Three axis projections of the soft normal map from the bind-pose position, blended by the skinned object-space normal
                    // and added to it (UDN blend), then back to world: a break in the light that rides on the skin.
                    float3 nO = normalize(i.normalOS);
                    float3 w = pow(abs(nO), 4); w /= (w.x + w.y + w.z + 1e-5);
                    half2 tx = UnpackNormalScale(SAMPLE_TEXTURE2D(_BumpMap, sampler_BumpMap, i.bindPos.zy * _BumpTile), _BumpScale).xy;
                    half2 ty = UnpackNormalScale(SAMPLE_TEXTURE2D(_BumpMap, sampler_BumpMap, i.bindPos.xz * _BumpTile), _BumpScale).xy;
                    half2 tz = UnpackNormalScale(SAMPLE_TEXTURE2D(_BumpMap, sampler_BumpMap, i.bindPos.xy * _BumpTile), _BumpScale).xy;
                    nO = normalize(nO + w.x * float3(0, tx.y, tx.x) + w.y * float3(ty.x, 0, ty.y) + w.z * float3(tz.x, tz.y, 0));
                    n = normalize(TransformObjectToWorldNormal(nO));
                }
                else
                {
                    half3 ts = UnpackNormalScale(SAMPLE_TEXTURE2D(_BumpMap, sampler_BumpMap, i.uv), _BumpScale);
                    half3 t = normalize(i.tangentWS.xyz); half3 b = cross(n, t) * i.tangentWS.w;
                    n = normalize(TransformTangentToWorld(ts, half3x3(t, b, n)));
                }
                #endif
                half3 v = normalize(GetWorldSpaceViewDir(i.positionWS));
                half4 c = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv) * _BaseColor;
                half lid = 0;
                if(_FaceRole>5.5h) {
                    if(abs(i.eyeCoord.x)<1.3h&&i.eyeCoord.y>.5h&&i.eyeCoord.y<3h)clip(.2h-_Blink);
                }
                else if (_FaceRole > .5h && (_FaceRole < 3.5h || _FaceRole > 4.5h)) {
                    half closed = -.45h + .22h * i.eyeCoord.x * i.eyeCoord.x;
                    half progress = pow(_Blink,.8h);
                    half upper = lerp(1,closed,progress), lower=lerp(-1,closed,progress);
                    lid = max(smoothstep(upper - .025h, upper + .025h, i.eyeCoord.y), 1 - smoothstep(lower - .025h, lower + .025h, i.eyeCoord.y));
                    if (_Blink > .995h) lid = 1;
                    if (_Blink < .001h) lid = 0;
                    if (_FaceRole < 3.5h) clip(.5h - lid);
                    else {
                        clip(lid - .5h); c.rgb = _FaceSkin.rgb;
                        half creaseY = closed;
                        half crease = (1 - smoothstep(.018h,.045h,abs(i.eyeCoord.y - creaseY))) * (1 - smoothstep(.78h,.98h,abs(i.eyeCoord.x))) * smoothstep(.72h,1,_Blink);
                        c.rgb *= 1 - crease * .38h;
                    }
                }
                half surfaceSmoothness = lerp(_Smoothness, .28h, lid);
                half surfaceSpecular = lerp(_SpecularStrength, .8h, lid);
                half surfaceWrap = lerp(_Wrap, .32h, lid);
                // The generated textures are painted warm and the resort grade warms again;
                // pull saturation back so skin reads peach rather than orange.
                c.rgb = lerp(dot(c.rgb, half3(0.2126, 0.7152, 0.0722)).xxx, c.rgb, _Saturation);
                Light main = HeroMain(GetMainLight(TransformWorldToShadowCoord(i.positionWS)));
                half3 reflection;
                half3 colour = HeroCharacterShade(main, n, v, c.rgb, surfaceWrap, surfaceSmoothness, _Subsurface.rgb, surfaceSpecular, reflection);
                #if defined(_ADDITIONAL_LIGHTS)
                uint count = GetAdditionalLightsCount();
                #if defined(_LIGHT_LAYERS)
                uint meshLayers = GetMeshRenderingLayer();
                #endif
                for (uint li = 0; li < count; li++)
                {
                    Light extra = GetAdditionalLight(li, i.positionWS);
                    // A light on its own rendering layer (the hero rim) only reaches meshes that carry that layer.
                    #if defined(_LIGHT_LAYERS)
                    if (!IsMatchingLightLayer(extra.layerMask, meshLayers)) continue;
                    #endif
                    half3 extraReflection;
                    colour += HeroCharacterShade(extra, n, v, c.rgb, surfaceWrap, surfaceSmoothness, _Subsurface.rgb, surfaceSpecular, extraReflection);
                    reflection += extraReflection;
                }
                #endif
                // Real probe reflections are restrained on skin and clear on varnished eyes/frames.
                // One shared reflection sample, no screen-space reflections or new render pass.
                half roughness = max(1 - surfaceSmoothness, .08h);
                half fresnel = .04h + .10h * pow(1 - saturate(dot(n, v)), 5);
                half3 environment = GlossyEnvironmentReflection(reflect(-v, n), i.positionWS, roughness, 1) * fresnel * lerp(_EnvironmentStrength, .12h, lid);
                colour += environment; reflection += environment;
                half3 ambient = HeroAmbient(n) * c.rgb;
                #if defined(_SCREEN_SPACE_OCCLUSION)
                AmbientOcclusionFactor ao = GetScreenSpaceAmbientOcclusion(GetNormalizedScreenSpaceUV(i.positionCS));
                half indirectAO = lerp(1,ao.indirectAmbientOcclusion,_OcclusionStrength);
                half directAO = lerp(1,ao.directAmbientOcclusion,_OcclusionStrength);
                ambient *= indirectAO; colour *= directAO; reflection *= directAO;
                #endif
                half rim = pow(1 - saturate(dot(v, n)), _RimPower) * _RimStrength * (_HeroProfile > .5h ? _HeroRim : 1);
                half3 rimLight = _RimColor.rgb * rim * (0.35 + 0.65 * c.rgb) * main.color;
                colour += ambient + rimLight; reflection += rimLight;
                return half4(MixFog(HeroCharacterFinish(colour, reflection), i.fog), 1);
            }
            ENDHLSL
        }
        UsePass "Universal Render Pipeline/Lit/ShadowCaster"
        Pass {
            Name "DepthOnly" Tags {"LightMode"="DepthOnly"}
            ZWrite On ColorMask R
            HLSLPROGRAM
            #pragma vertex vertDepth
            #pragma fragment fragDepth
            #include "HeroFaceDepth.hlsl"
            ENDHLSL
        }
        Pass {
            Name "DepthNormals" Tags {"LightMode"="DepthNormals"}
            ZWrite On
            HLSLPROGRAM
            #pragma vertex vertDepth
            #pragma fragment fragDepthNormals
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT
            #include "HeroFaceDepth.hlsl"
            ENDHLSL
        }
    }
    FallBack "Universal Render Pipeline/Lit"
}
