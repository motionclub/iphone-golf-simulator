#ifndef GOLF_ARCADE_HERO_LIGHTING_INCLUDED
#define GOLF_ARCADE_HERO_LIGHTING_INCLUDED
// Both sports preserve display headroom under their actual scene lights. Golf
// additionally publishes its profile exposure and warm course key parameters.
float _HeroProfile;
float _HeroFilmResponse;
half4 _HeroKeyColor, _HeroAmbientSky, _HeroAmbientEquator, _HeroAmbientGround;
half _HeroKeyStrength, _HeroRim, _HeroExposure, _HeroShoulderKnee, _HeroShoulderCeiling;
half3 _HeroClothBalance;
half _HeroClothExposure;
half _HeroPresentationFill;
half _HeroSkinPolish;
half _HeroLightingEnabled;
half4 _HeroFillColor, _HeroAnalyticRimColor;
half _HeroAnalyticRimStrength, _HeroSkinLightExposure;
// Bound environmental chroma without changing the light direction. This is
// hero-only; shadow casters and the scene's lights retain their authored values.
half3 HeroBoundLight(half3 c, half minimum, half maximum)
{
    c = max(c, 0);
    half luminance = dot(c, half3(.2126h,.7152h,.0722h));
    half peak = max(max(c.r,c.g),c.b);
    half trough = min(min(c.r,c.g),c.b);
    // Mixing toward luminance until HSV saturation is at most .35.
    half chroma = min(1, .35h*luminance / max(peak-trough-.35h*(peak-luminance), .0001h));
    c = lerp(luminance.xxx,c,chroma);
    return luminance > .0001h ? c * (clamp(luminance,minimum,maximum)/luminance) : minimum.xxx;
}
half3 HeroPresentationRim(half3 n, half3 v, half3 albedo)
{
    half edge = 1-saturate(dot(n,v));
    // Camera-relative backlight approximation: a cubic grazing lobe. No light
    // slot, shadow lookup, texture sample or material variant.
    return _HeroAnalyticRimColor.rgb * _HeroAnalyticRimStrength * edge*edge*edge * (.35h+.65h*albedo);
}
// A broad camera-side reflector for character surfaces. It consumes no URP
// per-object light slot and never changes the course, court, or ball lighting.
Light HeroPresentationLight(half3 viewDirection)
{
    half3 right = SafeNormalize(cross(half3(0,1,0),viewDirection));
    Light light = (Light)0;
    light.direction = _HeroLightingEnabled > .5h
        ? SafeNormalize(viewDirection*.90h + half3(0,.30h,0) - right*.25h)
        : SafeNormalize(viewDirection*.80h + half3(0,.60h,0) - right*.30h);
    light.color = (_HeroLightingEnabled > .5h ? _HeroFillColor.rgb : half3(1,.95h,.88h))*_HeroPresentationFill;
    light.distanceAttenuation = 1;
    light.shadowAttenuation = 1;
    return light;
}
Light HeroMain(Light light)
{
    #if defined(HERO_PRESENTATION_SURFACE)
    if (_HeroLightingEnabled > .5h) {
        light.color = HeroBoundLight(light.color,0,1.1h);
        light.shadowAttenuation = max(light.shadowAttenuation,.4h);
    } else
    #endif
    if (_HeroProfile > .5) light.color = _HeroKeyColor.rgb * _HeroKeyStrength;
    return light;
}
Light HeroAdditional(Light light)
{
    if (_HeroLightingEnabled > .5h) {
        // Venue point lights can be much brighter than the sun (lava glows).
        // Bound only their contribution to the hero; their world response is intact.
        light.color = HeroBoundLight(light.color,0,.35h);
        light.shadowAttenuation = max(light.shadowAttenuation,.4h);
    }
    return light;
}
half3 HeroAmbient(half3 n)
{
    half3 ambient = SampleSH(n);
    #if defined(HERO_PRESENTATION_SURFACE)
    return _HeroLightingEnabled > .5h ? HeroBoundLight(ambient,.25h,.60h) : ambient;
    #else
    return ambient;
    #endif
}
half3 HeroHighlightRoll(half3 c,half knee,half ceiling)
{
    half peak=max(max(c.r,c.g),max(c.b,1e-4h));
    half span=max(ceiling-knee,.001h);
    half excess=max(peak-knee,0);
    // A late rational shoulder preserves highlight contrast instead of rapidly
    // flattening every bright surface to a single value.
    half rolled=peak<=knee ? peak : knee+span*excess/(span+excess);
    return c*(rolled/peak);
}
// A soft lighting shoulder on skin keeps bright keys/fill from washing out
// the lighter complexion. Pigment, regional face shading and textures are unchanged.
half3 HeroSkinLightFinish(half3 c,half skinFinish)
{
    if (_HeroLightingEnabled > .5h && skinFinish > 1.5h)
        return HeroHighlightRoll(c,.60h,.90h)*_HeroSkinLightExposure;
    return _HeroLightingEnabled > .5h && skinFinish > .5h ? HeroHighlightRoll(c,.35h,.75h)*_HeroSkinLightExposure : c;
}
half3 HeroFinish(half3 c)
{
    if (_HeroFilmResponse > .5 || _HeroProfile < .5) return c;
    return HeroHighlightRoll(c*_HeroExposure,_HeroShoulderKnee,_HeroShoulderCeiling);
}
half3 HeroClothFinish(half3 c)
{
    if (_HeroFilmResponse > .5) return c;
    if (_HeroProfile < .5) return HeroHighlightRoll(c*.98h,.72h,.96h);
    return HeroHighlightRoll(c*.945h,.64h,.88h);
}
half3 HeroCharacterFinish(half3 c,half3 reflection)
{
    if (_HeroFilmResponse > .5) return c;
    half exposure=_HeroProfile > .5 ? _HeroExposure : 1.0h;
    half3 base=_HeroProfile > .5 ? HeroHighlightRoll(max(c-reflection,0)*(.95h*exposure),.70h,.90h) : HeroHighlightRoll(max(c-reflection,0),.76h,.96h);
    half3 room=max(.985h-base,.001h);
    // Retain the authored specular/rim shape after diffuse highlight handling.
    // Each channel approaches its remaining display headroom without clipping.
    reflection=max(reflection,0)*exposure;
    return base+reflection*room/(room+reflection);
}
half HeroWrapped(half3 n,half3 direction,half wrap)
{ return saturate((dot(n,direction)+wrap)/(1+wrap)); }
// A normalized broad lobe for skin plus a narrower varnish lobe for smooth eyes/equipment.
// Grazing reflectance and direct-light visibility prevent the flat clay/plastic silhouette.
half3 HeroCharacterShade (Light light, half3 n, half3 v, half3 albedo, half wrap, half smoothness, half3 subsurface, half specularStrength, out half3 reflection)
{
    half ndl = dot(n, light.direction), nl = saturate(ndl);
    half wrapped = saturate((ndl + wrap) / (1 + wrap));
    half edge = saturate(wrapped - nl) * 1.35h;
    half3 h = SafeNormalize(light.direction + v);
    half nh = saturate(dot(n, h));
    half broad = pow(nh, 10 + smoothness * 30) * .045h;
    half varnish = pow(nh, 24 + smoothness * smoothness * 200) * smoothness * .25h;
    half fresnel = 1 + pow(1 - saturate(dot(v, h)), 5) * 1.5h;
    half spec = (broad + varnish) * specularStrength * fresnel * saturate(ndl * 3);
    half atten = light.distanceAttenuation * light.shadowAttenuation;
    reflection = spec * light.color * atten;
    return (albedo * wrapped + subsurface * edge * albedo) * light.color * atten + reflection;
}
// Work-only skin response, selected per Body material. Other character roles
// retain HeroCharacterShade. Keep direct/fill energy bounded and the skin lobe
// broad, rather than using the narrow varnish contribution of eyes/equipment.
half3 HeroSkinShade (Light light, half3 n, half3 v, half3 albedo, half wrap, half smoothness, half3 subsurface, half specularStrength, out half3 reflection)
{
    half ndl = dot(n, light.direction);
    half wrapped = saturate((ndl + wrap) / (1 + wrap));
    half edge = saturate(wrapped - saturate(ndl));
    half3 h = SafeNormalize(light.direction + v);
    half nh = saturate(dot(n, h));
    half broad = pow(nh, 18 + smoothness * 18) * .075h;
    if (_HeroSkinPolish > .5h) {
        // Softbox skin: concentrate the broad wash into a visible satin core.
        // Lower integrated reflection energy preserves the side-plane colour;
        // the soft shoulder keeps the highlight transition from becoming oily.
        // Rougher lips/neck remain below the forehead/nose response.
        half glossWeight = .16h + .84h * saturate((smoothness - .32h) / .06h);
        broad = (pow(nh, 5 + smoothness * 6) * .035h
               + pow(nh, 18 + smoothness * 18) * .40h) * glossWeight;
    }
    half visibility = smoothstep(-.06h, .24h, ndl);
    half shadow = lerp(light.shadowAttenuation, 1, .12h);
    half atten = light.distanceAttenuation * shadow;
    reflection = broad * specularStrength * visibility * light.color * atten;
    return albedo * (wrapped * .84h + subsurface * edge) * light.color * atten + reflection;
}
// Female athlete: clean diffuse form with a restrained satin lobe and a warm
// terminator. No extra light, screen pass, pore texture or fixed skin-tone paint.
half3 HeroFemaleSkinShade(Light light, half3 n, half3 v, half3 albedo, half smoothness, out half3 reflection)
{
    half ndl=dot(n,light.direction), nl=saturate(ndl);
    half wrapped=saturate((ndl+.26h)/1.26h);
    half nh=saturate(dot(n,SafeNormalize(light.direction+v)));
    half lobe=pow(nh,12+smoothness*12)*.035h+pow(nh,32+smoothness*24)*.018h;
    half visibility=smoothstep(-.04h,.28h,ndl);
    half attenuation=light.distanceAttenuation*lerp(light.shadowAttenuation,1,.08h);
    reflection=lobe*.65h*visibility*light.color*attenuation;
    half3 diffuse=wrapped*.88h+half3(.30h,.12h,.08h)*saturate(wrapped-nl);
    return albedo*diffuse*light.color*attenuation+reflection;
}

#endif
