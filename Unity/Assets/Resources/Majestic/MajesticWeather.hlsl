#ifndef MAJESTIC_WEATHER_INCLUDED
#define MAJESTIC_WEATHER_INCLUDED
#if defined(MAJESTIC_WEATHER_ON)
// Majestic weather inside the world materials (chat W, work/majestic-weather, 10-17).
// Included by Environment/Shaders/EnvironmentSurface.hlsl (one hook, patch for chat 6) so every world shader
// that ends in EnvironmentFog / EnvironmentBackdrop gets: wet darkening + gloss + puddles with sky/sun
// reflections and ripples, snow/ash cover on up-facing ground (play corridor, green and court kept clear),
// frost sparkle, grass waves and racing cloud shadows in wind, whitecaps, lightning/eruption light, and
// height + distance fog toward the rendered sky's colour. Replaces the three full-screen weather volumes.
// Compiled only into the MAJESTIC_WEATHER_ON variant (a global fragment keyword the layer enables while weather
// is active). Without it this file defines nothing but pass-through macros, so the world shaders' off variant is
// exactly their original code (TOGGLE_RESTORES).
// Units: world positions are in the scene's units (golf yards, tennis metres); _MajUnit = metres per unit.

half _MajWeatherOn;
float _MajUnit;
float4 _MajWet;       // x wetness, y puddle coverage, z rain falling (ripples), w drying (0 all wet .. 1 edges/slopes dry)
float4 _MajCover;     // rgb snow/ash colour, a amount
float4 _MajCoverFx;   // x frost sparkle, y keep the play corridor clear (0..1), z ember specks, w how much cover lands on turf (0..1)
float4 _MajCorridor;  // xy = corridor start (world xz), zw = end
float4 _MajClear;     // xz centre of the green / court (x,z in .xz of xyz), w radius (units): no cover, fewer puddles
float4 _MajFogColor;  // rgb fog colour, a max fog
float4 _MajFog;       // x density per metre, y height falloff per metre, z base height (world y), w clear radius (metres)
float4 _MajFogGlow;   // rgb forward-scatter glow toward the sun (or lava below), a strength
float4 _MajObserver;  // xyz golfer (gameplay fog observer), w 1 = golf fog visibility rule active
float4 _MajSkyRefl;   // rgb what wet ground mirrors (cloud / sky), a gloss
float4 _MajSunDir;    // xyz toward the sun, w sun-glint strength on wet ground
float4 _MajSunCol;    // rgb sun colour x intensity
float4 _MajWind;      // xy wind direction (xz), z strength 0..1, w gust 0..1 now
float4 _MajTime;      // x seconds, y grass waves, z cloud shadows, w whitecaps
float4 _MajFlash;     // rgb flash light (lightning / eruption), a -
float4 _MajWater;     // x water level (world y), y 1 = whitecaps apply to flat water at that level
float4 _MajPools;     // x lava pools (ash), y ice pools (snow), z sky-reflection exposure (the weather's darker sky), w 1 = _MajSkyMap bound
#if !defined(MAJESTIC_WEATHER_LITE)
TEXTURE2D(_MajSkyMap); SAMPLER(sampler_MajSkyMap);   // the rendered sky as an equirect (RenderedSky.Reflection)
#endif

static half _majTurf = 0;   // set by EnvironmentTurfWeather (turf only), read by the same pixel's EnvironmentFog
static half _majWaterPx = 0;   // set by MajesticWeatherWater (the sea shader only): whitecaps go on water, never on low ground

float MajHash(float2 p) { p = frac(p * float2(123.34, 456.21)); p += dot(p, p + 45.32); return frac(p.x * p.y); }
float MajNoise(float2 p)
{
    float2 i = floor(p), f = frac(p); f = f * f * (3 - 2 * f);
    float a = MajHash(i), b = MajHash(i + float2(1, 0)), c = MajHash(i + float2(0, 1)), d = MajHash(i + float2(1, 1));
    return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
}
float MajSegDist(float2 p, float2 a, float2 b)
{
    float2 ab = b - a; float t = saturate(dot(p - a, ab) / max(dot(ab, ab), 1e-4));
    return length(p - a - ab * t);
}
half MajLum(half3 c) { return dot(c, half3(.2126h, .7152h, .0722h)); }

