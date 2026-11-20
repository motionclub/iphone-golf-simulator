// CLOTH_OVERHAUL: colour-neutral garment normal/masks, six fabric IDs, derivative-filtered detail atlas.
// Same shader name and seven-role runtime API. No new keywords or pipeline settings.
Shader "GolfArcade/TennisCloth"
{
    Properties
    {
        [MainColor] _BaseColor ("Color", Color) = (1,1,1,1)
        _ClothAuditColor ("Audit ID colour (ClothAudit)", Color) = (1,0,0,1)
        _TrimColor ("Trim colour", Color) = (0.035,0.035,0.0401,1)
        _NormalMap ("Garment normal (kit UV)", 2D) = "bump" {}
        _MaskMap ("AO / cavity / trim / fabric ID", 2D) = "white" {}
        _UseGarmentMaps ("Use garment construction", Float) = 0
        _FabricVersion ("Fabric encoding: 1 tennis, 2 golf", Float) = 1
        _AOStrength ("Garment AO strength", Range(0,1)) = 1
        _NormalStrength ("Garment normal strength", Range(0,2)) = 1
        [HideInInspector] _FemaleSurface ("Female material finish", Float) = 0
        _Smoothness ("Smoothness", Range(0,1)) = 0.1
        _Wrap ("Wrap", Range(0,1)) = 0.5
        _RimColor ("Rim colour", Color) = (1,0.96,0.88,1)
        _RimPower ("Rim power", Range(0.5,8)) = 3.5
        _RimStrength ("Rim strength", Range(0,1)) = 0.2
        _Exposure ("Cloth exposure", Range(0.2,1.5)) = 0.7
        _Knee ("Highlight knee", Range(0.3,0.95)) = 0.7
        _WeaveMap ("Weave: normal xy, thread break", 2D) = "gray" {}
        _WeaveTile ("Weave tiles per UV unit", Float) = 120
        _WeaveAngle ("Weave grain angle (deg)", Float) = 0
        _WeaveNormal ("Weave normal strength", Range(0,2)) = 1
        _WeaveThread ("Thread break strength", Range(0,1)) = 0.5
        _SheenStrength ("Sheen strength", Range(0,2)) = 0.55
        _SheenPower ("Sheen power", Range(1,8)) = 3
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Face culling", Float) = 2
        // Bald-base pass: 1 = shoe sole line, 2 = sock cuff, drawn from the kit edge measurements in UV3 (HeroKitEdges). 0 = off.
        [HideInInspector] _EdgeLines ("Kit edge lines", Float) = 0
        // Clothing V3: 3 = the 4 x 4 Blender yarn atlas (KitV3_FabricAtlas), fibre shine and tonal grain. 2 = the V2 path, unchanged.
        _AtlasVersion ("Fabric atlas version", Float) = 2
        _KnitCell ("Knit atlas cell for id 7 (1 pique, 4 jersey)", Float) = 1
        _FabricDetail ("V3 yarn relief", Range(0,2)) = 1
        _FibreShine ("V3 fibre shine", Range(0,3)) = 1
        _Mottle ("V3 tonal grain", Range(0,0.2)) = 0.08
        // STYLE PILOT (2026-10-30): 0 = off, every other garment unchanged
        _MaterialMatte ("Woven textile response", Range(0,1)) = 0
        _StylePass ("Style pass", Float) = 0
        _StyleSmooth ("Style smoothness", Range(0,1)) = 0.55
        _StyleSpec ("Style highlight", Range(0,2)) = 0.6
        _StyleEnv ("Style reflection", Range(0,1)) = 0.35
        _StyleAOFloor ("Style fold shadow floor", Range(0,1)) = 0.3
        _StyleRamp ("Style top-lit ramp", Range(0,0.5)) = 0.15
        _StyleSheen ("Style fabric edge sheen", Range(0,2)) = 0.5
        _StyleValueCap ("Style albedo value cap", Range(0.5,1)) = 0.8
        _StyleSat ("Style saturation", Range(0.5,1)) = 0.88
        _StyleCool ("Style cool shadow side", Range(0,1)) = 0
        _StyleFill ("Style garment fill (court)", Range(0,1)) = 0
        _StyleDewarm ("Style counter to the warm grade", Range(0,1)) = 0
        // CLOTH JIGGLE (2026-10-30 pilot): looseness map (R hem, G left sleeve, B right sleeve, A collar) x spring offsets (ClothJiggle.cs)
        [NoScaleOffset] _JiggleMap ("Jiggle looseness", 2D) = "black" {}
        _JigOn ("Jiggle on", Float) = 0
        [HideInInspector] _JigHem ("", Vector) = (0,0,0,0)
        [HideInInspector] _JigSleeveL ("", Vector) = (0,0,0,0)
        [HideInInspector] _JigSleeveR ("", Vector) = (0,0,0,0)
        [HideInInspector] _JigCollar ("", Vector) = (0,0,0,0)
    }
    HLSLINCLUDE
    #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial)
                float4 _ClothAuditColor;
                float4 _BaseColor, _TrimColor; half4 _RimColor; float4 _WeaveMap_ST; float4 _NormalMap_ST, _MaskMap_ST;
                half _Smoothness, _Wrap, _RimPower, _RimStrength, _Exposure, _Knee;
                float _WeaveTile, _WeaveAngle;
                half _WeaveNormal, _WeaveThread, _SheenStrength, _SheenPower;
                half _UseGarmentMaps, _NormalStrength, _AOStrength;
                half _FabricVersion, _EdgeLines, _FemaleSurface;
                half _AtlasVersion, _KnitCell, _FabricDetail, _FibreShine, _Mottle;
                half _MaterialMatte;
                half _StylePass, _StyleSmooth, _StyleSpec, _StyleEnv, _StyleAOFloor, _StyleRamp, _StyleSheen, _StyleValueCap, _StyleSat, _StyleCool, _StyleFill, _StyleDewarm;
                float4 _JigHem, _JigSleeveL, _JigSleeveR, _JigCollar; half _JigOn;
            CBUFFER_END
            TEXTURE2D(_JiggleMap); SAMPLER(sampler_JiggleMap);
            float _ClothAuditMode;               // ClothAudit (editor films): 1 = flat ID colour, inside faces darker
            float _ClothJiggleGlobal;            // set by ClothJiggle (1 while any hero simulates); 0 = every garment static, as shipped
            // Inertia wobble: loose cloth moves by the springs' world offsets; never into the body (inward part along the normal dropped)
            float3 ClothJiggle(float3 pWS, float3 nWS, float2 uv)
            {
                if (_JigOn < .5 || _ClothJiggleGlobal < .5) return pWS;
                float4 w = SAMPLE_TEXTURE2D_LOD(_JiggleMap, sampler_JiggleMap, uv, 0);
                float3 off = w.r * _JigHem.xyz + w.g * _JigSleeveL.xyz + w.b * _JigSleeveR.xyz + w.a * _JigCollar.xyz;
                off -= nWS * min(dot(off, nWS), 0) * .85;
                return pWS + off;
            }
            // LIVE POLO (PoloCloth.cs): world offsets of up to 256 cloth particles, 4 per vertex (UV5 ids, UV6 weights).
            float4 _Cage[256]; float _CageOn;
            float _KitSatCut;
            // POSE-DRIVEN WRINKLES (WrinkleBlend.cs): up to 6 baked wrinkle maps, two per texture (xy, xy), weighted per frame
            TEXTURE2D(_Wr0); SAMPLER(sampler_Wr0); TEXTURE2D(_Wr1); TEXTURE2D(_Wr2);
            float4 _WrW0, _WrW1; float _WrOn, _WrGain;
            float _KnitShow;   // 1 = keep the piqué thread shade under the style pass (live polo)
            float3 PoloCage(float3 pWS, float4 id, float4 w)
            {
                if (_CageOn < .5 || _ClothJiggleGlobal < .5) return pWS;
                return pWS + w.x * _Cage[(uint)id.x].xyz + w.y * _Cage[(uint)id.y].xyz + w.z * _Cage[(uint)id.z].xyz + w.w * _Cage[(uint)id.w].xyz;
            }
            TEXTURE2D(_NormalMap); SAMPLER(sampler_NormalMap);
            TEXTURE2D(_MaskMap); SAMPLER(sampler_MaskMap);
            TEXTURE2D(_WeaveMap); SAMPLER(sampler_WeaveMap);

    ENDHLSL
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        Cull [_Cull]
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
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #define HERO_PRESENTATION_SURFACE 1
            #include "HeroLighting.hlsl"
            #include "HeroCloth.hlsl"

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float4 tangentOS : TANGENT; float2 uv : TEXCOORD0; float4 edge : TEXCOORD3; float4 construction : TEXCOORD4; float4 cageId : TEXCOORD5; float4 cageW : TEXCOORD6; };
            struct Varyings
            {
                float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; float3 positionWS : TEXCOORD1; float3 normalWS : TEXCOORD2;
                float4 tangentWS : TEXCOORD3; half fog : TEXCOORD4; float4 edge : TEXCOORD5; float4 construction : TEXCOORD6;
            };

            Varyings vert (Attributes i)
            {
                Varyings o;
                VertexNormalInputs nrm = GetVertexNormalInputs(i.normalOS, i.tangentOS);
                o.positionWS = PoloCage(ClothJiggle(TransformObjectToWorld(i.positionOS.xyz), nrm.normalWS, i.uv), i.cageId, i.cageW);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.normalWS = nrm.normalWS;
                o.tangentWS = float4(nrm.tangentWS, i.tangentOS.w * GetOddNegativeScale());
                o.uv = i.uv; o.edge = i.edge; o.construction = i.construction;
                o.fog = ComputeFogFactor(o.positionCS.z);
                return o;
            }

            // Bald-base pass: kit edge lines from per-vertex measurements in metres (HeroKitEdges), anti-aliased with their own derivatives.
            //   shoe: e.x = height above the sole's bottom (-1 on the upper), e.y = signed height above the sole's top edge, e.z = 1
            //   sock: e.x = depth below the top opening, e.yz = direction round the leg, e.w = rib count
            half KitEdgeLines(float4 e)
            {
                if (_EdgeLines < 1.5h) {
                    if (e.z < .5) return 1;
                    float wy = max(fwidth(e.y), 1e-5);
                    // the line where the upper stands on the sole: the upper's first 1.5 mm and the sole's top 1 mm
                    half seam = 1 - smoothstep(.00125 - wy, .00125 + wy, abs(e.y - .00025));
                    half rubber = 0;
                    if (e.x >= 0) { float wx = max(fwidth(e.x), 1e-5); rubber = 1 - smoothstep(.0065 - wx, .0065 + wx, e.x); }
                    return (1 - .45h * seam) * (1 - .18h * rubber);
                }
                if (e.w < .5) return 1;
                float wd = max(fwidth(e.x), 1e-5);
                half cuff = 1 - smoothstep(.022 - wd, .022 + wd, e.x);
                float phase = atan2(e.z, e.y) * e.w;
                half ribFade = 1 - smoothstep(1.2, 2.6, fwidth(phase));      // fade the ribs before they alias (and on the atan seam)
                half valley = .5h - .5h * cos(phase);
                half ribs = 1 - .12h * valley * valley * ribFade * cuff;
                half cuffLine = 1 - smoothstep(.0008 - wd, .0008 + wd, abs(e.x - .022));
                half cuffTop = 1 - smoothstep(.0012 - wd, .0012 + wd, e.x);
                return ribs * (1 - .32h * cuffLine) * (1 - .14h * cuffTop);
            }

            // Two symmetric comparison taps keep cloth shadow sampling within the six-fetch phone budget.
            // Court/pipeline shadow settings stay unchanged; this receiver alone uses two taps.
            

            // Charlie distribution with Ashikhmin visibility. Knit fibres have a broad grazing lobe,
            // while rubber/foam have zero sheen. Numbers are shared with GARMENT_SPEC.md.
            
            

            // Roll the brightest channel off above the knee (hue kept): a lit white keeps a gradient instead of clipping.
            

            // Female knit response (2026-10-16 shader pass): matte Lambert form so
            // folds read, a saturated light-through-fibre band at the terminator
            // (relative to the chosen colour, so every swatch keeps its hue) and a
            // Charlie velvet lobe for the soft grazing sheen of cotton knit.
            // Rubber/foam keep a small dielectric highlight and no textile sheen.
            half3 FemaleClothDeep(half3 albedo)
            {
                half luma=max(dot(albedo,half3(.2126h,.7152h,.0722h)),.04h);
                return saturate(albedo*albedo/luma);
            }
            half3 FemaleClothShade(Light light, half3 n, half3 v, half3 albedo,
                                  half smoothness, half sheen, half ao, half id)
            {
                half ndl=dot(n,light.direction), nl=saturate(ndl), nv=saturate(dot(n,v));
                half wrapped=saturate((ndl+_Wrap)/(1+_Wrap));
                half band=saturate(wrapped-nl);
                half3 h=SafeNormalize(light.direction+v);
                half nh=saturate(dot(n,h));
                half rubber=id>2.5h&&id<4.5h?1:0;
                half invR=1.55h;
                half charlie=(2+invR)*pow(max(1-nh*nh,.0001h),invR*.5h)*.15915494h;
                half visibility=rcp(max(4*(nl+nv-nl*nv),.10h));
                half3 fibreTint=lerp(albedo,sqrt(max(albedo,0)),.45h);
                half3 velvet=fibreTint*(charlie*visibility*nl*sheen*2.4h)*(1-rubber);
                half spec=pow(nh,24+smoothness*60)*.035h*nl*rubber;
                // Rounded knit volume: fibres turned away from the viewer read deeper.
                half body=lerp(.64h,1,sqrt(nv));
                half3 diffuse=(albedo*nl*.96h+lerp(albedo,FemaleClothDeep(albedo),.65h)*band*.85h*(1-rubber*.5h))*lerp(1,body,1-rubber);
                return (diffuse+velvet+spec)*ao*light.color*light.distanceAttenuation*light.shadowAttenuation;
            }
            float ClothHash(float2 p)
            {
                float3 h=frac(float3(p.x,p.y,p.x)*.1031);
                h+=dot(h,h.yzx+33.33);return frac((h.x+h.y)*h.z);
            }
            half ClothGrain(float2 p)
            {
                float2 cell=floor(p), f=frac(p);f=f*f*(3-2*f);
                return lerp(lerp(ClothHash(cell),ClothHash(cell+float2(1,0)),f.x),lerp(ClothHash(cell+float2(0,1)),ClothHash(cell+1),f.x),f.y);
            }

            half4 frag (Varyings i, FRONT_FACE_TYPE facing : FRONT_FACE_SEMANTIC) : SV_Target
            {
                if (_ClothAuditMode > .5) return IS_FRONT_VFACE(facing, true, false) ? half4(_ClothAuditColor.rgb, 1) : half4(_ClothAuditColor.rgb * .5h, 1);
                half3 n = normalize(i.normalWS);
                half3 v = normalize(GetWorldSpaceViewDir(i.positionWS));

                half4 mask = half4(1, 1, 0, 0);
                half3 garment = half3(0, 0, 1);
                if (_UseGarmentMaps > .5h) {
                    mask = SAMPLE_TEXTURE2D(_MaskMap, sampler_MaskMap, i.uv);
                    garment = UnpackNormal(SAMPLE_TEXTURE2D(_NormalMap, sampler_NormalMap, i.uv));
                    garment.xy *= _NormalStrength;
                    if (_WrOn > .5h) {
                        half4 q0 = SAMPLE_TEXTURE2D(_Wr0, sampler_Wr0, i.uv) * 2 - 1, q1 = SAMPLE_TEXTURE2D(_Wr1, sampler_Wr0, i.uv) * 2 - 1, q2 = SAMPLE_TEXTURE2D(_Wr2, sampler_Wr0, i.uv) * 2 - 1;
                        half2 wr = q0.xy * _WrW0.x + q0.zw * _WrW0.y + q1.xy * _WrW0.z + q1.zw * _WrW0.w + q2.xy * _WrW1.x + q2.zw * _WrW1.y;
                        garment = normalize(half3(garment.xy + wr * _WrGain, garment.z));
                    }
                }
                bool panel = i.construction.z > 3.5;
                bool sewn = i.construction.z > .5 && !panel;
                if (sewn || panel) {
                    garment = half3(0, 0, 1);
                    mask.rg = 1;
                }
                if (panel) {
                    mask.b = 0;
                    mask.a = 0;
                }
                half id = floor(mask.a * (_FabricVersion > 2.5h ? 15 : _FabricVersion > 1.5h ? 9 : 5) + .5h), smoothness, sheen, knit, frequency;
                bool v3 = _AtlasVersion > 2.5h;
                FabricV3Look fv = FabricV3(id, _KnitCell);
                float2 quadrant;
                Fabric(id, smoothness, sheen, knit, quadrant, frequency);
                if (_UseGarmentMaps < .5h) { smoothness = _Smoothness; sheen = _SheenStrength; }
                else if (_FemaleSurface > .5h) { smoothness *= .65h; sheen *= .90h; }
                if (_FemaleSurface>.5h && _EdgeLines>.5h && _EdgeLines<1.5h) { id=i.edge.x>=0?3:2; sheen=0; }
                smoothness = lerp(smoothness, .12h, _MaterialMatte);
                sheen *= lerp(1, .28h, _MaterialMatte);
                float ang = radians(_WeaveAngle); float sn, cs; sincos(ang, sn, cs);
                float2 wuv = float2(cs * i.uv.x - sn * i.uv.y, sn * i.uv.x + cs * i.uv.y) * _WeaveTile;
                if (sewn) wuv = float2(i.construction.x * 64.0, i.construction.y * 0.42);
                if (panel) wuv = i.construction.xy * 77.0;
                // Fade individual threads before their Nyquist limit; UV derivatives are evaluated before frac.
                float2 dx = ddx(wuv), dy = ddy(wuv);
                float footprint = max(max(abs(dx.x), abs(dx.y)), max(abs(dy.x), abs(dy.y)));
                half fade = 1 - smoothstep(.32h, .72h, footprint * frequency);
                float2 atlasUV = (quadrant + .03125 + frac(wuv) * .9375) * .5;
                if (_UseGarmentMaps < .5h) atlasUV = wuv;
                half4 weave;
                if (v3) {
                    // one tile = 8 threads; the yarn relief is kept until a stitch is ~2 px, then the mips carry its average shade
                    fade = 1 - smoothstep(.45h, 1.10h, footprint * 8);
                    float2 cell = float2(fmod(fv.cell, 4), floor(fv.cell / 4));
                    atlasUV = (cell + .03125 + frac(wuv) * .9375) * .25;
                    weave = SAMPLE_TEXTURE2D_GRAD(_WeaveMap, sampler_WeaveMap, atlasUV, dx * .234375, dy * .234375);
                } else weave = SAMPLE_TEXTURE2D_GRAD(_WeaveMap, sampler_WeaveMap, atlasUV, dx * .46875, dy * .46875);
                half fibreCoverage=_FemaleSurface>1.5h ? 1-mask.b:1;
                half2 slope = (weave.rg * 2 - 1) * (v3 ? fv.relief * _FabricDetail : _WeaveNormal) * fade * fibreCoverage;
                if(_FemaleSurface>1.5h)sheen*=fibreCoverage;
                if (!v3 && id > 2.5h && id < 4.5h) slope = 0;
                // Rotate slopes back from the grain coordinate system (the previous male 41-degree correction).
                slope = half2(cs * slope.x + sn * slope.y, -sn * slope.x + cs * slope.y);
                half3 ts = normalize(half3(garment.xy + slope, garment.z));
                float3 tw = i.tangentWS.xyz;
                half3 grain = dot(tw, tw) > 1e-8 ? (half3)normalize(tw) : half3(1, 0, 0);
                if (dot(tw, tw) > 1e-8) {
                    half3 t = normalize(tw), b = cross(n, t) * i.tangentWS.w;
                    n = normalize(TransformTangentToWorld(ts, half3x3(t, b, n)));
                }
                // A visible reverse side of thin cloth shades toward its viewer.
                n *= IS_FRONT_VFACE(facing, 1.0h, -1.0h);
                half threadBreak = lerp(1, weave.b * 1.28h, _WeaveThread * fade * fibreCoverage);
                if (!v3 && id > 2.5h && id < 4.5h) threadBreak = 1;
                // V3: the yarn shade (traced AO x melange) stays on; its mip average is 1 by construction, so far away it only
                // loses the threads, never the cloth's tone. Tonal grain at yarn-bundle scale (palette-neutral, after the tint).
                half mottle = 1;
                if (v3) {
                    threadBreak = lerp(1, weave.b * 1.28h, (.45h + .55h * fade) * fibreCoverage);
                    float2 m1 = wuv * .55, m2 = wuv * 1.9;
                    half f2 = 1 - smoothstep(.5h, 1.2h, max(length(ddx(m2)), length(ddy(m2))));
                    mottle = 1 + _Mottle * ((ClothMottle(m1) - .5h) * 1.4h + (ClothMottle(m2) - .5h) * .9h * f2) * (id > 2.5h && id < 4.5h ? .3h : 1);
                }
                if (_StylePass > .5h && _KnitShow < .5h) { threadBreak = lerp(1, threadBreak, .25h); mottle = lerp(1, mottle, .3h); }   // smooth performance poly: little thread speckle
                half3 albedo = lerp(_BaseColor.rgb, _TrimColor.rgb, mask.b) * threadBreak * mottle;
                if (_MaterialMatte > .5 && v3) {
                    // Bundles of knit loops and woven ribs remain readable in a close
                    // gameplay view. Derivative filtering leaves the atlas average
                    // when the pattern is below a screen pixel.
                    float2 yarn = wuv * float2(4.1, 5.4);
                    half visible = 1 - smoothstep(.31, .80, max(length(ddx(yarn)), length(ddy(yarn))));
                    half warp = cos(6.2831853 * yarn.x);
                    half weft = cos(6.2831853 * yarn.y);
                    half knitBundle = warp * weft * .58h + weft * .27h;
                    half wovenRib = sin(6.2831853 * (yarn.x + yarn.y * .53)) * .65h;
                    half bundleKnit = (fv.cell > .5h && fv.cell < 1.5h) || (fv.cell > 3.5h && fv.cell < 4.5h);
                    half tone = lerp(wovenRib, knitBundle, bundleKnit);
                    albedo *= 1 + ((weave.b - .78h) * .40h + tone * .11h) * visible;
                }
                if (sewn) {
                    float lengthAlong = i.construction.x / .0054;
                    half stitches = 1 - smoothstep(.19, .39, abs(frac(lengthAlong) - .5));
                    stitches *= 1 - smoothstep(.40, .87, fwidth(lengthAlong));
                    half track = i.construction.z > 1.5 ? abs(abs(i.construction.y) - .52) : abs(i.construction.y);
                    half thread = (1 - smoothstep(.13, .39, track)) * stitches;
                    half dark = i.construction.z > 2.5 ? .81 : i.construction.z > 1.5 ? .91 : .87;
                    albedo *= lerp(1, dark + thread * .21h, i.construction.w);
                }
                if (_FemaleSurface>.5h && !(id>2.5h&&id<4.5h)) {
                    // Larger knit clusters remain visible after individual atlas
                    // threads fade. Relative neutral detail preserves all palettes.
                    float2 grainUV=wuv*9;
                    half grainFade=1-smoothstep(.35h,.85h,max(length(ddx(grainUV)),length(ddy(grainUV))));
                    half grain=ClothGrain(grainUV)-.5h;
                    albedo*=1+grain*.09h*grainFade*fibreCoverage;
                    smoothness*=1+grain*.25h*grainFade*fibreCoverage;
                }
                // Applied to the finished colour: the white kit's highlight shoulder would otherwise roll a darker albedo back to white.
                if (panel) albedo *= lerp(1, .685h, i.construction.w);
                half edgeShade = _EdgeLines > .5h ? KitEdgeLines(i.edge) : 1;
                half aoVisibility = lerp(1, max(mask.r, .70h), _AOStrength);
                half ao = lerp(1, aoVisibility, .5h);
                albedo *= lerp(_FemaleSurface>.5h?.88h:.40h, 1, mask.g);
                half ndv = saturate(dot(n, v));
                if (_StylePass > .5h) {
                    // painted fold shadows at full strength, and a top-lit value ramp (lighter up-facing planes, darker under-planes)
                    aoVisibility = lerp(1, max(mask.r, _StyleAOFloor), _AOStrength); ao = aoVisibility;
                    albedo *= lerp(1 - _StyleRamp, 1 + _StyleRamp * .5h, saturate(n.y * .5h + .5h));
                    // colour headroom: a pure, bright pick (#F00, #00F) leaves no room between lit and shadow sides -> cap value, ease saturation
                    half lum = dot(albedo, half3(.2126h, .7152h, .0722h));
                    albedo = lerp(lum.xxx, albedo, _StyleSat);
                    half peak = max(albedo.r, max(albedo.g, albedo.b));
                    albedo *= min(1, _StyleValueCap / max(peak, 1e-3h));
                }

                Light main = HeroMain(GetMainLight());
                main.shadowAttenuation = ClothShadow(i.positionWS);
                if (_HeroLightingEnabled > .5h) main.shadowAttenuation = max(main.shadowAttenuation,.4h);
                half3 colour = _FemaleSurface>.5h ? FemaleClothShade(main,n,v,albedo,smoothness,sheen,ao,id) : Shade(main, n, v, albedo, smoothness, sheen, ao);
                // V3 fibre shine: near-white with a hint of the cloth colour (dielectric fibres), on the yarn crowns, shadowed like the key
                half3 shineTint = lerp(half3(1, 1, 1), albedo / max(max(albedo.r, max(albedo.g, albedo.b)), .05h), .22h);
                half shineK = v3 ? fv.shine * _FibreShine * fibreCoverage : 0;
                if (shineK > 0)
                    colour += shineTint * FibreShine(n, v, main.direction, grain, weave.a, shineK, fv.power, fv.aniso) * ao * main.color * main.distanceAttenuation * main.shadowAttenuation;
                if (_HeroPresentationFill > 0) { Light fill=HeroPresentationLight(v); if(_FemaleSurface>.5h) { fill.color*=.42h; colour+=FemaleClothShade(fill,n,v,albedo,smoothness,sheen,ao,id); } else colour+=Shade(fill,n,v,albedo,smoothness,sheen,ao); }
                #if defined(_ADDITIONAL_LIGHTS)
                uint count = GetAdditionalLightsCount();
                #if defined(_LIGHT_LAYERS)
                uint meshLayers = GetMeshRenderingLayer();
                #endif
                for (uint li = 0; li < count; li++)
                {
                    Light extra = HeroAdditional(GetAdditionalLight(li, i.positionWS));
                    #if defined(_LIGHT_LAYERS)
                    if (!IsMatchingLightLayer(extra.layerMask, meshLayers)) continue;
                    #endif
                    colour += _FemaleSurface>.5h ? FemaleClothShade(extra,n,v,albedo,smoothness,sheen,ao,id) : Shade(extra, n, v, albedo, smoothness, sheen, ao);
                    if (shineK > 0) colour += shineTint * FibreShine(n, v, extra.direction, grain, weave.a, shineK * .6h, fv.power, fv.aniso) * ao * extra.color * extra.distanceAttenuation * extra.shadowAttenuation;
                }
                #endif
                half3 ambient = HeroAmbient(n) * albedo * ao;
                if(_FemaleSurface>.5h) {
                    // Indirect light deepens toward the folds' own colour and falls off
                    // on downward planes, so the garment keeps rounded fold shading.
                    half up=saturate(n.y*.5h+.5h);
                    ambient=HeroAmbient(n)*lerp(albedo,FemaleClothDeep(albedo),.40h)*ao*lerp(.58h,.98h,up*up)*lerp(.80h,1,sqrt(saturate(dot(n,v))));
                }
                #if defined(_SCREEN_SPACE_OCCLUSION)
                AmbientOcclusionFactor screenAO = GetScreenSpaceAmbientOcclusion(GetNormalizedScreenSpaceUV(i.positionCS));
                ambient *= _HeroProfile > .5h ? lerp(1,screenAO.indirectAmbientOcclusion,.35h) : screenAO.indirectAmbientOcclusion;
                colour *= _HeroProfile > .5h ? lerp(1,screenAO.directAmbientOcclusion,.35h) : screenAO.directAmbientOcclusion;
                #endif
                if (_StylePass > .5h) {
                    // sport-poly finish: a GGX highlight from the key light + the environment's reflection at grazing angles
                    half rough = 1 - _StyleSmooth, a2 = max(rough * rough, .03h); a2 *= a2;
                    half3 hv = SafeNormalize(main.direction + v);
                    half nh = saturate(dot(n, hv)), nl = saturate(dot(n, main.direction));
                    half dd = nh * nh * (a2 - 1) + 1;
                    half F = .04h + .96h * pow(1 - saturate(dot(hv, v)), 5);
                    half spec = min(a2 / (PI * dd * dd + 1e-4h) * F * .25h, 6);
                    colour += spec * nl * _StyleSpec * main.color * main.shadowAttenuation * ao;
                    half fres = .04h + .96h * pow(1 - ndv, 5);
                    colour += GlossyEnvironmentReflection(reflect(-v, n), rough, ao) * fres * _StyleEnv;
                    // fabric sheen: sportswear glows softly toward its silhouette where the key reaches it (not a hot spot in the middle)
                    half edge = pow(1 - ndv, 2.5h);
                    colour += lerp(albedo, 1, .35h) * edge * _StyleSheen * saturate(dot(n, main.direction) * .6h + .4h) * main.color * main.shadowAttenuation * ao;
                    // cool, slightly deeper shadow side (the lit side keeps its hue)
                    colour = lerp(colour, colour * half3(.90h, .95h, 1.08h), (1 - nl) * .6h * _StyleCool);
                    // court lighting for clothes: a soft view-side fill (the studio's fill light the venue lacks) so folds, gloss and
                    // colour read under a single hard sun; and a slight counter-tint against the venues' warm grade (whites stay white)
                    colour += albedo * _StyleFill * (.45h + .55h * ndv) * ao * half3(.95h, .98h, 1.05h);
                    colour *= lerp(half3(1, 1, 1), half3(.95h, .98h, 1.05h), _StyleDewarm);
                }
                half rim = pow(1 - ndv, _RimPower) * _RimStrength * (_HeroProfile > .5h ? _HeroRim : 1);
                colour += albedo * knit * pow(1 - ndv, 5) * .045h * saturate(dot(n, main.direction)) * main.shadowAttenuation * main.color;
                half3 rimLight = _RimColor.rgb * rim * saturate(dot(n,main.direction)*.7h+.3h) * (0.35 + 0.65 * albedo) * main.color;
                colour += ambient + (_HeroLightingEnabled > .5h ? HeroPresentationRim(n,v,albedo) : rimLight);
                // Preserve moderate AO contrast through the bright-white highlight shoulder.
                if (_HeroProfile > .5h) {
                    // Neutral construction maps retain the palette under warm postcard keys.
                    // A cloth exposure controls white reflectance; trim keeps its measured dark value.
                    half neutralWhite = smoothstep(.4h,.8h,dot(albedo,half3(.2126h,.7152h,.0722h)));
                    half clothGain = lerp(min(_HeroClothExposure,3),_HeroClothExposure,neutralWhite);
                    colour *= _HeroClothBalance * lerp(clothGain, 1, mask.b);
                    colour *= lerp(.68h, 1, aoVisibility) * lerp(_FemaleSurface>.5h?.95h:.75h, 1, mask.g);
                    if (_HeroFilmResponse < .5h) {
                        half3 legacy = max(colour, albedo * lerp(.35h, 4.0h, mask.b));
                        colour = lerp(legacy, colour, _MaterialMatte);
                    }
                } else {
                    colour = (_HeroFilmResponse>.5h ? colour*_Exposure : SoftShoulder(colour * _Exposure)) * lerp(.68h, 1, aoVisibility) * lerp(_FemaleSurface>.5h?.95h:.75h, 1, mask.g);
                }
                { half mx = max(max(albedo.r, albedo.g), albedo.b), mn = min(min(albedo.r, albedo.g), albedo.b);
                  colour *= 1 - _KitSatCut * saturate((mx - mn) / max(mx, 1e-3)); }   // KIT DETAIL: saturated picks stop clipping to a flat hue
                half3 finish = HeroClothFinish(colour);
                // Keep the folds visible on saturated colors without clipping the key-side highlight.
                half3 wovenFinish = HeroHighlightRoll(colour, .38h, .72h);
                return half4(MixFog(lerp(finish, wovenFinish, _MaterialMatte) * edgeShade, i.fog), 1);
            }
            ENDHLSL
        }
        // Own depth/shadow passes share the exact UnityPerMaterial layout: SRP Batcher compatible.
        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode"="ShadowCaster" }
            ZWrite On ZTest LEqual ColorMask 0
            HLSLPROGRAM
            #pragma vertex shadowVert
            #pragma fragment shadowFrag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"
            float3 _LightDirection;
            struct ShadowInput { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; float4 cageId : TEXCOORD5; float4 cageW : TEXCOORD6; };
            float4 shadowVert(ShadowInput i) : SV_POSITION {
                float3 p = TransformObjectToWorld(i.positionOS.xyz), n = TransformObjectToWorldNormal(i.normalOS);
                p = PoloCage(ClothJiggle(p, n, i.uv), i.cageId, i.cageW);
                float4 clip = TransformWorldToHClip(ApplyShadowBias(p,n,_LightDirection));
                #if UNITY_REVERSED_Z
                clip.z = min(clip.z, UNITY_NEAR_CLIP_VALUE * clip.w);
                #else
                clip.z = max(clip.z, UNITY_NEAR_CLIP_VALUE * clip.w);
                #endif
                return clip;
            }
            half4 shadowFrag() : SV_Target { return 0; }
            ENDHLSL
        }
        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode"="DepthOnly" }
            ZWrite On ColorMask R
            HLSLPROGRAM
            #pragma vertex depthVert
            #pragma fragment depthFrag
            float4 depthVert(float4 p : POSITION, float3 nOS : NORMAL, float2 uv : TEXCOORD0, float4 cageId : TEXCOORD5, float4 cageW : TEXCOORD6) : SV_POSITION { return TransformWorldToHClip(PoloCage(ClothJiggle(TransformObjectToWorld(p.xyz), TransformObjectToWorldNormal(nOS), uv), cageId, cageW)); }
            half4 depthFrag() : SV_Target { return 0; }
            ENDHLSL
        }
        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode"="DepthNormals" }
            ZWrite On
            HLSLPROGRAM
            #pragma vertex normalVert
            #pragma fragment normalFrag
            struct NInput { float4 positionOS : POSITION; float3 normalOS : NORMAL; float4 tangentOS : TANGENT; float2 uv : TEXCOORD0; float4 cageId : TEXCOORD5; float4 cageW : TEXCOORD6; };
            struct NOutput { float4 positionCS : SV_POSITION; float3 normalWS : TEXCOORD0; float4 tangentWS : TEXCOORD1; float2 uv : TEXCOORD2; };
            NOutput normalVert(NInput i) {
                NOutput o; VertexNormalInputs n=GetVertexNormalInputs(i.normalOS,i.tangentOS);o.normalWS=n.normalWS;
                o.positionCS=TransformWorldToHClip(PoloCage(ClothJiggle(TransformObjectToWorld(i.positionOS.xyz),n.normalWS,i.uv),i.cageId,i.cageW));
                o.tangentWS=float4(n.tangentWS,i.tangentOS.w*GetOddNegativeScale());o.uv=i.uv;return o;
            }
            half4 normalFrag(NOutput i, FRONT_FACE_TYPE facing : FRONT_FACE_SEMANTIC) : SV_Target {
                half3 n=normalize(i.normalWS);
                if(_UseGarmentMaps>.5h) {
                    half3 ts=UnpackNormal(SAMPLE_TEXTURE2D(_NormalMap,sampler_NormalMap,i.uv));ts.xy*=_NormalStrength;
                    half3 t=normalize(i.tangentWS.xyz),b=cross(n,t)*i.tangentWS.w;
                    n=normalize(TransformTangentToWorld(ts,half3x3(t,b,n)));
                }
                return half4(n * IS_FRONT_VFACE(facing, 1.0h, -1.0h),0);
            }
            ENDHLSL
        }
    }
    FallBack "Universal Render Pipeline/Lit"
}
