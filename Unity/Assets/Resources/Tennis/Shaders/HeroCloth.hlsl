#ifndef GOLF_ARCADE_HERO_CLOTH_INCLUDED
#define GOLF_ARCADE_HERO_CLOTH_INCLUDED
// Shared cloth surface core. v1 map bytes and the tennis branch stay unchanged.
half ClothShadow(float3 world)
            {
                #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
                return MainLightRealtimeShadow(ComputeScreenPos(TransformWorldToHClip(world)));
                #elif defined(MAIN_LIGHT_CALCULATE_SHADOWS)
                float4 sc = TransformWorldToShadowCoord(world);
                ShadowSamplingData data = GetMainLightShadowSamplingData();
                float2 stepUV = data.shadowmapSize.xy * .45;
                half a = SAMPLE_TEXTURE2D_SHADOW(_MainLightShadowmapTexture, sampler_LinearClampCompare, sc.xyz + float3(stepUV,0));
                half b = SAMPLE_TEXTURE2D_SHADOW(_MainLightShadowmapTexture, sampler_LinearClampCompare, sc.xyz - float3(stepUV,0));
                half attenuation = LerpWhiteTo((a+b)*.5h, GetMainLightShadowParams().x);
                if (BEYOND_SHADOW_FAR(sc)) attenuation=1;
                return lerp(attenuation, 1, GetMainLightShadowFade(world));
                #else
                return 1;
                #endif
            }
half3 Shade(Light light, half3 n, half3 v, half3 albedo, half smoothness, half sheenStrength, half ao)
            {
                half ndl = dot(n, light.direction), nl = saturate(ndl), nv = saturate(dot(n, v));
                half wrapped = saturate((ndl + _Wrap) / (1 + _Wrap));
                half3 h = SafeNormalize(light.direction + v);
                half nh = saturate(dot(n, h));
                half invR = rcp(max(1 - smoothness, .25h));
                half charlie = (2 + invR) * pow(max(1 - nh * nh, .0001h), invR * .5h) * .15915494h;
                half visibility = rcp(max(4 * (nl + nv - nl * nv), .08h));
                half3 sheen = albedo * (charlie * visibility * nl * sheenStrength);
                half spec = pow(nh, smoothness * 28 + 2) * smoothness * .22h * nl * ao;
                return (albedo * wrapped * ao + spec + sheen * ao) * light.color * light.distanceAttenuation * light.shadowAttenuation;
            }
void Fabric(half id, out half smoothness, out half sheen, out half knit, out float2 quadrant, out half frequency)
            {
                smoothness = .10h; sheen = .55h; knit = 1; quadrant = float2(0,0); frequency = 8;
                if (id > .5h && id < 1.5h) { smoothness = .13h; sheen = .38h; quadrant = float2(1,0); frequency = 12; }
                else if (id < 2.5h && id > 1.5h) { smoothness = .16h; sheen = .24h; knit = 0; quadrant = float2(0,1); }
                else if (id < 3.5h && id > 2.5h) { smoothness = .04h; sheen = 0; knit = 0; quadrant = float2(1,1); }
                else if (id < 4.5h && id > 3.5h) { smoothness = .08h; sheen = 0; knit = 0; quadrant = float2(1,1); }
                else if (id > 4.5h) { smoothness = .10h; sheen = .18h; knit = 0; quadrant = float2(1,0); }
                // Version 2 extends the decoder. Version 1 keeps its six IDs and bytes.
                if (_FabricVersion > 1.5h && id > 5.5h) {
                    if (id < 6.5h) { smoothness=.09h;sheen=.24h;knit=0;quadrant=float2(0,0);frequency=8; }
                    else if (id < 7.5h) { smoothness=.12h;sheen=.32h;knit=1;quadrant=float2(1,0);frequency=10; }
                    else if (id < 8.5h) { smoothness=.18h;sheen=.10h;knit=0;quadrant=float2(0,1);frequency=8; }
                    else { smoothness=.08h;sheen=.18h;knit=0;quadrant=float2(1,1);frequency=8; }
                }
            }
