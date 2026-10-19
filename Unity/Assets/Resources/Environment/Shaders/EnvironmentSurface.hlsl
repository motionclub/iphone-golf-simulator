#ifndef PARTY_ENVIRONMENT_SURFACE_INCLUDED
#define PARTY_ENVIRONMENT_SURFACE_INCLUDED
// Shared presentation contract for ground, foliage, prop, water and emissive
// variants. Sky retains its authored panorama/horizon response. No hero include.
half _EnvironmentDepthEnabled, _EnvironmentWeatherEnabled;
float _EnvironmentMetresPerUnit;
float4 _EnvironmentDepthLayers;
half4 _EnvironmentHazeColor;
half _DreamNight;
half _EnvironmentWetness, _EnvironmentSnow, _EnvironmentStorm;
// MAJESTIC_WEATHER_HOOK (chat W, work/majestic-weather): weather inside the world materials, in the MAJESTIC_WEATHER_ON variant only.
#include "Assets/Resources/Majestic/MajesticWeather.hlsl"

half EnvironmentLayerAmount(float3 world)
{
    float metres=distance(_WorldSpaceCameraPos,world)*_EnvironmentMetresPerUnit;
    // Full color in play, a separate middle veil, then a quieter far silhouette.
    return smoothstep(_EnvironmentDepthLayers.x,_EnvironmentDepthLayers.y,metres)*.24h
         + smoothstep(_EnvironmentDepthLayers.y,_EnvironmentDepthLayers.z,metres)*.48h;
}
#if defined(MAJESTIC_WEATHER_ON) // MAJESTIC_WEATHER_HOOK: the venue's own fog amount, composed by max with the weather's
half MajesticVenueFogAmount(half fogFactor,float3 world)
{
    half venueAmount=MajesticVenueFog(fogFactor);
    return _EnvironmentDepthEnabled>.5h?max(venueAmount,EnvironmentLayerAmount(world)):venueAmount;
}
#endif
half3 EnvironmentFog(half3 color,half fogFactor,float3 world)
{
    #if defined(MAJESTIC_WEATHER_ON) // MAJESTIC_WEATHER_HOOK
    if(_MajWeatherOn>.5h)return MajesticWeatherFinish(color,world,MajesticVenueFogAmount(fogFactor,world),unity_FogColor.rgb);
    #endif
    if(_EnvironmentDepthEnabled<.5h)return MixFog(color,fogFactor);
    // Max rather than addition: the weather/venue fog and depth layers must not
    // apply two separate washes to the same pixel.
    // URP returns zero intensity when no fog keyword is active; that means
    // disabled fog, not an opaque veil. Keep the independent distance layers.
    half venueAmount=0;
    #if defined(FOG_LINEAR_KEYWORD_DECLARED)
    if(FOG_LINEAR)venueAmount=1-ComputeFogIntensity(fogFactor);
    #endif
    #if defined(FOG_EXP_KEYWORD_DECLARED)
    if(FOG_EXP)venueAmount=1-ComputeFogIntensity(fogFactor);
    #endif
    #if defined(FOG_EXP2_KEYWORD_DECLARED)
    if(FOG_EXP2)venueAmount=1-ComputeFogIntensity(fogFactor);
    #endif
    half amount=max(venueAmount,EnvironmentLayerAmount(world));
    return lerp(color,unity_FogColor.rgb,saturate(amount));
}
half3 EnvironmentBackdrop(half3 color,float3 world)
{
    #if defined(MAJESTIC_WEATHER_ON) // MAJESTIC_WEATHER_HOOK
    if(_MajWeatherOn>.5h)color=MajesticWeatherBackdrop(color,world);
    #endif
    return _EnvironmentDepthEnabled>.5h ? lerp(color,_EnvironmentHazeColor.rgb,EnvironmentLayerAmount(world)) : color;
}
// Turf's wet overlay already owns darkening/gloss. This owns only chroma;
// it cannot darken the ground a second time or turn grass into polished stone.
half3 EnvironmentTurfWeather(half3 color)
{
    #if defined(MAJESTIC_WEATHER_ON) // MAJESTIC_WEATHER_HOOK
    if(_MajWeatherOn>.5h)return MajesticWeatherTurf(color);
    #endif
    half wet=_EnvironmentWetness*_EnvironmentWeatherEnabled;
    half luminance=dot(color,half3(.2126h,.7152h,.0722h));
    return lerp(color,luminance.xxx,wet*(.30h+.12h*_EnvironmentStorm));
}
#endif
