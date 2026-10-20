import Foundation
import SceneKit
import MetalKit
import simd

@MainActor extension MatchHeroSurfaces {
    private static var garmentTextures: [String: MTLTexture] = [:]
    private static func compressed(_ name: String) -> MTLTexture? {
        if let cached = garmentTextures[name] { return cached }
        guard let url = MatchHeroData.locate(name, "ktx"), let device = MTLCreateSystemDefaultDevice() else { return nil }
        do {
            let texture = try MTKTextureLoader(device: device).newTexture(URL: url, options: [.SRGB: false, .textureUsage: MTLTextureUsage.shaderRead.rawValue])
            garmentTextures[name] = texture
            return texture
        } catch { print("GARMENT_TEXTURE_ERROR \(name): \(error)"); return nil }
    }
    static func garment(_ look: MatchHeroData.Look, tint: SIMD3<Float>, trim: SIMD3<Float>?) -> SCNMaterial {
        let m = SCNMaterial(); m.lightingModel = .blinn
        m.diffuse.contents = flatColour(tint)
        guard let n = compressed(look.normalMap ?? ""), let mask = compressed(look.maskMap ?? ""), let atlas = compressed(look.weaveMap) else { fatalError("Incomplete garment maps") }
        for (key, tex) in [("garmentN", n), ("garmentM", mask), ("fabricAtlas", atlas)] {
            let prop = SCNMaterialProperty(contents: tex); prop.wrapS = .clamp; prop.wrapT = .clamp
            prop.mipFilter = .linear; prop.minificationFilter = .linear; prop.magnificationFilter = .linear; prop.maxAnisotropy = 4
            m.setValue(prop, forKey: key)
        }
        let fallback = look.trimColor ?? [0.035, 0.035, 0.0401]
        let c = trim ?? SIMD3(fallback[0], fallback[1], fallback[2])
        m.setValue(SCNVector4(srgbToLinear(tint.x), srgbToLinear(tint.y), srgbToLinear(tint.z), 1), forKey: "clothTint")
        m.setValue(SCNVector4(srgbToLinear(c.x), srgbToLinear(c.y), srgbToLinear(c.z), 1), forKey: "trimTint")
        m.setValue(SCNVector4(look.weaveTile, look.weaveAngle * .pi / 180, look.weaveNormal, look.weaveThread), forKey: "weaveParams")
        m.setValue(SCNVector4(look.normalStrength ?? 1, 0, 0, 0), forKey: "normalParams")
        m.setValue(SCNVector4(look.wrap, look.smoothness, look.sheenStrength, look.sheenPower), forKey: "clothLook")
        m.setValue(SCNVector4(look.rimStrength, look.rimPower, 0, 0), forKey: "rimParams")
        m.setValue(SCNVector4(rimLight.x, rimLight.y, rimLight.z, 0), forKey: "rimLight")
        m.setValue(SCNVector4(look.exposure * 1.0, look.knee, 0, 0), forKey: "shoulder")
        m.shaderModifiers = [.surface: garmentSurface, .lightingModel: garmentLighting, .fragment: garmentShoulder]
        return m
    }
    static let garmentShoulder = clothShoulder + "\n_output.color.rgb *= mix(0.68, 1.0, _surface.metalness);\n"
    static let garmentSurface = """
    #pragma arguments
    texture2d<float> garmentN;
    texture2d<float> garmentM;
    texture2d<float> fabricAtlas;
    float4 clothTint;
    float4 trimTint;
    float4 weaveParams;
    float4 normalParams;
    float4 rimParams;
    float4 rimLight;
    #pragma body
    constexpr sampler maps(filter::linear, mip_filter::linear, address::clamp_to_edge, max_anisotropy(4));
    float2 uv = _surface.diffuseTexcoord;
    float4 mask = garmentM.sample(maps, uv);
    float id = floor(mask.a * 5.0 + 0.5);
    float3 nts = garmentN.sample(maps, uv).rgb * 2.0 - 1.0;
    nts.xy *= normalParams.x;
    float sn = sin(weaveParams.y), cs = cos(weaveParams.y);
    float2 wu = float2(cs*uv.x-sn*uv.y, sn*uv.x+cs*uv.y)*weaveParams.x;
    float2 quad = id==1.0 || id==5.0 ? float2(0.5,0.0) : id==2.0 ? float2(0.0,0.5) : id==3.0 || id==4.0 ? float2(0.5,0.5) : float2(0.0);
    float freq = id==1.0 || id==5.0 ? 12.0 : 8.0;
    float2 ax = dfdx(wu), ay = dfdy(wu);
    float fade = 1.0-smoothstep(0.32,0.72,max(length(ax),length(ay))*freq);
    if(id==3.0 || id==4.0)fade=0.0;
    float4 detail = fabricAtlas.sample(maps,quad+(0.03125+fract(wu)*0.9375)*0.5,gradient2d(ax*0.46875,ay*0.46875));
    float2 slope = (detail.rg*2.0-1.0)*weaveParams.z*fade;
    nts.xy += float2(cs*slope.x+sn*slope.y,-sn*slope.x+cs*slope.y);
    nts = normalize(nts);
    float3 n=normalize(_surface.normal), dp1=dfdx(_surface.position),dp2=dfdy(_surface.position);
    float2 duv1=dfdx(uv),duv2=dfdy(uv);
    float3 T=cross(dp2,n)*duv1.x+cross(n,dp1)*duv2.x;
    float3 B=cross(dp2,n)*duv1.y+cross(n,dp1)*duv2.y;
    float inv=rsqrt(max(max(dot(T,T),dot(B,B)),1e-20));
    n=normalize(T*inv*nts.x+B*inv*nts.y+n*nts.z);
    float thread=mix(1.0,detail.b*1.28,weaveParams.w*fade);
    float ao=max(mask.r,0.7), cavity=mix(0.4,1.0,mask.g);
    float3 albedo=mix(clothTint.rgb,trimTint.rgb,mask.b)*thread*cavity;
    _surface.normal=n;
    _surface.diffuse=float4(albedo*mix(1.0,ao,0.5),1.0);
    _surface.specular=float4(albedo,1.0);
    _surface.roughness=id/5.0;
    _surface.metalness=ao;
    float ndv=saturate(dot(n,normalize(_surface.view)));
    float fuzz=(id==0.0 || id==1.0)?pow(1.0-ndv,5.0)*0.018:0.0;
    float rim=pow(1.0-ndv,rimParams.y)*rimParams.x;
    _surface.emission=float4(rimLight.rgb*(rim*(0.35+0.65*albedo)+fuzz*albedo)*ao,0.0);
    """
    static let garmentLighting = """
    #pragma arguments
    float4 clothLook;
    #pragma body
    float id=floor(_surface.roughness*5.0+0.5);
    float smooth=id==0.0?0.10:id==1.0?0.13:id==2.0?0.16:id==3.0?0.04:id==4.0?0.08:0.10;
    float sheen=id==0.0?0.55:id==1.0?0.38:id==2.0?0.24:id==5.0?0.18:0.0;
    float3 n=normalize(_surface.normal),v=normalize(_surface.view),l=_light.direction,h=normalize(l+v);
    float nl=dot(n,l), nv=saturate(dot(n,v)),nh=saturate(dot(n,h));
    float wrapped=saturate((nl+clothLook.x)/(1.0+clothLook.x));
    float invR=1.0/max(0.25,1.0-smooth);
    float D=(2.0+invR)*pow(max(1.0-nh*nh,1e-5),0.5*invR)/(6.2831853);
    float V=1.0/max(4.0*(saturate(nl)+nv-saturate(nl)*nv),0.08);
    float spec=pow(nh,smooth*28.0+2.0)*smooth*0.22*saturate(nl);
    _lightingContribution.diffuse+=_light.intensity.rgb*wrapped;
    _lightingContribution.specular+=_light.intensity.rgb*(float3(spec)+_surface.specular.rgb*D*V*sheen*saturate(nl))*mix(1.0,_surface.metalness,0.5);
    """
}