// Clothing V3 (2026-10-26): the 4 x 4 fabric atlas built from real yarn geometry in Blender (work/clothing-v3/fabric).
// Cells: 0 twill, 1 pique, 2 leather, 3 2x2 rib, 4 jersey, 5 plain weave (rayon / gabardine), 6 canvas, 7 suede, 8 rubber, 9 knit mesh.
// Per cell: normal strength of the yarn relief, fibre shine (strength, Blinn power, anisotropic along the grain).
struct FabricV3Look { half cell, relief, shine, power, aniso; };
FabricV3Look FabricV3(half id, half knitCell)
{
    FabricV3Look f; f.cell = 1; f.relief = .30h; f.shine = .22h; f.power = 10; f.aniso = 0;
    // V2 garment ids (M alpha * 9) keep their meaning; 7 = the garment's knit (pique polo, jersey tank / socks via _KnitCell)
    if (id < .5h || (id > 5.5h && id < 6.5h)) { f.cell = 0; f.relief = .32h; f.shine = .10h; f.power = 8; }      // twill shorts / trousers / skirts
    else if (id < 1.5h || (id > 4.5h && id < 5.5h)) { f.cell = 1; }
    else if (id < 2.5h || (id > 7.5h && id < 8.5h)) { f.cell = 2; f.relief = .22h; f.shine = .35h; f.power = 28; }  // leather
    else if (id < 4.5h) { f.cell = 8; f.relief = .12h; f.shine = .10h; f.power = 30; }                            // rubber / foam
    else if (id < 7.5h) { f.cell = knitCell; f.relief = knitCell > 3.5h ? .26h : .30h; f.shine = knitCell > 3.5h ? .16h : .22h; f.power = 10; }
    else if (id < 9.5h) { f.cell = 3; f.relief = .34h; f.shine = .12h; f.power = 12; }                            // rib
    // V3-only ids (M alpha * 15, bowling kits)
    else if (id < 10.5h) { f.cell = 5; f.relief = .18h; f.shine = .24h; f.power = 24; f.aniso = 1; }             // rayon / gabardine: silky, along the grain
    else if (id < 11.5h) { f.cell = 6; f.relief = .32h; f.shine = .06h; f.power = 8; }                            // canvas
    else if (id < 12.5h) { f.cell = 7; f.relief = .14h; f.shine = .03h; f.power = 6; }                            // suede
    else if (id < 13.5h) { f.cell = 9; f.relief = .30h; f.shine = .14h; f.power = 10; }                           // knit mesh
    else { f.cell = 4; f.relief = .26h; f.shine = .16h; f.power = 10; }                                           // jersey
    return f;
}
// Fibre shine: a soft highlight that sits on the yarn crowns (atlas A). Polyester / rayon / leather have one; it is what makes cloth
// read as a material instead of paint. Anisotropic cells stretch it across the grain (Kajiya-Kay on the weave direction).
half FibreShine(half3 n, half3 v, half3 l, half3 grain, half crown, half shine, half power, half aniso)
{
    half3 h = SafeNormalize(l + v);
    half nl = saturate(dot(n, l));
    half nh = saturate(dot(n, h));
    half iso = pow(nh, power);
    half th = dot(grain, h);
    half kk = pow(saturate(sqrt(max(1 - th * th, 0))), power * 2.2h);
    half lobe = lerp(iso, kk, aniso);
    half fres = .65h + .35h * pow(1 - saturate(dot(n, v)), 3);
    return lobe * shine * nl * fres * lerp(.55h, 1.25h, crown) * (power + 2) * .125h;
}
// Two octaves of tonal grain at yarn-bundle scale: survives at distance (it is far coarser than a thread), palette-neutral.
half ClothMottle(float2 p)
{
    float2 i = floor(p), f = frac(p); f = f * f * (3 - 2 * f);
    float a = frac(sin(dot(i, float2(127.1, 311.7))) * 43758.5453), b = frac(sin(dot(i + float2(1, 0), float2(127.1, 311.7))) * 43758.5453);
    float c = frac(sin(dot(i + float2(0, 1), float2(127.1, 311.7))) * 43758.5453), d = frac(sin(dot(i + 1, float2(127.1, 311.7))) * 43758.5453);
    return (half)lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
}
half3 SoftShoulder (half3 c)
            {
                half peak = max(max(c.r, c.g), max(c.b, 1e-4));
                half k = _Knee;
                half rolled = peak <= k ? peak : k + (1 - k) * (1 - exp(-(peak - k) / (1 - k)));
                return c * (rolled / peak);
            }

#endif
