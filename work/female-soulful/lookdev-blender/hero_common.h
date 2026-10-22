// Shared lookdev lighting: a port of the shipping-game hero path
// (VISUAL_HERO_LIGHTING off: _HeroLightingEnabled 0, presentation fill .12,
// _HeroFilmResponse 1 -> no highlight roll). All maths in Unity axes.
// Blender (x,y,z) -> Unity (-x, z, -y), the FBX mirror.
vector toU(vector b) { return vector(-b[0], b[2], -b[1]); }
float luma(color c) { return dot(vector(c), vector(.2126,.7152,.0722)); }
float sat01(float x) { return clamp(x,0.0,1.0); }
color satc(color c) { return color(sat01(c[0]),sat01(c[1]),sat01(c[2])); }
float smoothstepf(float a, float b, float x) { float t=sat01((x-a)/(b-a)); return t*t*(3-2*t); }
vector snorm(vector v) { float l=length(v); return l>1e-6 ? v/l : vector(0,0,1); }

// Studio rig from HeroTurnaround.Studio (directional, Unity "from" vectors) in linear colour.
vector LKey()  { return snorm(vector(-0.452,0.616,0.645)); }
vector LFill() { return snorm(vector(0.801,0.208,0.561)); }
vector LBack() { return snorm(vector(-0.224,0.5,-0.837)); }
color CKey()  { return color(1.0,0.931,0.855)*1.15; }
color CFill() { return color(0.831,0.913,1.0)*0.45; }
color CBack() { return color(1.0,0.955,0.888)*0.35; }
// HeroPresentationLight, non-enabled branch.
vector LPres(vector v) {
    vector right = snorm(cross(vector(0,1,0), v));
    return snorm(v*0.80 + vector(0,0.60,0) - right*0.30);
}
color CPres() { return color(1.0,0.95,0.88)*0.12; }
// Trilight SH approximation (sky .50/.52/.56, equator .40/.40/.41, ground .26/.25/.24 sRGB).
color Ambient(vector n) {
    color sky=color(0.214,0.235,0.274), eq=color(0.133,0.133,0.141), gr=color(0.055,0.051,0.047);
    float up=max(n[1],0.0), dn=max(-n[1],0.0);
    return eq + (sky-eq)*1.6*(0.25+0.55*up) + (gr-eq)*1.6*(0.25+0.55*dn) - (sky-eq)*0.4 - (gr-eq)*0.4;
}