/// The sky in direction R (RenderedSky's equirect, same mapping as TennisWorldSurface), darkened as the weather darkens it;
/// near the horizon the treeline / shore reads as a dark band, as it does in a real puddle.
half3 MajSky(float3 R, float lod)
{
    half3 sky = _MajSkyRefl.rgb;
#if !defined(MAJESTIC_WEATHER_LITE)
    if (_MajPools.w > .5)
    {
        float2 uv = float2(frac(atan2(R.z, R.x) / 6.2831853 + .5), clamp(.53 + asin(saturate(R.y)) / 3.14159265, .53, .975));
        sky = SAMPLE_TEXTURE2D_LOD(_MajSkyMap, sampler_MajSkyMap, uv, lod).rgb * _MajPools.z;
    }
#endif
    half band = 1 - smoothstep(.02, .16, R.y);
    return lerp(sky, _MajSkyRefl.rgb * .3, band * .8);
}

/// Puddle blobs on flat ground: x = the water (0..1), y = the damp rim just outside it.
float2 MajPuddles(float2 wm, float cover, float up)
{
    float pn = MajNoise(wm * .11) * .68 + MajNoise(wm * .43 + 7.3) * .32;
    float flat = smoothstep(.955, .992, up);
    float edge = 1 - cover;
    return float2(smoothstep(edge, edge + .03, pn) * flat, smoothstep(edge - .08, edge, pn) * (1 - smoothstep(edge, edge + .03, pn)) * flat);
}

/// Raindrop rings: one drop per cell at a random spot and time; returns the ring's slope (xz) for the water normal.
float2 MajRipple(float2 g, float t, float seed)
{
    float2 cell = floor(g), f = frac(g) - .5;
    float h = MajHash(cell + seed * 13.7);
    f -= (float2(MajHash(cell + 3.7 + seed), h) - .5) * .5;
    float ph = frac(t + h), r = length(f), front = ph * .48;
    float ring = sin((r - front) * 48) * saturate(1 - abs(r - front) * 10) * (1 - ph) * (1 - ph);
    return f / max(r, 1e-3) * ring;
}

/// Open water (GolfOcean): whitecaps may form here.
half3 MajesticWeatherWater(half3 c) { _majWaterPx = 1; return c; }

/// Turf: the pixel is grass (grass waves, full porosity). Returns the colour unchanged; the weather lands in EnvironmentFog.
half3 MajesticWeatherTurf(half3 c) { _majTurf = 1; return c; }

half3 MajesticWeatherSurface(half3 c, float3 w)
{
    float3 toCam = _WorldSpaceCameraPos - w;
    float dist = length(toCam);
    float3 V = toCam / max(dist, 1e-4);
    float3 n = cross(ddy(w), ddx(w));
    n = n / max(length(n), 1e-6);
    if (dot(n, V) < 0) n = -n;
    float up = saturate(n.y);
    float metres = dist * _MajUnit;
    float2 wm = w.xz * _MajUnit;
    float t = _MajTime.x;
    float2 wd = _MajWind.xy;
    half turf = _majTurf;

    // keep clear: the green / court, and the line of play
    float clearZone = 1 - smoothstep(_MajClear.w * .8, _MajClear.w, distance(w.xz, _MajClear.xz));
    float corridor = (1 - smoothstep(5, 12, MajSegDist(w.xz, _MajCorridor.xy, _MajCorridor.zw) * _MajUnit)) * _MajCoverFx.y;
    float keep = max(clearZone, corridor);

    // wind: soft cloud shadows drifting over the land, grass waves rolling over the turf
    // (10-18 phone report "insane shadows going everywhere": these were hard-edged 50 m blobs at up to 20 m/s; now
    // ~110 m soft patches at 2-8 m/s, like real cumulus shadows)
    float speed = 2 + 6 * _MajWind.z;
    if (_MajTime.z > 0)
    {
        float2 q = wm * .009 - wd * t * speed * .009;
        float s = MajNoise(q) * .7 + MajNoise(q * 2.3 + 3.1) * .3;
        c *= 1 - _MajTime.z * smoothstep(.4, .68, s);
    }
    if (turf > 0 && _MajTime.y > 0)
    {
        float along = dot(wm, wd);
        float wave = sin(along * .35 - t * (1.4 + 1.6 * _MajWind.w) + MajNoise(wm * .06) * 5.0) * .5 + .5;   // ~18 m apart, ~4-9 m/s
        float gustBand = smoothstep(.35, .75, MajNoise(wm * .025 - wd * t * .05));   // gusts arrive in patches
        float fade = 1 - smoothstep(90, 200, metres);
        half lift = (pow(wave, 3) * .35 - .05) * (.4 + .6 * gustBand);   // a sheen, never a dark stripe
        c = c * (1 + _MajTime.y * fade * lift) + half3(.07, .1, .03) * _MajTime.y * fade * pow(wave, 5) * gustBand;   // bent grass shows its pale side
    }

    // wet: darker by porosity and deeper in colour; then puddles: flat blobs that mirror the (weather-darkened)
    // rendered sky with the treeline as a dark band at the horizon, a muddy shallow bottom, a damp rim, raindrop
    // ring ripples near the camera and a sharp sun glint. Ash: glowing lava pools with a cooling crust. Snow: ice pools.
    float wet = _MajWet.x;
    float poolCover = max(_MajWet.y, max(_MajPools.x, _MajPools.y));
    float2 pools = poolCover > 0 && up > .95 ? MajPuddles(wm, poolCover, up) : float2(0, 0);
    float poolFade = (1 - clearZone * .85) * (1 - smoothstep(80, 200, metres));      // water may lie on the fairway (cosmetic)
    float hotFade = (1 - clearZone) * (1 - corridor) * (1 - smoothstep(35, 70, metres));  // lava never on the line of play or the green; near only (cost)
    if (wet > 0)
    {
        float porous = lerp(.6, 1, turf);
        float wetHere = saturate(wet - _MajWet.w * (1 - up * up) * 1.5);
        half lw = MajLum(c);
        c = lerp(lw.xxx, c, 1 + .18 * wetHere);                       // wet colour is deeper
        c *= 1 - wetHere * lerp(.42, .22, turf) * porous;
        // a thin film of water on the whole surface: a soft sheen of the sky at grazing angles
        float fresW = .02 + .98 * pow(1 - saturate(dot(n, V)), 5);
        half3 film = lerp(_MajSkyRefl.rgb * .3, _MajSkyRefl.rgb, smoothstep(.02, .2, reflect(-V, n).y));   // cheap: no texture for the film
        c = lerp(c, film, saturate(fresW * wetHere * lerp(.5, .18, turf)));
    }
    if (_MajWet.y > 0 && wet > 0)
    {
        float drying = saturate(1 - _MajWet.w * .8);
        float puddle = pools.x * poolFade * drying;
        float rim = pools.y * poolFade * drying;
        c *= 1 - rim * .28;                                           // the damp ring round each puddle
        if (puddle > 0)
        {
            float3 N = float3(0, 1, 0);
            if (_MajWet.z > 0 && metres < 32)
            {
                float fadeR = (1 - metres / 32) * _MajWet.z;
                float2 g1 = MajRipple(wm * 2.3, t * 1.15, 0), g2 = MajRipple(wm * 3.1 + 17.3, t * 1.4, 1);
                N.xz += (g1 + g2 * .8) * .35 * fadeR;
                N = normalize(N);
            }
            float3 R = reflect(-V, N);
            float fres = .02 + .98 * pow(1 - saturate(dot(N, V)), 5);
            half3 bottom = c * half3(.55, .5, .44);                   // the shallow, muddy bottom seen through the water
            half3 mirror = MajSky(R, .6);
            float glint = pow(saturate(dot(R, _MajSunDir.xyz)), 900) * 40 + pow(saturate(dot(R, _MajSunDir.xyz)), 60) * .6;
            half3 water = lerp(bottom, mirror, saturate(fres * 1.15)) + _MajSunCol.rgb * glint * _MajSunDir.w * .35;
            c = lerp(c, water, puddle);
        }
    }
    if (_MajPools.x > 0 && hotFade > 0)
    {
        // lava pools (ash weathers): a molten core under a cracked, cooling crust, a scorched rim, a heat halo
        float lava = pools.x * hotFade * (1 - turf * .4);
        float halo = pools.y * hotFade * (1 - turf * .3);
        if (lava + halo > 0)
        {
            float2 q = wm * 1.6 + float2(t * .05, -t * .03);
            float cells = MajNoise(q) * .55 + MajNoise(q * 2.7 + 5.1) * .45;
            float crack = 1 - smoothstep(.04, .14, abs(cells - .5));    // bright seams between crust plates
            float pulse = .8 + .2 * sin(t * 1.7 + MajNoise(wm * .3) * 9);
            half3 molten = lerp(half3(1.0, .28, .04), half3(1.6, .9, .25), crack) * pulse * 2.2;
            half3 crust = half3(.05, .035, .03);
            float open = saturate(crack + smoothstep(.25, .9, pools.x) * .6);
            half3 pool = lerp(crust, molten, open);
            c = lerp(c, c * half3(.35, .22, .18) + half3(.25, .06, .01) * pulse, halo * _MajPools.x);   // scorched, glowing rim
            c = lerp(c, pool, lava * _MajPools.x);
        }
    }
    if (_MajPools.y > 0)
    {
        // ice pools (snow weathers): frozen puddles, pale blue, mirror-smooth, a few white cracks
        float ice = pools.x * poolFade * _MajPools.y;
        if (ice > 0)
        {
            float3 R = reflect(-V, float3(0, 1, 0));
            float fres = .04 + .96 * pow(1 - saturate(dot(float3(0, 1, 0), V)), 5);
            float cracks = 1 - smoothstep(.0, .03, abs(MajNoise(wm * 2.1) - .5)) ;
            half3 iceCol = lerp(half3(.55, .7, .82) * max(MajLum(c) * 2.5, .35), MajSky(R, 1.0), saturate(fres + .25));
            iceCol += cracks * .35 + pow(saturate(dot(R, _MajSunDir.xyz)), 400) * _MajSunCol.rgb * 3;
            c = lerp(c, iceCol, ice);
        }
    }
    // snow / ash settled on what faces up (lines, green, court and the line of play kept clear)
    float cov = _MajCover.a;
    if (cov > 0)
    {
        float cn = MajNoise(wm * .3) * .62 + MajNoise(wm * 2.3 + 1.3) * .38;
        float slope = smoothstep(.45, .85, up);
        float m = slope * smoothstep(1 - cov - .12, 1 - cov + .12, cn * .75 + up * .25) * (1 - keep) * lerp(1, _MajCoverFx.w, turf);
        half light = saturate(MajLum(c) * 2.4);
        half3 shade = lerp(_MajCover.rgb * half3(.62, .7, .86), _MajCover.rgb, light);
        half3 covered = shade * (.62 + .5 * light);
        if (_MajCoverFx.x > 0 && metres < 45)
        {
            float2 sc = floor(wm * 22 + V.xz * 9);
            float spark = step(.984, MajHash(sc)) * (1 - metres / 45) * _MajCoverFx.x;
            covered += spark * 2.2;
        }
        if (_MajCoverFx.z > 0)
        {
            float2 ec = floor(wm * 5);
            float ember = step(.985, MajHash(ec)) * (.6 + .4 * sin(t * 3 + MajHash(ec + 9) * 20)) * _MajCoverFx.z;
            covered += half3(1, .38, .1) * ember * 1.4;
        }
        c = lerp(c, covered, saturate(m));
    }

    // whitecaps: foam streaks over open water, running with the wind
    if (_majWaterPx > .5h && _MajTime.w > 0)
    {
        float2 q = float2(dot(wm, wd), dot(wm, float2(-wd.y, wd.x)));
        float foam = MajNoise(float2(q.x * .05 - t * .25, q.y * .2)) * MajNoise(float2(q.x * .19 - t * .6, q.y * .55));
        foam = smoothstep(.42, .55, foam) * _MajTime.w * (1 - smoothstep(200, 900, metres));
        c = lerp(c, half3(.9, .94, .97) * max(MajLum(_MajSunCol.rgb) * .9, .45), foam);
    }

    c += c * _MajFlash.rgb + _MajFlash.rgb * .05;
    return c;
}

/// Weather fog amount at `w` (0..1): height + distance fog, thick low over water and hollows, thin on high ground;
/// in golf fog the gameplay visibility rule (DreamConditions.Visibility around the golfer) is never undercut.
half MajesticWeatherFogAmount(float3 w)
{
    float3 ray = w - _WorldSpaceCameraPos;
    float run = max(length(ray) * _MajUnit - _MajFog.w, 0);
    float k = max(_MajFog.y, 1e-4);
    float camH = (_WorldSpaceCameraPos.y - _MajFog.z) * _MajUnit, endH = (w.y - _MajFog.z) * _MajUnit;
    // density x e^(-k h) integrated along the straight ray from camera height to the point's height
    float dh = endH - camH;
    float base = _MajFog.x * exp(clamp(-k * camH, -40.0, 8.0));
    float depth = abs(dh) < 1e-3 ? base * run : base * run * (1 - exp(clamp(-k * dh, -40.0, 40.0))) / (k * dh);
    half a = min(1 - exp(-max(depth, 0)), _MajFogColor.a);
    if (_MajObserver.w > .5)
    {
        float2 delta = w.xz - _MajObserver.xz;
        float bank = 1 + .18 * sin((w.x + _MajObserver.x) * .009) + .12 * cos((w.z + _MajObserver.z) * .013);
        float height = 1 + .12 * tanh((_MajObserver.y - w.y) / 20);
        float vis = exp(-max(0, length(delta) - 12) * .042 * bank * height);
        // the rule hides the GROUND beyond sight; trees, cliffs and landmarks rise out of the bank (PLAN 4.4 "fog bank")
        float above = (w.y - (_MajObserver.y + 2)) * _MajUnit;
        vis = lerp(vis, 1, smoothstep(1, 12, above) * .95);
        a = max(a, 1 - vis);
    }
    return a;
}

half3 MajesticWeatherFogColor(float3 w)
{
    float3 d = normalize(w - _WorldSpaceCameraPos);
    float s = pow(saturate(dot(d, _MajSunDir.xyz)), 6);
    float low = 1 - saturate((w.y - _MajFog.z) * _MajUnit / 40);   // lava / sun glow pooled in the low banks
    return _MajFogColor.rgb + _MajFogGlow.rgb * _MajFogGlow.a * (s * .7 + low * .3) + _MajFlash.rgb * .25;
}

/// The whole weather for one world pixel: surface weather, then fog over it composed with the venue's own
/// distance fog (`venueAmount`, `venueColor`) by max, so a pixel never gets two washes.
half3 MajesticWeatherFinish(half3 c, float3 w, half venueAmount, half3 venueColor)
{
    c = MajesticWeatherSurface(c, w);
    half mine = MajesticWeatherFogAmount(w);
    half total = max(venueAmount, mine);
    half3 fogColor = lerp(venueColor, MajesticWeatherFogColor(w), mine / max(total, 1e-3h));
    return lerp(c, fogColor, saturate(total));
}

/// For shaders that end in URP's MixFog (rocks, pines, botanicals): the weather, or exactly MixFog when off.
half MajesticVenueFog(half fogFactor)
{
    half a = 0;
    #if defined(FOG_LINEAR_KEYWORD_DECLARED)
    if (FOG_LINEAR) a = 1 - ComputeFogIntensity(fogFactor);
    #endif
    #if defined(FOG_EXP_KEYWORD_DECLARED)
    if (FOG_EXP) a = 1 - ComputeFogIntensity(fogFactor);
    #endif
    #if defined(FOG_EXP2_KEYWORD_DECLARED)
    if (FOG_EXP2) a = 1 - ComputeFogIntensity(fogFactor);
    #endif
    return a;
}
half3 MajesticWeatherMixFog(half3 c, half fogFactor, float3 w)
{
    if (_MajWeatherOn > .5h) return MajesticWeatherFinish(c, w, MajesticVenueFog(fogFactor), unity_FogColor.rgb);
    return MixFog(c, fogFactor);
}

/// Backdrop pieces (distant islands): only the fog.
half3 MajesticWeatherBackdrop(half3 c, float3 w)
{
    half a = MajesticWeatherFogAmount(w);
    return lerp(c, MajesticWeatherFogColor(w), a);
}
#else
// off variant: the hooks collapse to the original expressions
#define MajesticWeatherMixFog(c, fogFactor, w) MixFog(c, fogFactor)
#define MajesticWeatherWater(c) (c)
#define MajesticWeatherTurf(c) (c)
#endif
#endif
