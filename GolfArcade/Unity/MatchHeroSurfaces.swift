import Foundation
import SceneKit
import simd
import CoreGraphics
import ImageIO
import MetalKit
#if canImport(UIKit)
import UIKit
typealias HeroColor = UIColor
#else
import AppKit
typealias HeroColor = NSColor
#endif

/// LOCKER_MIRROR: what the match heroes' surfaces look like in the Swift locker mirror. SceneKit cannot run Unity's shaders, so this matches their RESULT from the numbers Unity's runtime
/// materials carry (MatchHeroLockerExport writes them into the manifest as each submesh's `look`):
///
///  * kit (Kit_Shirt, Kit_ShirtTrim, Kit_Shorts, Kit_ShortsBand, Kit_Sock, Kit_Shoe, Kit_Sole) and the racket grip = Unity's TennisCloth. The kit's own UV carries the seam / collar / hem map (multiplied into the colour);
///    a small tiling weave map adds a normal (the weave breaks the light) and a thread break (multiplied into the colour); tiled per UV unit exactly as TennisCloth does (`weaveTile`, turned by `weaveAngle`).
///    The lighting is TennisCloth's: wrapped diffuse, a faint BROAD gloss (never a dot), a soft grazing sheen that grows toward the silhouette and only where a light reaches, a weak rim, and an
///    exposure + soft shoulder so a lit white keeps its fold shading instead of clipping to one flat white.
///  * skin = TennisCharacter at smoothness 0.2 with a weak soft normal projected triplanar from the BIND pose (the body has no UVs): it rides on the skin while the body moves.
///  * eyes, the painted face decals, the racket frame and strings = TennisCharacter: flat colour, their own smoothness (eyes .85, frame .65, strings .15), no weave and no skin normal.
@MainActor enum MatchHeroSurfaces {
    // MARK: maps
    private static var imageCache: [String: CGImage] = [:]

    /// A shipped map (MatchHero_<name>.png) as a CGImage tagged for what it holds: colour maps are sRGB (SceneKit linearises them when it samples), data maps (the weave's normal and thread break, the
    /// soft skin normal) are tagged LINEAR so the sampler returns the raw numbers. `maxPixels` > 0 shrinks a bigger map (the seam maps are smooth multipliers: 1024 px is plenty on a phone).
    static func image(_ name: String, linear: Bool, maxPixels: Int = 0) -> CGImage? {
        let key = "\(name)|\(linear)|\(maxPixels)"
        if let c = imageCache[key] { return c }
        guard let url = MatchHeroData.locate(name, "png"), let src = CGImageSourceCreateWithURL(url as CFURL, nil) else { return nil }
        let decoded: CGImage?
        if maxPixels > 0, let w = (CGImageSourceCopyPropertiesAtIndex(src, 0, nil) as? [CFString: Any])?[kCGImagePropertyPixelWidth] as? Int, w > maxPixels {
            decoded = CGImageSourceCreateThumbnailAtIndex(src, 0, [kCGImageSourceCreateThumbnailFromImageAlways: true, kCGImageSourceThumbnailMaxPixelSize: maxPixels,
                                                                   kCGImageSourceShouldCacheImmediately: true] as CFDictionary)
        } else { decoded = CGImageSourceCreateImageAtIndex(src, 0, nil) }
        guard let cg = decoded else { return nil }
        // redraw into plain RGBA8 in the file's own colour space (the bytes stay what the PNG holds), then tag
        let w = cg.width, h = cg.height
        let own = cg.colorSpace ?? CGColorSpace(name: CGColorSpace.sRGB)!
        guard let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w * 4, space: own, bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue) else { return nil }
        // Unity's v = 0 is the BOTTOM row of a texture, Metal's the TOP: the rows are stored upside down so that every (u, v) of the export (the kit's UVs, the weave tiling) reads the texel Unity reads
        ctx.translateBy(x: 0, y: CGFloat(h)); ctx.scaleBy(x: 1, y: -1)
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
        guard let raw = ctx.data else { return nil }
        let bytes = Data(bytes: raw, count: w * h * 4)
        let tag = CGColorSpace(name: linear ? CGColorSpace.linearSRGB : CGColorSpace.sRGB)!
        guard let provider = CGDataProvider(data: bytes as CFData),
              let tagged = CGImage(width: w, height: h, bitsPerComponent: 8, bitsPerPixel: 32, bytesPerRow: w * 4, space: tag, bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.noneSkipLast.rawValue),
                                   provider: provider, decode: nil, shouldInterpolate: true, intent: .defaultIntent) else { return nil }
        imageCache[key] = tagged
        return tagged
    }

    static func srgbToLinear(_ c: Float) -> Float { c <= 0.04045 ? c / 12.92 : pow((c + 0.055) / 1.055, 2.4) }
    static func linearToSRGB(_ c: Float) -> Float { c <= 0.0031308 ? c * 12.92 : 1.055 * pow(c, 1 / 2.4) - 0.055 }
    /// A flat sRGB colour for a SceneKit material (UIColor / NSColor, which SceneKit linearises itself).
    static func flatColour(_ c: SIMD3<Float>) -> HeroColor { HeroColor(red: CGFloat(c.x), green: CGFloat(c.y), blue: CGFloat(c.z), alpha: 1) }

    // MARK: the registry (what each material was made from: tests and the proof sheets read it)
    @MainActor final class Made { let look: MatchHeroData.Look?; let role: String; let colour: SIMD3<Float>; init(_ look: MatchHeroData.Look?, _ role: String, _ colour: SIMD3<Float>) { self.look = look; self.role = role; self.colour = colour } }
    private static let registry = NSMapTable<SCNMaterial, Made>(keyOptions: .weakMemory, valueOptions: .strongMemory)
    /// The look numbers and colour a hero material was built from.
    static func made(_ material: SCNMaterial) -> Made? { registry.object(forKey: material) }

    // MARK: materials
    /// SceneKit Blinn parameters for a Unity smoothness (the same mapping the locker has always used: soft plastic, no specular blobs).
    static func blinn(_ smoothness: Float) -> (specular: CGFloat, shininess: CGFloat) { (CGFloat(0.03 + 0.18 * smoothness * smoothness), CGFloat(0.12 + 0.3 * smoothness)) }

    /// One submesh's material. `colour` (sRGB) is the locker's pick for it (skin tone, racket colour, a kit role's tint), nil = the authored colour of the look.
    /// `sceneScale` is the hero's scale on the stage (a metre of the export is that many scene units): the weave's nominal tile is `tileMetres * sceneScale` scene units.
    /// `part` (when known) says which extra texcoord channels its geometry carries: the body's lid-liner distances, the kit's edge measurements.
    static func material(_ sub: MatchHeroData.Sub, colour: SIMD3<Float>?, sceneScale: Float = 1, trimColour: SIMD3<Float>? = nil, part: MatchHeroData.Part? = nil) -> SCNMaterial {
        let mat: SCNMaterial
        let tint: SIMD3<Float>
        if let look = sub.look {
            tint = colour ?? SIMD3(look.color[0], look.color[1], look.color[2])
            if look.shader == "Universal Render Pipeline/Lit" {
                mat=SCNMaterial();mat.lightingModel = .physicallyBased;mat.diffuse.contents=flatColour(tint)
                mat.metalness.contents=look.metallic ?? 0;mat.roughness.contents=1-look.smoothness
            } else {
                mat = look.isCloth ? cloth(look, tint: tint, sceneScale: sceneScale, trim: trimColour, edges: part?.hasEdges == true) : character(look, tint: tint, lid: part?.hasLid == true)
            }
        } else {
            tint = colour ?? SIMD3(repeating: 1)
            mat = SCNMaterial(); mat.lightingModel = .blinn; mat.diffuse.contents = flatColour(tint)
        }
        if sub.look?.anatomicalFace != true { configurePaint(mat, role: sub.material, crafted: sub.look?.craftedPaint ?? 0) }
        if let part, part.kind == "body", part.hasEdges, let look = sub.look, !look.isCloth { addKitContact(mat, part: part, look: look) }
        if ProcessInfo.processInfo.environment["VISUAL_CHARACTER_SKIN_POLISH"] == "1", let look=sub.look, look.anatomicalFace == true,
           sub.material.contains("Iris") || sub.material.contains("Sclera") {
            let spec:Float=sub.material.contains("Iris") ? 0.85:0.52
            mat.setValue(SCNVector4(look.wrap,look.smoothness,spec,look.saturation),forKey:"athleteSurface")
        }
        if let look=sub.look, (look.femaleSurface ?? 0)>0.5,
           ["Iris","Sclera","Pupil","Limbal"].contains(where:{sub.material.contains($0)}) {
            // TennisCharacter female eye depth: role 1 sclera, 2 iris, 3 pupil/limbal
            // (shaded by the lid only). The frame comes from configureFace.
            let role:Float=sub.material.contains("Sclera") ? 1:sub.material.contains("Iris") ? 2:3
            mat.setValue(role,forKey:"femaleEyeRole")
            mat.setValue((look.femaleSurface ?? 0)>2.5 ? Float(1):Float(0),forKey:"maleEye")   // MaleFaceFinish: _FemaleSurface 3 = the male tuning
            var modifiers=mat.shaderModifiers ?? [:]
            if modifiers[.geometry]==nil && modifiers[.surface]==nil {
                modifiers[.geometry]=femaleEyeGeometry
                modifiers[.surface]=femaleEyeSurface
                if role<2.5 { modifiers[.lightingModel]=femaleEyeLighting }
            } else if role<2.5 {
                modifiers[.lightingModel]=femaleEyeLighting
                modifiers[.surface]=(modifiers[.surface] ?? "#pragma body\n")+"\n_surface.ambient.rgb+=_surface.diffuse.rgb*(-0.35);\n"
            }
            mat.shaderModifiers=modifiers
        }
        if let look=sub.look, (look.femaleSurface ?? 0)>0.5, look.isCloth {
            mat.setValue(sub.material.contains("Sole") ? Float(3):sub.material.contains("Shoe") ? Float(2):Float(0),forKey:"femaleClothKind")
        }
        mat.name = sub.material   // the Unity material name (Skin, White_Frame, Kit_Shirt ...): the role a tint is applied to
        mat.isDoubleSided = true   // a mirrored (left-handed) hero flips the winding
        registry.setObject(Made(sub.look, sub.material, tint), forKey: mat)
        return mat
    }

    // ---- TennisCharacter: skin, eyes, face decals, racket frame and strings
    private static func character(_ look: MatchHeroData.Look, tint: SIMD3<Float>, lid: Bool = false) -> SCNMaterial {
        let m = SCNMaterial(); m.lightingModel = .blinn
        let lum=simd_dot(tint,SIMD3<Float>(0.2126,0.7152,0.0722))
        m.diffuse.contents = flatColour(SIMD3<Float>(repeating:lum)+(tint-SIMD3<Float>(repeating:lum))*look.saturation)
        // Exported relative LUTs multiply the selected tint; never bake a skin preset.
        m.setValue(SCNVector4(srgbToLinear(tint.x),srgbToLinear(tint.y),srgbToLinear(tint.z),1),forKey:"heroTint")
        let hasRelativeMap = !look.baseMap.isEmpty && image(look.baseMap,linear:look.baseMapLinear ?? false) != nil
        if hasRelativeMap, let map=image(look.baseMap,linear:look.baseMapLinear ?? false) {
            m.diffuse.contents=map; m.diffuse.wrapS = .clamp; m.diffuse.wrapT = .clamp
            // Tint the sampled albedo before lighting. SCNMaterial.multiply
            // acts after lighting and would tint specular / skin twice.
        }
        m.setValue(look.skinFinish ?? 0,forKey:"skinFinish")
        m.setValue(look.maleFormPass ?? 0,forKey:"maleFormPass")
        m.setValue(ProcessInfo.processInfo.environment["VISUAL_CHARACTER_SKIN_POLISH"] == "1" ? Float(1):Float(0),forKey:"skinPolish")
        m.setValue(look.skinPigmentUV ?? 0,forKey:"skinPigmentUV")
        m.setValue((look.skinPigmentUV ?? 0)>0.5 ? Float(1):Float(0),forKey:"skinBindChannel")
        // Same broad skin / varnished eye-frame lobes as HeroCharacterShade, replacing
        // SceneKit's undifferentiated plastic Blinn response. Old manifests remain valid.
        m.setValue(SCNVector4(look.wrap, look.smoothness, look.specularStrength ?? 1, look.saturation), forKey: "athleteSurface")
        let warm = look.subsurface.count >= 3 ? SIMD3(look.subsurface[0], look.subsurface[1], look.subsurface[2]) : SIMD3<Float>(repeating: 0)
        m.setValue(SCNVector4(srgbToLinear(warm.x), srgbToLinear(warm.y), srgbToLinear(warm.z), 0), forKey: "athleteWarmth")
        m.setValue(SCNVector4(look.rimStrength, look.rimPower, look.environmentStrength ?? 0.12, 0), forKey: "athleteRim")
        m.specular.contents = HeroColor(white: 1, alpha: 1)
        m.shaderModifiers = hasRelativeMap ? [.surface:relativeCharacterSurface,.lightingModel:athleteLighting] : [.lightingModel:athleteLighting]
        let regional=(look.headOrigin?.count ?? 0)>=4 && (look.headOrigin?[3] ?? 0)>0.5
        func vector(_ values:[Float]?,flipZ:Bool)->SCNVector4{guard let a=values,a.count>=3 else{return SCNVector4(0,0,0,0)};return SCNVector4(a[0],a[1],flipZ ? -a[2]:a[2],a.count>3 ? a[3]:0)}
        m.setValue(vector(look.headOrigin,flipZ:true),forKey:"headOrigin")
        if regional {
            m.setValue(vector(look.headRight,flipZ:true),forKey:"headRight");m.setValue(vector(look.headUp,flipZ:true),forKey:"headUp");m.setValue(vector(look.headForward,flipZ:true),forKey:"headForward");m.setValue(vector(look.headEye,flipZ:false),forKey:"headEye")
            m.shaderModifiers=[.geometry:skinGeometry,.surface:hasRelativeMap ? headSurface.replacingOccurrences(of:"#pragma body",with:"#pragma body\n"+relativeTintBody):headSurface,.lightingModel:athleteLighting]
        }
        let face = regional && look.faceSkin == true && (look.skinFinish ?? 0) > 0.5
        if face {
            // MatchHeroLook.SkinSaturationFor: the picked tone's own saturation (light / mid tones .74, deep .88), as Unity sets it on every skin change
            m.setValue(SCNVector4(look.wrap, look.smoothness, look.specularStrength ?? 1, skinSaturation(for: tint)), forKey: "athleteSurface")
        }
        guard look.bumpTriplanar > 0.5, !look.bumpMap.isEmpty, let map = image(look.bumpMap, linear: true) else {
            if face { m.shaderModifiers = [.geometry: faceSkinGeometry(lid: lid, bindChannel: (look.skinPigmentUV ?? 0) > 0.5), .surface: "#pragma arguments\n" + headSurfaceArguments + "\n" + faceSkinDeclarations + "#pragma body\n" + faceSkinBody(lid: lid), .lightingModel: faceSkinLighting, .fragment: faceSkinFinish] }
            return m
        }
        let prop = SCNMaterialProperty(contents: map)
        prop.wrapS = .repeat; prop.wrapT = .repeat; prop.mipFilter = .linear; prop.minificationFilter = .linear; prop.magnificationFilter = .linear
        m.setValue(prop, forKey: "skinBumpMap")
        m.setValue(SCNVector4(look.bumpScale, look.bumpTile, 0, 0), forKey: "skinBump")
        m.shaderModifiers = [.geometry: skinGeometry, .surface: regional ? skinSurface.replacingOccurrences(of:"#pragma body",with:headSurfaceArguments+"\n#pragma body"+(hasRelativeMap ? "\n"+relativeTintBody:""))+headSurfaceBody:skinSurface, .lightingModel: athleteLighting]
        if face {
            // Unity's HeroFaceSkin (the in-game head): the same registered face, its analytic lips / lid liner / blush / beard and its face light.
            m.shaderModifiers = [.geometry: faceSkinGeometry(lid: lid, bindChannel: (look.skinPigmentUV ?? 0) > 0.5),
                                 .surface: skinSurface.replacingOccurrences(of: "#pragma body", with: headSurfaceArguments + "\n" + faceSkinDeclarations + "#pragma body") + faceSkinBody(lid: lid),
                                 .lightingModel: faceSkinLighting, .fragment: faceSkinFinish]
        }
        return m
    }

    /// CLOTHING V2: the garments' soft contact shadow on the skin (MatchHeroLook.ApplyKitV2Cover, mesh UV3.x, exported in the body's edge channel),
    /// applied like Unity's skin shaders (`colour *= 1 - _KitContact * contact`). The channel comes after UV0 (if any), the bind pose (2) and the lid liner (if any).
    static let kitContactShadow: Float = 0.55
    static func addKitContact(_ m: SCNMaterial, part: MatchHeroData.Part, look: MatchHeroData.Look) {
        guard var geometry = m.shaderModifiers?[.geometry] else { return }
        let channel = (part.uvOffset ?? -1 >= 0 ? 1 : 0) + 2 + (part.hasLid ? 1 : 0)
        geometry = geometry.replacingOccurrences(of: "float3 bindPos;", with: "float3 bindPos;\nfloat kitContact;") + "\nout.kitContact = _geometry.texcoords[\(channel)].x * \(kitContactShadow);\n"
        var mods = m.shaderModifiers ?? [:]
        mods[.geometry] = geometry
        let shade = "\n_output.color.rgb *= 1.0 - in.kitContact;\n"
        if let fragment = mods[.fragment] { mods[.fragment] = fragment + shade } else { mods[.fragment] = "#pragma body\n" + shade }
        m.shaderModifiers = mods
    }

    static let relativeTintBody = "_surface.diffuse.rgb*=heroTint.rgb;\n"
    static let relativeCharacterSurface = """
    #pragma arguments
    float4 heroTint;
    #pragma body
    _surface.diffuse.rgb*=heroTint.rgb;
    float relativeLuminance=dot(_surface.diffuse.rgb,float3(0.2126,0.7152,0.0722));
    _surface.diffuse.rgb=mix(float3(relativeLuminance),_surface.diffuse.rgb,athleteSurface.w);
    """

    static let athleteLighting = """
    #pragma arguments
    float4 athleteSurface;
    float4 athleteWarmth;
    float4 athleteRim;
    float4 headOrigin;
    float skinFinish;
    float skinPolish;
    #pragma body
    float3 n = normalize(_surface.normal), v = normalize(_surface.view), l = normalize(_light.direction);
    float nl = dot(n,l), wrapped = saturate((nl + athleteSurface.x) / (1.0 + athleteSurface.x));
    float edge = saturate(wrapped - saturate(nl)) * 1.35;
    float3 h = normalize(l+v); float nh = saturate(dot(n,h));
    float smoothness=headOrigin.w>0.5 ? _surface.shininess:athleteSurface.y;
    float broad = pow(nh,10.0+smoothness*30.0)*0.045;
    float varnish = pow(nh,24.0+smoothness*smoothness*200.0)*smoothness*0.25;
    float fresnel = 1.0+pow(1.0-saturate(dot(v,h)),5.0)*1.5;
    float spec = (broad+varnish)*athleteSurface.z*fresnel*saturate(nl*3.0);
    float rim = pow(1.0-saturate(dot(n,v)),athleteRim.y)*athleteRim.x;
    if(skinFinish>0.5){
        wrapped=saturate((nl+0.28)/1.28);
        edge=saturate(wrapped-saturate(nl));
        float skinLobe=pow(nh,18.0+smoothness*18.0)*0.075;
        if(skinPolish>0.5) {
            // Same soft shoulder / satin core as Unity's HeroSkinShade.
            float glossWeight=0.16+0.84*saturate((smoothness-0.32)/0.06);
            skinLobe=(pow(nh,5.0+smoothness*6.0)*0.035+pow(nh,18.0+smoothness*18.0)*0.40)*glossWeight;
        }
        spec=skinLobe*0.95*smoothstep(-0.06,0.24,nl);
        _lightingContribution.diffuse += _light.intensity.rgb*(float3(wrapped*0.84)+athleteWarmth.rgb*edge);
        _lightingContribution.specular += _light.intensity.rgb*(float3(spec)+rim*0.45*(float3(0.35)+0.65*_surface.diffuse.rgb));
    }else{
        _lightingContribution.diffuse += _light.intensity.rgb*(float3(wrapped)+athleteWarmth.rgb*edge);
        _lightingContribution.specular += _light.intensity.rgb*(float3(spec)+rim*(float3(0.35)+0.65*_surface.diffuse.rgb));
    }
    """

    /// Female eye material only. Geometry, authored pigment and catchlight stay intact.
    static let femaleEyeLighting = """
    #pragma arguments
    float4 athleteSurface;
    float femaleEyeRole;
    #pragma body
    float3 n=normalize(_surface.normal),v=normalize(_surface.view),l=normalize(_light.direction);
    float nl=saturate(dot(n,l));
    float wrapped=saturate((dot(n,l)+0.10)/1.10);
    float3 h=normalize(l+v);float nh=saturate(dot(n,h)),vh=saturate(dot(v,h));
    float cornea=pow(nh,femaleEyeRole>1.5 ?110.0:72.0)*0.32;
    float fresnel=1.0+pow(1.0-vh,5.0)*3.0;
    float occlusion=_surface.metalness>0.0 ? _surface.metalness:1.0;
    _lightingContribution.diffuse+=_light.intensity.rgb*wrapped*0.88*occlusion;
    _lightingContribution.specular+=_light.intensity.rgb*cornea*athleteSurface.z*fresnel*nl*occlusion;
    """
    /// The eye frame (bind pose) for the female eye layers: Unity's _FemaleEyeL/R/Right/Up.
    static let femaleEyeGeometry = """
    #pragma arguments
    float4 faceEyeL;
    float4 faceEyeR;
    float4 femaleEyeRight;
    float4 femaleEyeUp;
    #pragma varyings
    float2 femaleEyeUV;
    float femaleEyeSide;
    #pragma body
    float3 eyeP=_geometry.position.xyz, eyeMid=(faceEyeL.xyz+faceEyeR.xyz)*0.5;
    float4 eyeFrame=dot(eyeP-eyeMid,femaleEyeRight.xyz)<0.0 ? faceEyeL:faceEyeR;
    out.femaleEyeSide=dot(eyeP-eyeMid,femaleEyeRight.xyz)<0.0 ? 1.0:-1.0;
    float3 eyeD=eyeP-eyeFrame.xyz;
    out.femaleEyeUV=femaleEyeUp.w>0.5 ? float2(dot(eyeD,femaleEyeRight.xyz)/max(femaleEyeRight.w,0.0001),dot(eyeD,femaleEyeUp.xyz)/max(eyeFrame.w,0.0001)):float2(0.0);
    """
    /// Upper-lid shading on every eye layer, socket corners, lower-iris caustic; the
    /// sclera loses the energy that clipped it. The occlusion rides in metalness.
    static let femaleEyeSurface = """
    #pragma arguments
    float femaleEyeRole;
    float maleEye;
    #pragma body
    float2 eu=in.femaleEyeUV;
    float lidShade=smoothstep(-0.05,0.72,eu.y), lidContact=smoothstep(0.40,0.72,eu.y);
    float corner=smoothstep(0.50,1.0,abs(eu.x)), lowerLid=smoothstep(-0.62,-0.98,eu.y);
    float occ=mix(1.0,0.40,lidShade)*mix(1.0,0.55,lidContact);
    // 2026-10-17 (reference sheet 07): clean sclera with a soft shadow under the upper lid only, deeper iris, near-black pupil
    if(femaleEyeRole<1.5){_surface.diffuse.rgb*=float3(0.89,0.87,0.845);occ=mix(1.0,0.66,smoothstep(0.48,0.86,eu.y))*mix(1.0,0.78,smoothstep(0.62,0.82,eu.y))*mix(1.0,0.82,corner)*mix(1.0,0.90,lowerLid);}
    else if(femaleEyeRole<2.5){float caustic=smoothstep(0.22,-0.32,eu.y);_surface.diffuse.rgb*=maleEye>0.5 ? mix(float3(0.80,0.70,0.58),float3(1.12,0.92,0.66),caustic):mix(float3(0.52,0.47,0.42),float3(1.05,0.88,0.66),caustic);occ*=mix(1.0,0.86,lowerLid);}
    else{_surface.diffuse.rgb*=0.55;}
    if(maleEye>0.5){
        // = TennisCharacter male eye (MaleFaceFinish 2026-10-18, _MaleLash .50/.78/.30/.55): lash line on the eye, lower-lid rim, socket corners, caruncle
        float lash=smoothstep(0.50,0.78,eu.y), lowerRimE=smoothstep(0.30,0.55,-eu.y);
        if(femaleEyeRole<1.5){
            _surface.diffuse.rgb*=mix(float3(1.0),float3(0.80,0.78,0.76),smoothstep(0.35,1.0,abs(eu.x)));
            _surface.diffuse.rgb=mix(_surface.diffuse.rgb,float3(0.07,0.045,0.035),lash*0.92);
            _surface.diffuse.rgb*=mix(1.0,0.72,lowerRimE);
            _surface.diffuse.rgb*=mix(float3(1.0),float3(0.92,0.62,0.58),smoothstep(0.50,0.85,eu.x*in.femaleEyeSide));
        }else{_surface.diffuse.rgb=mix(_surface.diffuse.rgb,_surface.diffuse.rgb*0.35,lash*0.80);}
    }
    _surface.diffuse.rgb*=mix(femaleEyeRole<1.5 ? 0.88:0.70,1.0,occ);
    _surface.metalness=max(occ,0.001);
    _surface.ambient.rgb+=_surface.diffuse.rgb*((femaleEyeRole<1.5 ? 0.78:femaleEyeRole<2.5 ? 0.62:1.0)*mix(femaleEyeRole<1.5 ? 0.62:0.40,1.0,occ)-1.0);
    """

    private final class FacePerformanceState {
        let group: Float, lift: Float
        var blink: Float = 0, brow: Float = 0
        var gaze = SIMD2<Float>.zero
        init(group: Float, lift: Float) { self.group=group; self.lift=lift }
    }
    private static let faceStates = NSMapTable<SCNMaterial,FacePerformanceState>(keyOptions:.weakMemory,valueOptions:.strongMemory)

    private static func configurePaint(_ material: SCNMaterial, role: String, crafted: Float) {
        guard role.hasPrefix("Face_") else { return }
        material.setValue(SCNVector4(0,0,0,0),forKey:"headOrigin")
        var group: Float = 0, lift: Float = 0.00015
        if role.contains("EyelidRim") {group=9;lift=0.00005}
        else if role.contains("Closure") { group=5;lift=0.0002 }
        else if role.contains("Sclera") { group=1;lift=0.00008 }
        else if ["Iris","Pupil","Limbal","Catch"].contains(where: {role.contains($0)}) { group=2;lift=role.contains("Catch") ? 0.0002:role.contains("Pupil") ? 0.00014:0.00012 }
        else if (role.contains("LidLine") || role.contains("LidLower") || role.contains("LidCrease")) { group=3;lift=0.00012 }
        else if role.contains("Seam") {group=6;lift=0.00008}
        else if role.contains("LipUp") {group=7;lift=0}
        else if role.contains("BrowSoft") {group=8;lift=0.00008}
        else if role.contains("Brow") { group=4;lift=role.contains("BrowSoft") ? 0.00008:0.00018 }
        material.setValue(crafted,forKey:"craftedFacePaint")
        material.setValue(SCNVector4(group,lift,0,0),forKey:"facePaint")
        faceStates.setObject(FacePerformanceState(group:group,lift:lift),forKey:material)
        material.setValue(SCNVector4(0,0,0,0),forKey:"facePerformance")
        material.setValue(SCNVector4(0,1,0,0),forKey:"faceUp")
        material.setValue(SCNVector4(1,0,0,0),forKey:"faceRight")
        var modifiers=material.shaderModifiers ?? [:];modifiers[.geometry]=faceGeometry;modifiers[.surface]=faceSurface;modifiers[.lightingModel]=athleteLighting;material.shaderModifiers=modifiers
    }
    /// Eye centres measured from the actual exported sclera geometry, in that face's own space.
    static func configureFace(_ root: SCNNode) {
        guard let node=root.childNode(withName:"Face",recursively:true),let geometry=node.geometry,
              let vertices=geometry.sources(for:.vertex).first,let normals=geometry.sources(for:.normal).first else{return}
        func vertex(_ i:Int)->SIMD3<Float>{
            vertices.data.withUnsafeBytes { raw in
                let at=vertices.dataOffset+i*vertices.dataStride
                return SIMD3(raw.loadUnaligned(fromByteOffset:at,as:Float.self),raw.loadUnaligned(fromByteOffset:at+4,as:Float.self),raw.loadUnaligned(fromByteOffset:at+8,as:Float.self))
            }
        }
        var lo=[SIMD3<Float>(repeating:Float.greatestFiniteMagnitude),SIMD3<Float>(repeating:Float.greatestFiniteMagnitude)]
        var hi=lo.map {-$0};var found=[false,false];var eyeNormals=[SIMD3<Float>.zero,SIMD3<Float>.zero]
        for (sub,material) in geometry.materials.enumerated() where material.name?.contains("Sclera") == true {
            let element=geometry.elements[sub]
            element.data.withUnsafeBytes { raw in
                for k in 0..<(element.primitiveCount*3) {
                    let i=element.bytesPerIndex==4 ? Int(raw.loadUnaligned(fromByteOffset:k*4,as:UInt32.self)):Int(raw.loadUnaligned(fromByteOffset:k*2,as:UInt16.self))
                    let v=vertex(i),side=v.x<0 ? 0:1
                    normals.data.withUnsafeBytes { nraw in let at=normals.dataOffset+i*normals.dataStride;eyeNormals[side]+=SIMD3(nraw.loadUnaligned(fromByteOffset:at,as:Float.self),nraw.loadUnaligned(fromByteOffset:at+4,as:Float.self),nraw.loadUnaligned(fromByteOffset:at+8,as:Float.self)) }
                    lo[side]=simd_min(lo[side],v);hi[side]=simd_max(hi[side],v);found[side]=true
                }
            }
        }
        guard found.allSatisfy({$0}) else{return}
        let left=(lo[0]+hi[0])*0.5,right=(lo[1]+hi[1])*0.5
        // Female eye frame: right between the eyes, up toward the brows (FemaleGarmentFinish.EyeFrame).
        var browSum=SIMD3<Float>.zero, browCount:Float=0
        for (sub,material) in geometry.materials.enumerated() where material.name?.contains("Brow") == true {
            let element=geometry.elements[sub]
            element.data.withUnsafeBytes { raw in
                for k in 0..<(element.primitiveCount*3) {
                    let i=element.bytesPerIndex==4 ? Int(raw.loadUnaligned(fromByteOffset:k*4,as:UInt32.self)):Int(raw.loadUnaligned(fromByteOffset:k*2,as:UInt16.self))
                    browSum+=vertex(i);browCount+=1
                }
            }
        }
        let eyeRightAxis=simd_normalize(right-left)
        var eyeUpAxis=browCount>0 ? browSum/browCount-(left+right)*0.5 : SIMD3<Float>(0,1,0)
        eyeUpAxis=simd_normalize(eyeUpAxis-simd_dot(eyeUpAxis,eyeRightAxis)*eyeRightAxis)
        let eyeHalfWidth=((hi[0].x-lo[0].x)+(hi[1].x-lo[1].x))*0.25
        let nl=simd_normalize(eyeNormals[0]),nr=simd_normalize(eyeNormals[1])
        let skin=root.childNode(withName:"Body",recursively:true)?.geometry?.materials.first.flatMap { made($0)?.colour } ?? SIMD3<Float>(0.76,0.48,0.3)
        let skinLinear=SIMD3(srgbToLinear(skin.x),srgbToLinear(skin.y),srgbToLinear(skin.z))
        for material in geometry.materials {
            material.setValue(SCNVector4(left.x,left.y,left.z,(hi[0].y-lo[0].y)*0.5),forKey:"faceEyeL")
            material.setValue(SCNVector4(right.x,right.y,right.z,(hi[1].y-lo[1].y)*0.5),forKey:"faceEyeR")
            material.setValue(SCNVector4(nl.x,nl.y,nl.z,(hi[0].x-lo[0].x)*0.5),forKey:"faceNormalL")
            material.setValue(SCNVector4(nr.x,nr.y,nr.z,(hi[1].x-lo[1].x)*0.5),forKey:"faceNormalR")
            material.setValue(SCNVector4(skinLinear.x,skinLinear.y,skinLinear.z,1),forKey:"faceSkin")
            material.setValue(SCNVector4(eyeRightAxis.x,eyeRightAxis.y,eyeRightAxis.z,eyeHalfWidth),forKey:"femaleEyeRight")
            material.setValue(SCNVector4(eyeUpAxis.x,eyeUpAxis.y,eyeUpAxis.z,browCount>0 ? 1:0),forKey:"femaleEyeUp")
        }
    }
    static func performFace(on root: SCNNode, blink: Float, gaze: SIMD2<Float> = .zero, brow: Float = 0) {
        let b=max(0,min(1,blink))
        var anatomicalFace=false
        for partName in ["Body","Face"] {
            guard let node=root.childNode(withName:partName,recursively:true),let morpher=node.morpher,
                  let full=morpher.targets.firstIndex(where:{$0.name=="Hero_Blink"}) else { continue }
            let half=morpher.targets.firstIndex(where:{$0.name=="Hero_Blink_Half"})
            if let half { morpher.setWeight(CGFloat(max(0,1-abs(2*b-1))),forTargetAt:half) }
            morpher.setWeight(CGFloat(half == nil ? b:max(0,2*b-1)),forTargetAt:full)
            if partName == "Face" { anatomicalFace=true }
        }
        // OriginalSeam's source targets already close/recess the eyes. Unity
        // also bypasses gaze, brow lift and the legacy fragment closure stack.
        if anatomicalFace { return }
        guard let node=root.childNode(withName:"Face",recursively:true) else{return}
        for material in node.geometry?.materials ?? [] {
            guard let state=faceStates.object(forKey:material) else{continue}
            let nextBlink=max(0,min(1,blink)), nextBrow=max(-0.001,min(0.001,brow))
            // Unchanged uniforms were invalidating every face submesh on every frame.
            // Keep the same continuous blink, but update only its participating roles.
            let eyeRole=state.group>0.5 && state.group != 4 && state.group != 7
            let browRole=state.group == 4 || state.group == 8
            if (eyeRole && abs(state.blink-nextBlink)>0.000001) || (browRole && abs(state.brow-nextBrow)>0.000001) {
                state.blink=nextBlink; state.brow=nextBrow
                material.setValue(SCNVector4(state.group,state.lift,nextBlink,nextBrow),forKey:"facePaint")
            }
            // Gaze is submillimetre; this threshold is below a pixel on the stage.
            if state.group == 2 && simd_distance(state.gaze,gaze)>0.00008 {
                state.gaze=gaze
                material.setValue(SCNVector4(gaze.x,gaze.y,0,0),forKey:"facePerformance")
            }
        }
    }
    static func performFace(on root: SCNNode, at time: Double, happy: Bool = false) {
        let interval=3.4,phase=time.truncatingRemainder(dividingBy:interval)
        let blink=phase<0.16 ? Float(sin(phase/0.16*Double.pi)):0
        performFace(on:root,blink:max(blink,happy ? 0.16:0),gaze:SIMD2(Float(sin(time*0.47))*0.00125,0),brow:happy ? 0.00065:0)
    }
    static let faceGeometry = """
    #pragma arguments
    float4 faceEyeL;
    float4 faceEyeR;
    float4 faceUp;
    float4 faceRight;
    float4 facePaint;
    float4 facePerformance;
    float4 faceNormalL;
    float4 faceNormalR;
    #pragma varyings
    float4 eyeLidData;
    #pragma body
    float3 facePos=_geometry.position.xyz;
    out.eyeLidData=float4(0.0,facePaint.x,facePaint.z,0.0);
    if(facePaint.x>0.5){
        float4 eye=dot(facePos-(faceEyeL.xyz+faceEyeR.xyz)*0.5,faceRight.xyz)<0.0 ? faceEyeL:faceEyeR;
        if(facePaint.x<3.5 || facePaint.x>4.5){
            float4 closeNormal=dot(facePos-(faceEyeL.xyz+faceEyeR.xyz)*0.5,faceRight.xyz)<0.0 ? faceNormalL:faceNormalR;
            if(facePaint.x>1.5 && facePaint.x<2.5)facePos+=(faceRight.xyz*facePerformance.x+faceUp.xyz*facePerformance.y)*(1.0-facePaint.z);
            float height=dot(facePos-eye.xyz,faceUp.xyz);
            out.eyeLidData.x=height/max(eye.w,0.0001);
            out.eyeLidData.w=dot(facePos-eye.xyz,faceRight.xyz)/max(closeNormal.w,0.0001);
            if(facePaint.x>7.5 && facePaint.x<8.5)facePos+=faceUp.xyz*facePaint.w;
            if(facePaint.x>8.5){float crease=(-0.45+0.22*out.eyeLidData.w*out.eyeLidData.w)*eye.w;facePos+=faceUp.xyz*(crease-height)*facePaint.z*(1.0-_geometry.texcoords[0].x);}
        }else facePos+=faceUp.xyz*facePaint.w;
    }
    facePos+=_geometry.normal.xyz*facePaint.y;
    _geometry.position.xyz=facePos;
    """
    static let faceSurface = """
    #pragma arguments
    float4 faceSkin;
    float craftedFacePaint;
    #pragma body
    float role=in.eyeLidData.y,blink=in.eyeLidData.z;
    if(craftedFacePaint>0.5 && role>3.5 && role<4.5){float2 uv=_surface.diffuseTexcoord;float coverage=smoothstep(0.0,0.16,uv.y)*smoothstep(0.0,0.16,1.0-uv.y)*smoothstep(0.0,0.045,uv.x)*smoothstep(0.0,0.045,1.0-uv.x);_surface.diffuse.rgb=mix(faceSkin.rgb,_surface.diffuse.rgb,coverage);}
    if(role>8.5){if(blink>0.90)discard_fragment();_surface.diffuse.rgb=faceSkin.rgb;}
    else if(role>7.5){if(in.eyeLidData.x<1.3 && blink>0.2)discard_fragment();}
    else if(role>6.5){discard_fragment();}
    else if(role>5.5){discard_fragment();}
    else if(role>0.5 && (role<3.5 || role>4.5)){
        if(role>4.5 && blink>0.985)discard_fragment();
        float closed=-0.45+0.22*in.eyeLidData.w*in.eyeLidData.w;float progress=pow(blink,0.8);
        float upper=mix(1.0,closed,progress),lower=mix(-1.0,closed,progress);
        float lid=max(smoothstep(upper-0.025,upper+0.025,in.eyeLidData.x),1.0-smoothstep(lower-0.025,lower+0.025,in.eyeLidData.x));
        if(blink>0.995)lid=1.0;
        if(blink<0.001)lid=0.0;
        if(role<3.5){if(lid>0.5)discard_fragment();}
        else {
            if(lid<0.5)discard_fragment();
            _surface.diffuse.rgb=faceSkin.rgb;
            float creaseY=closed;
            float crease=(1.0-smoothstep(0.018,0.045,abs(in.eyeLidData.x-creaseY)))*(1.0-smoothstep(0.78,0.98,abs(in.eyeLidData.w)))*smoothstep(0.72,1.0,blink);
            _surface.diffuse.rgb*=1.0-crease*0.38;
        }
    }
    """

    // ---- TennisCloth: the kit and the racket grip
    private static func cloth(_ look: MatchHeroData.Look, tint: SIMD3<Float>, sceneScale: Float, trim: SIMD3<Float>?, edges: Bool = false) -> SCNMaterial {
        if (look.useGarmentMaps ?? 0) > 0.5, let m = garment(look, tint: tint, trim: trim, edges: edges) { return m }
        let m = SCNMaterial(); m.lightingModel = .blinn   // the per-light maths is replaced by the lighting modifier below
        // the kit's seam / collar / placket / hem map on its own UV (clamped); the grip has none (no UVs on the racket)
        if !look.baseMap.isEmpty, let seams = image(look.baseMap, linear: false, maxPixels: 1024) {
            m.diffuse.contents = seams
            m.diffuse.wrapS = .clamp; m.diffuse.wrapT = .clamp; m.diffuse.mipFilter = .linear; m.diffuse.minificationFilter = .linear; m.diffuse.magnificationFilter = .linear; m.diffuse.maxAnisotropy = 4
        } else { m.diffuse.contents = CGColor(gray: 1, alpha: 1) }
        let hasUV = !look.baseMap.isEmpty
        if hasUV {
            // the weave: a small tiling map, tiles per UV unit as TennisCloth sets them per piece (the racket has no UVs: its grip is the flat variant, with no map bound at all)
            let weave = look.weaveMap.isEmpty ? nil : image(look.weaveMap, linear: true)
            let prop = SCNMaterialProperty(contents: weave ?? CGColor(gray: 0.5, alpha: 1))
            prop.wrapS = .repeat; prop.wrapT = .repeat; prop.mipFilter = .linear; prop.minificationFilter = .linear; prop.magnificationFilter = .linear; prop.maxAnisotropy = 4
            m.setValue(prop, forKey: "weaveMap")
            let strength: Float = weave == nil ? 0 : 1
            // x tiles per UV unit, y grain angle (radians), z weave normal strength, w thread break strength
            m.setValue(SCNVector4(look.weaveTile, look.weaveAngle * .pi / 180, strength * look.weaveNormal, strength * look.weaveThread), forKey: "weaveParams")
            m.setValue(SCNVector4(weaveMipBias, weaveThreadPixelsOff, weaveThreadPixelsFull, (look.tileMetres ?? 0.026) * sceneScale), forKey: "weaveParams2")
        }
        m.setValue(SCNVector4(srgbToLinear(tint.x), srgbToLinear(tint.y), srgbToLinear(tint.z), 1), forKey: "clothTint")
        m.setValue(SCNVector4(look.rimStrength, look.rimPower, 0, 0), forKey: "rimParams")
        m.setValue(SCNVector4(rimLight.x, rimLight.y, rimLight.z, 0), forKey: "rimLight")
        m.setValue(SCNVector4(look.wrap, look.smoothness, look.sheenStrength, look.sheenPower), forKey: "clothLook")
        m.setValue(SCNVector4(look.exposure * sceneExposure, look.knee, 0, 0), forKey: "shoulder")
        if (look.femaleSurface ?? 0)>0.5 {
            var surface=hasUV ? clothSurface:clothSurfaceFlat
            surface += femaleClothAmbient
            m.shaderModifiers = [.surface:surface,.lightingModel:femaleFabricLighting(golf:false,garment:false),.fragment:clothShoulder]
        } else {
            m.shaderModifiers = [.surface: hasUV ? clothSurface : clothSurfaceFlat, .lightingModel: clothLighting, .fragment: clothShoulder]
        }
        return m
    }

    /// Calibration of the plain (no garment maps) cloth against Unity's TennisCloth under the same light rig (work/hero-sync sheets, 2026-10-12): 1, i.e. Unity's own
    /// exposure. The old 1.4 was tuned against a comparison whose Unity side had a fifth of the ambient and its lights mirrored, and drew the polos and skirt ~40 % too bright.
    static var sceneExposure: Float = 1.0
    /// The weave is 8 threads per tile (2.0 - 2.9 cm): on a phone the whole hero is ~0.6 px per mm, so a thread is about 1.5 px and can only alias. The weave is faded out by how many pixels a thread
    /// covers on screen, measured from the surface's world-space pixel footprint (not from the UVs, whose density differs from island to island): full strength from `weaveThreadPixelsFull` px per thread,
    /// gone at `weaveThreadPixelsOff`. A close-up (the locker's torso, a shoe) shows the threads; a whole body shows the seams, the trim, the sheen and the fold shading.
    static var weaveMipBias: Float = 0.6, weaveThreadPixelsOff: Float = 1.4, weaveThreadPixelsFull: Float = 3.0

    /// Colour (linear) of the main light the rim is added with (the locker's key light, warm).
    static let rimLight = SIMD3<Float>(1.0, 0.85, 0.66) * 1.05

    // MARK: shader modifiers (Metal)
    /// Skin: carry the bind-pose position (texcoord channels 0 = x, y and 1 = z) to the fragment stage.
    static let skinGeometry = """
    #pragma arguments
    float skinBindChannel;
    #pragma varyings
    float3 bindPos;
    #pragma body
    out.bindPos = skinBindChannel>0.5 ? float3(_geometry.texcoords[1].x, _geometry.texcoords[1].y, _geometry.texcoords[2].x) : float3(_geometry.texcoords[0].x, _geometry.texcoords[0].y, _geometry.texcoords[1].x);
    """
    static let headSurfaceArguments = """
    float4 headRight;
    float4 headUp;
    float4 headForward;
    float4 headEye;
    float4 heroTint;
    float skinPigmentUV;
    """
    static let headSurfaceBody = """
    float3 hd=in.bindPos-headOrigin.xyz;
    float3 hp=float3(dot(hd,headRight.xyz),dot(hd,headUp.xyz),dot(hd,headForward.xyz))-headEye.xyz;
    if(skinFinish>0.5&&skinFinish<1.5){float orbitM=smoothstep(-0.085,-0.022,hp.y)*(1.0-smoothstep(0.060,0.110,hp.y))*smoothstep(-0.075,-0.045,hp.z);hp.y+=0.010*(1.0-orbitM);}   // male 2026-10-17: = HeroFaceSkin (eyes no longer lowered 10 mm)
    float3 q=(hp-float3(-0.044,-0.052,-0.005))/float3(0.032,0.031,0.080);
    float cheeks=exp(-2.0*dot(q,q));q=(hp-float3(0.044,-0.052,-0.005))/float3(0.032,0.031,0.080);cheeks+=exp(-2.0*dot(q,q));
    q=(hp-float3(0.0,-0.040,0.018))/float3(0.022,0.038,0.070);float nose=exp(-2.0*dot(q,q));
    q=(hp-float3(0.0,0.062,-0.027))/float3(0.054,0.044,0.075);float forehead=exp(-2.0*dot(q,q));
    q=(hp-float3(-0.092,-0.025,-0.055))/float3(0.020,0.042,0.055);float ears=exp(-2.0*dot(q,q));q=(hp-float3(0.092,-0.025,-0.055))/float3(0.020,0.042,0.055);ears+=exp(-2.0*dot(q,q));
    float warmth=saturate(cheeks*0.85+nose*0.40+ears*0.7);
    if(skinFinish>0.5){
        if(skinPigmentUV>0.5){
            float2 masks=saturate((_surface.diffuseTexcoord*64.0-0.5)/63.0);
            float lipPigment=masks.x, linePigment=masks.y;
            float3 lip=skinFinish<1.5 ? float3(0.99,0.83,0.80):float3(0.99,0.76,0.74);
            float3 line=float3(0.80,0.67,0.64);
            if(skinPigmentUV>1.5){
                // Exact SkinPigmentUV2 relative palette and mouth-only seam gain.
                lip=skinFinish<1.5 ? float3(0.95,0.68,0.69):float3(0.94,0.61,0.64);
                line=float3(0.62,0.44,0.42);
                linePigment=saturate(linePigment*mix(1.0,1.65,saturate(lipPigment*4.0)));
            }
            _surface.diffuse.rgb=heroTint.rgb*mix(float3(1.0),lip,lipPigment)*mix(float3(1.0),line,linePigment);
        }
        _surface.diffuse.rgb*=mix(float3(1.0),float3(1.012,0.965,0.955),warmth);
        if(skinFinish<1.5){
            q=(hp-float3(0.0,-0.126,-0.010))/float3(0.086,0.048,0.095);float jaw=exp(-2.0*dot(q,q));
            q=(hp-float3(0.0,-0.077,0.016))/float3(0.048,0.016,0.060);float upperLip=exp(-2.0*dot(q,q));
            _surface.diffuse.rgb*=mix(float3(1.0),float3(0.88,0.91,0.94),saturate(jaw*0.42+upperLip*0.20));
        }
        _surface.shininess=mix(0.32,0.40,saturate(nose+forehead*0.55));
        float lum=dot(_surface.diffuse.rgb,float3(0.2126,0.7152,0.0722));
        _surface.diffuse.rgb=mix(float3(lum),_surface.diffuse.rgb,athleteSurface.w);
    }else{
        _surface.diffuse.rgb*=float3(1.0+0.025*warmth,1.0-0.060*warmth,1.0-0.025*warmth)*(1.0+0.012*forehead);
        _surface.shininess=saturate(athleteSurface.y+0.08*nose+0.06*forehead-0.025*cheeks);
    }
    """
    static var headSurface:String {"#pragma arguments\n"+headSurfaceArguments+"\n#pragma body\n"+headSurfaceBody}

    /// MatchHeroLook.SkinSaturationFor (sRGB tone): deep tones keep more richness (.88), light and mid tones get .74.
    static func skinSaturation(for tone: SIMD3<Float>) -> Float {
        let luminance = simd_dot(tone, SIMD3<Float>(0.2126, 0.7152, 0.0722))
        let t = min(max((luminance - 0.15) / 0.30, 0), 1), s = t * t * (3 - 2 * t)
        return 0.88 + (0.74 - 0.88) * s
    }

    /// The skin's geometry modifier with HeroFaceSkin's lid-liner distances as a varying (the channel after the bind pose: 3 after UV0, else 2).
    static func faceSkinGeometry(lid: Bool, bindChannel: Bool) -> String {
        guard lid else { return skinGeometry }
        return skinGeometry.replacingOccurrences(of: "float3 bindPos;", with: "float3 bindPos;\nfloat2 lidDistance;")
            + "\nout.lidDistance = _geometry.texcoords[\(bindChannel ? 3 : 2)];\n"
    }

    /// Port of HeroFaceSkin's registered face (`_SkinFinish` 1 male / 2 female, `_SkinPigmentUV` on): the same regions, pigments and order, in the same head frame.
    /// The lighting it needs per pixel goes to faceSkinLighting in fields the blinn model does not use: roughness = wrap, metalness = face amount, shininess = smoothness.
    /// Two-sided regions use |x| (the cross term of the mirrored Gaussian is below 1e-6 for every region here).
    static func faceSkinBody(lid: Bool) -> String { faceSkinBodyStart + (lid ? faceSkinLidLiner : "") + faceSkinBodyEnd }
    /// HeroFaceSkin's SkinRegion and its skin-grain value noise, as global functions of the surface modifier.
    static let faceSkinDeclarations = """
    #pragma declaration
    float SkinRegion(float3 p,float3 c,float3 r){float3 q=(p-c)/r;return exp(-2.0*dot(q,q));}
    float SkinHash(float3 p){p=fract(p*0.1031);p+=dot(p,p.zyx+31.32);return fract((p.x+p.y)*p.z);}
    float SkinNoise(float3 p){
        float3 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);
        return mix(mix(mix(SkinHash(i),SkinHash(i+float3(1,0,0)),f.x),mix(SkinHash(i+float3(0,1,0)),SkinHash(i+float3(1,1,0)),f.x),f.y),
                   mix(mix(SkinHash(i+float3(0,0,1)),SkinHash(i+float3(1,0,1)),f.x),mix(SkinHash(i+float3(0,1,1)),SkinHash(i+float3(1,1,1)),f.x),f.y),f.z);
    }

    """
    static let faceSkinBodyStart = """
    float3 hd=in.bindPos-headOrigin.xyz;
    float3 hp=float3(dot(hd,headRight.xyz),dot(hd,headUp.xyz),dot(hd,headForward.xyz))-headEye.xyz;
    if(skinFinish>0.5&&skinFinish<1.5){float orbitM=smoothstep(-0.085,-0.022,hp.y)*(1.0-smoothstep(0.060,0.110,hp.y))*smoothstep(-0.075,-0.045,hp.z);hp.y+=0.010*(1.0-orbitM);}   // male 2026-10-17: = HeroFaceSkin (eyes no longer lowered 10 mm)
    float3 hs=float3(abs(hp.x),hp.y,hp.z);
    bool maleFace=skinFinish<1.5;
    float faceAmount=smoothstep(-0.19,-0.12,hp.y)*(1.0-smoothstep(0.14,0.19,abs(hp.x)));
    float3 q=(hs-float3(0.044,-0.052,-0.005))/float3(0.032,0.031,0.080);float cheeks=exp(-2.0*dot(q,q));
    q=(hp-float3(0.0,-0.040,0.018))/float3(0.022,0.038,0.070);float nose=exp(-2.0*dot(q,q));
    q=(hp-float3(0.0,0.062,-0.027))/float3(0.054,0.044,0.075);float forehead=exp(-2.0*dot(q,q));
    q=maleFace ? (hs-float3(0.102,-0.015,-0.095))/float3(0.018,0.042,0.030) : (hs-float3(0.092,-0.025,-0.055))/float3(0.020,0.042,0.055);float ears=exp(-2.0*dot(q,q));
    float warmth=saturate(cheeks*0.85+nose*0.40+ears*0.7);
    float3 c=skinPigmentUV>0.5 ? heroTint.rgb : _surface.diffuse.rgb;
    c*=mix(float3(1.0),maleFace ? float3(1.0,0.99,0.97) : float3(1.0),faceAmount);
    float nx=hp.x/0.025, ny=(hp.y-(maleFace ? -0.047 : -0.045))/0.007;
    float noseUnderside=exp(-2.0*nx*nx-2.0*ny*ny)*smoothstep(0.015,0.026,hp.z);
    bool malePass=maleFace&&maleFormPass>0.5;   // = HeroFaceSkin _MaleFormPass (MaleFaceFinish 2026-10-18)
    if(malePass){float ux=hp.x/0.023, uy=(hp.y+0.0485)/0.0030;noseUnderside=exp(-2.0*ux*ux*ux*ux-2.0*uy*uy)*smoothstep(0.012,0.024,hp.z)*1.8;}
    if(maleFace){float cx=(abs(hp.x)-0.016)/0.005, cy=(hp.y+0.042)/0.0022;float cavity=exp(-2.0*cx*cx-2.0*cy*cy)*smoothstep(0.013,0.025,hp.z);c*=mix(float3(1.0),float3(0.58,0.44,0.38),cavity*(malePass ? 0.0:0.40));}
    if(malePass){
        // = HeroFaceSkin male pass: teardrop nostrils, lit alar rims, columella, tip highlight, a hint of the nasolabial fold
        float nnx=abs(hp.x)-0.0090; float nu=saturate(0.5+nnx/0.0110);
        float halfH=mix(0.0004,0.0019,pow(nu,0.7));
        float nny=hp.y+0.0497+0.0016*(1.0-nu)+0.16*nnx;
        float nd=pow(nnx/0.0055,2.0)+pow(nny/max(halfH,0.0003),2.0);
        float nostril=(1.0-smoothstep(0.35,1.0,nd))*smoothstep(0.018,0.030,hp.z)*mix(0.75,1.0,nu);
        float nrim=(smoothstep(2.6,4.5,nd)*(1.0-smoothstep(5.0,9.0,nd)))*smoothstep(0.018,0.030,hp.z)*smoothstep(-0.0515,-0.0498,hp.y);
        c*=mix(float3(1.0),float3(1.08,1.04,1.02),nrim*0.6);
        float cx2=hp.x/0.0030, cy2=(hp.y+0.0480)/0.0025;float columella=exp(-2.0*cx2*cx2-2.0*cy2*cy2)*smoothstep(0.020,0.032,hp.z);
        float tx=hp.x/0.0065, ty=(hp.y+0.0405)/0.0055;float tipLight=exp(-2.0*tx*tx-2.0*ty*ty)*smoothstep(0.030,0.045,hp.z);
        c*=mix(float3(1.0),float3(1.07,1.05,1.04),tipLight);
        c*=mix(float3(1.0),float3(1.06,1.04,1.03),columella*0.6);
        float2 fa=float2(0.019,-0.050), fb=float2(0.031,-0.071), fq=float2(abs(hp.x),hp.y)-fa;
        float ft=saturate(dot(fq,fb-fa)/dot(fb-fa,fb-fa)); float fd=length(fq-ft*(fb-fa))/0.0026; float fold=exp(-fd*fd)*(1.0-ft*0.6)*smoothstep(0.0,0.02,hp.z);
        c*=mix(float3(1.0),float3(0.80,0.70,0.64),fold*0.75*0.3);
        c=mix(c,c*float3(0.20,0.12,0.09),nostril*0.85);
        c*=mix(float3(1.0),float3(0.80,0.70,0.66),(1.0-smoothstep(1.0,3.0,nd))*(1.0-nostril)*smoothstep(0.018,0.030,hp.z)*0.5);
    }
    float mouthWidth=maleFace ? 0.035 : 0.0265;
    float mx=abs(hp.x)/mouthWidth;
    float seam=(maleFace ? -0.0683 : -0.0701)+(maleFace ? -0.0010 : 0.0015)*mx*mx;   // male 2026-10-17 (= HeroFaceSkin): corners a touch down
    float fullness=saturate(1.0-mx*mx);
    float cu=(abs(hp.x)-0.008)/0.005;
    float cupid=0.0015*exp(-cu*cu)*fullness;
    float upperLipLine=seam+0.0055*fullness+cupid, lowerLipLine=seam-0.0075*fullness;
    if(maleFace){
        // Male lips 2026-10-17 (= HeroFaceSkin): thin bowed upper lip over a fuller lower lip, in mouth half-widths.
        float mb=(mx-0.25)/0.13, mc=mx/0.09;
        upperLipLine=seam+mouthWidth*(0.17*pow(saturate(1.0-pow(mx,2.4)),1.3)+0.040*exp(-mb*mb)-0.025*exp(-mc*mc));
        lowerLipLine=seam-mouthWidth*0.30*pow(saturate(1.0-pow(mx,2.6)),1.6);
    }
    if(!maleFace){
        // Female jaw/lips pass 2026-10-17 (= HeroFaceSkin): reference sheet 07 lip outline in mouth half-widths.
        float cb=(mx-0.28)/0.12, cc=mx/0.1;
        upperLipLine=seam+mouthWidth*(0.33*pow(saturate(1.0-pow(mx,2.8)),1.5)+0.025*exp(-cb*cb)-0.02*exp(-cc*cc));
        lowerLipLine=seam-mouthWidth*0.47*pow(saturate(1.0-pow(mx,3.4)),1.9);
    }
    float mouthFront=smoothstep(-0.006,0.009,hp.z);
    float lipMask=smoothstep(lowerLipLine-0.0009,lowerLipLine+0.0009,hp.y)*(1.0-smoothstep(upperLipLine-0.0009,upperLipLine+0.0009,hp.y))*(1.0-smoothstep(0.94,1.04,mx))*mouthFront;
    float sy=(hp.y-seam)/0.00085;
    float seamMask=exp(-sy*sy)*(1.0-smoothstep(0.88,1.03,mx))*mouthFront;
    c*=mix(float3(1.0),maleFace ? float3(1.0,0.80,0.74) : float3(0.80,0.50,0.44),lipMask);
    if(maleFace){
        // male 2026-10-17 (= HeroFaceSkin): upper lip deeper/browner, lower lip lit across its upper middle, soft shadow under it
        float upperSideM=smoothstep(seam-0.0004,seam+0.0008,hp.y);
        float tLm=saturate((seam-hp.y)/max(seam-lowerLipLine,0.0001));
        float lt=(tLm-0.35)/0.25, lm=mx/0.5;
        c*=mix(float3(1.0),float3(0.74,0.66,0.64),lipMask*upperSideM);
        if(malePass){
            // = HeroFaceSkin male pass: lips a shade rosier and deeper, small shadows in the mouth corners
            c*=mix(float3(1.0),float3(0.95,0.86,0.85),lipMask);
            float kx=(abs(hp.x)-mouthWidth*1.02)/0.0024, ky=(hp.y-(seam-0.0003))/0.0022;
            c*=mix(float3(1.0),float3(0.66,0.56,0.52),exp(-2.0*kx*kx-2.0*ky*ky)*mouthFront*0.85);
        }else
        c*=mix(float3(1.0),float3(1.05,1.03,1.02),exp(-lt*lt)*exp(-lm*lm)*lipMask*(1.0-upperSideM));
        c*=mix(float3(1.0),float3(0.88,0.84,0.82),(1.0-smoothstep(0.70,1.0,mx))*lipMask);
        float bl=(hp.y-(lowerLipLine-0.0025))/0.0025, bm=mx/0.8;
        c*=mix(float3(1.0),float3(0.90,0.86,0.84),exp(-bl*bl)*exp(-bm*bm)*mouthFront*(1.0-lipMask));
    }
    if(!maleFace){
        // the upper lip a shade deeper than the lower; lip volume as pigment form (= HeroFaceSkin 2026-10-17)
        float upperSide=smoothstep(seam-0.0004,seam+0.0008,hp.y);
        c*=mix(float3(1.0),float3(1.06,1.03,1.03),lipMask*upperSide);
        float lat=1.0-smoothstep(0.70,1.0,mx);
        float tL=saturate((seam-hp.y)/max(seam-lowerLipLine,0.0001)), tU=saturate((hp.y-seam)/max(upperLipLine-seam,0.0001));
        float lt=(tL-0.38)/0.22, lm=mx/0.48;
        float lit=exp(-lt*lt)*exp(-lm*lm);
        float under=smoothstep(0.55,1.0,tL);
        c*=mix(float3(1.0),float3(1.08,1.05,1.04),lit*lipMask*(1.0-upperSide));
        c*=mix(float3(1.0),float3(0.86,0.80,0.79),under*lipMask*(1.0-upperSide));
        c*=mix(float3(1.0),float3(0.90,0.86,0.86),(1.0-smoothstep(0.15,0.6,tU))*lipMask*upperSide);
        c*=mix(float3(1.0),float3(0.85,0.80,0.80),(1.0-lat)*lipMask);
        float bl=(hp.y-(lowerLipLine-0.0022))/0.0022, bm=mx/0.75;
        float belowLip=exp(-bl*bl)*exp(-bm*bm)*mouthFront;
        c*=mix(float3(1.0),float3(0.92,0.88,0.86),belowLip*(1.0-lipMask));
    }
    c*=mix(float3(1.0),float3(0.50,0.30,0.26),seamMask*0.78);

    """
    static let faceSkinLidLiner = """
    float upperRim=maleFace ? 1.0-smoothstep(0.0012,0.0030,in.lidDistance.x) : 1.0-smoothstep(0.0014,0.0028,in.lidDistance.x);
    float lowerRim=1.0-smoothstep(0.0,0.0012,in.lidDistance.y);
    c*=mix(float3(1.0),maleFace ? float3(0.08,0.05,0.035) : float3(0.05,0.03,0.022),upperRim*0.96);
    if(maleFace){float cr=(in.lidDistance.x-0.0058)/(malePass ? 0.0014:0.0020);c*=mix(float3(1.0),float3(0.84,0.76,0.72),exp(-cr*cr)*step(in.lidDistance.x,in.lidDistance.y)*faceAmount*(malePass ? 0.85:0.55));}   // male 2026-10-17: upper-lid crease
    c*=mix(float3(1.0),float3(0.74,0.60,0.55),lowerRim*0.30);

    """
    static let faceSkinBodyEnd = """
    c*=mix(float3(1.0),float3(1.03,0.965,0.89),warmth);
    q=maleFace ? (hs-float3(0.050,-0.032,-0.010))/float3(0.024,0.020,0.060) : (hs-float3(0.046,-0.031,-0.005))/float3(0.025,0.021,0.060);
    float blush=saturate(exp(-2.0*dot(q,q)));
    c*=mix(float3(1.0),maleFace ? float3(1.02,0.93,0.91) : float3(1.035,0.80,0.77),blush);   // male 2026-10-17: no pink apples
    // skin pass: the ears and the nose tip a touch warmer; soft warm form shading (same regions as HeroFaceSkin)
    c*=mix(float3(1.0),float3(1.04,0.93,0.86),ears*0.45);
    if(malePass){float concha=SkinRegion(hs,float3(0.096,-0.022,-0.088),float3(0.010,0.016,0.012));c*=mix(float3(1.0),float3(1.03,0.90,0.82),ears*0.6);c*=mix(float3(1.0),float3(0.72,0.58,0.52),concha*0.6);}
    float noseTip=SkinRegion(hp,maleFace ? float3(0.0,-0.042,0.056) : float3(0.0,-0.037,0.032),maleFace ? float3(0.014,0.012,0.020) : float3(0.011,0.010,0.020));   // male: the 10-18 rounder, lower bulb (= HeroFaceSkin)
    c*=mix(float3(1.0),float3(1.05,0.93,0.86),noseTip*0.55);
    float browHollow=SkinRegion(hs,maleFace ? float3(0.034,0.020,0.017) : float3(0.036,0.029,0.006),float3(0.021,0.007,0.035));
    float innerCorner=SkinRegion(hs,maleFace ? float3(0.016,-0.006,0.025) : float3(0.016,-0.006,0.010),float3(0.007,0.011,0.035));
    float noseSide=SkinRegion(hs,maleFace ? float3(0.021,-0.042,0.044) : float3(0.020,-0.042,0.016),float3(0.007,0.011,0.035));
    float smileLine=SkinRegion(hs,maleFace ? float3(0.028,-0.056,0.039) : float3(0.026,-0.056,0.011),float3(0.007,0.013,0.035));
    float cheekHollow=SkinRegion(hs,maleFace ? float3(0.056,-0.071,0.014) : float3(0.053,-0.071,-0.004),float3(0.020,0.018,0.040));
    float jawSide=SkinRegion(hs,maleFace ? float3(0.064,-0.106,-0.020) : float3(0.060,-0.100,-0.040),float3(0.022,0.026,0.050));
    float neckWidth=1.0-smoothstep(maleFace ? 0.055 : 0.048,maleFace ? 0.080 : 0.070,abs(hp.x));
    float neck=smoothstep(-0.125,-0.160,hp.y)*(1.0-smoothstep(-0.270,-0.330,hp.y))*neckWidth;
    if(malePass) neck=smoothstep(-0.120,-0.145,hp.y)*(1.0-smoothstep(-0.165,-0.215,hp.y))*(1.0-smoothstep(0.040,0.090,abs(hp.x)))*0.55;   // = HeroFaceSkin: no hard band down to the chest
    float form=saturate(browHollow*0.85+innerCorner*0.70+noseSide*(malePass ? 0.20:0.65)+smileLine*(malePass ? 0.12:0.35)+cheekHollow*(malePass ? 0.25:0.60)+jawSide*0.55+neck*0.95)*(1.0-lipMask);
    c*=1.0+(maleFace ? float3(0.06,0.055,0.04) : float3(0.0))*smoothstep(-0.04,0.10,hp.y)*faceAmount;
    c*=mix(float3(1.0),float3(0.80,0.66,0.55),form);
    if(maleFace&&!malePass){   // the male pass is clean-shaven (= HeroFaceSkin _MaleBeard.z 0)
        q=(hp-float3(0.0,-0.126,-0.010))/float3(0.086,0.048,0.095);float jaw=exp(-2.0*dot(q,q));
        q=(hp-float3(0.0,-0.058,0.040))/float3(0.037,0.012,0.045);float upperLip=exp(-2.0*dot(q,q));
        q=(hs-float3(0.060,-0.077,0.002))/float3(0.032,0.052,0.055);float lowerCheeks=exp(-2.0*dot(q,q));
        // male 2026-10-17 (= HeroFaceSkin): the reference's visible stubble, neutral grey-brown, denser on the upper lip
        float beard=saturate(jaw*0.90+upperLip*0.85+lowerCheeks*0.75)*(1.0-lipMask);
        beard*=smoothstep(-0.150,-0.125,hp.y)*smoothstep(-0.055,-0.025,hp.z);
        c*=mix(float3(1.0),float3(0.76,0.74,0.72),beard);
        c*=mix(float3(1.0),float3(0.86,0.85,0.84),upperLip*(1.0-lipMask));
        float3 cell=floor(hp*1300.0);
        float stipple=smoothstep(0.45,0.85,fract(sin(dot(cell,float3(12.9898,78.233,45.164)))*43758.5453));
        float resolved=1.0-smoothstep(0.0005,0.0015,max(length(dfdx(hp)),length(dfdy(hp))));
        c*=1.0-stipple*beard*mix(0.12,0.36,resolved);
    }
    // skin pass: matte smoothness, lower wrap
    float surfaceSmoothness=mix(0.26,0.30,saturate(nose+forehead*0.55));
    float facialSmoothness=mix(mix(0.27,0.32,saturate(nose+forehead*0.75)),0.34,lipMask);
    surfaceSmoothness=mix(surfaceSmoothness,facialSmoothness,faceAmount);
    float surfaceWrap=mix(mix(0.20,0.24,faceAmount),0.26,lipMask);
    if(maleFace){
    // skin pass: golden grade (relative: every tone pick keeps its depth) and a faint grain, faded before it can alias
    c*=float3(1.0,1.035,0.92);
    float grainFootprint=max(length(dfdx(in.bindPos)),length(dfdy(in.bindPos)));
    float fineGrain=SkinNoise(in.bindPos*330.0)-0.5, coarseGrain=SkinNoise(in.bindPos*55.0)-0.5;
    c*=1.0+fineGrain*0.05*(1.0-smoothstep(0.0008,0.0025,grainFootprint));
    c*=mix(float3(1.0),float3(1.03,0.975,0.95),coarseGrain*1.2*(1.0-smoothstep(0.004,0.012,grainFootprint)));
    }
    float lum=dot(c,float3(0.2126,0.7152,0.0722));
    c=mix(float3(lum),c,maleFace ? (malePass ? max(athleteSurface.w,0.86):athleteSurface.w) : max(athleteSurface.w,0.95));
    _surface.diffuse=float4(c,1.0);
    // SceneKit already lights the final diffuse with the ambient light, and _surface.ambient is ADDED on top (negative works). HeroFaceSkin now warms its
    // ambient (x .82-.97 x (1, .86, .72)): add the difference to the old one, which the default matched within 1-2 % under the lobby rig.
    float3 ambientOld=mix(float3(0.82),float3(0.985,0.94,0.89),faceAmount), ambientNew=mix(0.82,0.97,faceAmount)*float3(1.0,0.86,0.72);
    if(!maleFace||malePass){
        // Female (and the male pass): indirect light in the tone's own deeper hue, darker on downward planes.
        float3 skinTone=saturate(c*c/max(dot(c,float3(0.2126,0.7152,0.0722)),0.04));
        float3 upView=normalize((scn_frame.viewTransform*float4(0.0,1.0,0.0,0.0)).xyz);
        float upness=saturate(dot(normalize(_surface.normal),upView)*0.5+0.5);
        ambientNew=mix(float3(1.0),skinTone/max(c,float3(0.001)),0.45)*mix(0.60,0.88,upness*upness)*mix(1.0,1.04,faceAmount);
    }
    _surface.ambient=float4(c*(ambientNew-ambientOld),1.0);
    // The warm lift under the nose is unlit in HeroFaceSkin, so it goes in as emission.
    _surface.emission=float4(c*(maleFace ? (malePass ? float3(0.30,0.21,0.16):float3(0.17,0.13,0.11)):float3(0.08,0.035,0.025))*noseUnderside*0.5,0.0);
    _surface.shininess=surfaceSmoothness;
    _surface.roughness=surfaceWrap;
    _surface.metalness=faceAmount;
    """

    /// HeroSkinShade blended into HeroFaceSkin's FaceSkinShade by the face amount (same wrap, light bleed and sheen), the skin rim at .30.
    static let faceSkinLighting = """
    #pragma arguments
    float4 athleteSurface;
    float4 athleteWarmth;
    float4 athleteRim;
    float4 headOrigin;
    float skinFinish;
    float skinPolish;
    float maleFormPass;
    #pragma body
    float3 n=normalize(_surface.normal), v=normalize(_surface.view), l=normalize(_light.direction);
    if(skinFinish>1.5||maleFormPass>0.5){   // the male face pass uses the female light model too (= HeroFaceSkin FaceSkinShade)
        // HeroFemaleSkinShade: Lambert form, a terminator band in the picked tone's own
        // saturated hue, a broad satin wash plus a soft core (2026-10-16 shader pass).
        float nl=dot(n,l), snl=saturate(nl);
        float wrapped=saturate((nl+0.34)/1.34), band=saturate(wrapped-snl);
        float3 h=normalize(l+v); float nh=saturate(dot(n,h)), vh=saturate(dot(v,h));
        float smoothness=_surface.shininess, gloss=saturate((smoothness-0.22)/0.20);
        float lobe=(pow(nh,6.0)*0.10*0.55+pow(nh,18.0+smoothness*16.0)*(0.08+0.10*gloss)*0.85)*(1.0+pow(1.0-vh,5.0)*1.6);
        float visibility=smoothstep(-0.02,0.30,nl);
        float3 albedo=max(_surface.diffuse.rgb,float3(0.001));
        float3 tone=saturate(albedo*albedo/max(dot(albedo,float3(0.2126,0.7152,0.0722)),0.04));
        _lightingContribution.diffuse+=_light.intensity.rgb*(float3(snl)+mix(float3(1.0),tone/albedo,0.75)*band*band*1.15);
        float rim=pow(1.0-saturate(dot(n,v)),athleteRim.y)*athleteRim.x;
        float3 sheenTint=mix(float3(1.0),saturate(albedo/max(dot(albedo,float3(0.2126,0.7152,0.0722)),0.04)),0.45);   // warm highlights (2026-10-17)
        _lightingContribution.specular+=_light.intensity.rgb*(lobe*visibility*sheenTint+rim*0.195*(float3(0.35)+0.65*_surface.diffuse.rgb));
    }else{
    float nl=dot(n,l), snl=saturate(nl);
    float faceAmount=_surface.metalness, wrap=_surface.roughness, smoothness=_surface.shininess;
    float3 h=normalize(l+v); float nh=saturate(dot(n,h));
    float wrapped=saturate((nl+wrap)/(1.0+wrap));
    float edge=saturate(wrapped-snl);
    float broad=pow(nh,18.0+smoothness*18.0)*0.075;
    if(skinPolish>0.5){float glossWeight=0.16+0.84*saturate((smoothness-0.32)/0.06);broad=(pow(nh,5.0+smoothness*6.0)*0.035+pow(nh,18.0+smoothness*18.0)*0.40)*glossWeight;}
    float visibility=smoothstep(-0.06,0.24,nl);
    float3 bodyDiffuse=float3(wrapped*0.84)+athleteWarmth.rgb*edge;
    // skin pass: matte (a faint wide sheen, highlight strength .40), a little lift on the lit face planes, a reddish-brown light bleed, a softer rim
    float faceWrapped=mix(wrapped,saturate((nl+0.30)/1.30),smoothstep(0.15,0.65,nl)*faceAmount*0.35);
    float sheen=pow(nh,8.0+smoothness*10.0)*0.045;
    float3 faceDiffuse=float3(faceWrapped*0.84)+float3(0.24,0.10,0.04)*saturate(faceWrapped-snl);
    float spec=mix(broad,sheen,faceAmount)*min(athleteSurface.z,0.40)*visibility;
    float rim=pow(1.0-saturate(dot(n,v)),athleteRim.y)*athleteRim.x;
    _lightingContribution.diffuse+=_light.intensity.rgb*mix(bodyDiffuse,faceDiffuse,faceAmount);
    _lightingContribution.specular+=_light.intensity.rgb*(float3(spec)+rim*0.30*(float3(0.35)+0.65*_surface.diffuse.rgb));
    }
    """

    /// HeroCharacterFinish outside the court profile: HeroHighlightRoll(colour, .76, .96), a late shoulder on the brightest channel (hue kept), so a light
    /// skin tone keeps its form under the key light instead of clipping to white.
    static let faceSkinFinish = """
    #pragma body
    {
        float3 skinOut=_output.color.rgb;
        float skinPeak=max(max(skinOut.r,skinOut.g),max(skinOut.b,1e-4)), skinExcess=max(skinPeak-0.76,0.0);
        float skinRolled=skinPeak<=0.76 ? skinPeak : 0.76+0.20*skinExcess/(0.20+skinExcess);
        _output.color.rgb=skinOut*(skinRolled/skinPeak);
    }
    """

    /// TennisCloth's kit edge lines (KitEdgeLines): the shoe's sole line and rubber band, the sock's cuff, cuff line and ribs, from HeroKitEdges' per-vertex measurements in metres.
    static let kitEdgeGeometry = """
    #pragma varyings
    float4 kitEdge;
    #pragma body
    out.kitEdge=float4(_geometry.texcoords[1],_geometry.texcoords[2]);
    """
    static let kitEdgeFragment = """

    float4 e=in.kitEdge;
    float wy=max(fwidth(e.y),1e-5), wx=max(fwidth(e.x),1e-5);
    float phase=atan2(e.z,e.y)*e.w, wp=fwidth(phase);
    float edgeShade=1.0;
    if(kitEdgeLines<1.5){
        if(e.z>0.5){
            float seamLine=1.0-smoothstep(0.00125-wy,0.00125+wy,abs(e.y-0.00025));
            float rubber=e.x>=0.0 ? 1.0-smoothstep(0.0065-wx,0.0065+wx,e.x) : 0.0;
            edgeShade=(1.0-0.45*seamLine)*(1.0-0.18*rubber);
        }
    }else if(e.w>0.5){
        float cuff=1.0-smoothstep(0.022-wx,0.022+wx,e.x);
        float ribFade=1.0-smoothstep(1.2,2.6,wp);
        float valley=0.5-0.5*cos(phase);
        float ribs=1.0-0.12*valley*valley*ribFade*cuff;
        float cuffLine=1.0-smoothstep(0.0008-wx,0.0008+wx,abs(e.x-0.022));
        float cuffTop=1.0-smoothstep(0.0012-wx,0.0012+wx,e.x);
        edgeShade=ribs*(1.0-0.32*cuffLine)*(1.0-0.14*cuffTop);
    }
    _output.color.rgb*=edgeShade;
    """

    /// Skin: TennisCharacter's triplanar soft normal, in Unity's space (the file negates z): three axis projections from the bind-pose position, weighted by the skinned object-space normal
    /// and added to it, then back to view space.
    static let skinSurface = """
    #pragma arguments
    texture2d<float> skinBumpMap;
    float4 skinBump;
    #pragma body
    constexpr sampler skinSmp(filter::linear, mip_filter::linear, address::repeat);
    float3 bp = float3(in.bindPos.x, in.bindPos.y, -in.bindPos.z);
    float3 nO = normalize((transpose(scn_node.modelViewTransform) * float4(_surface.normal, 0.0)).xyz);
    nO.z = -nO.z;
    float3 w = pow(abs(nO), float3(4.0));
    w /= (w.x + w.y + w.z + 1e-5);
    float2 tx = (skinBumpMap.sample(skinSmp, bp.zy * skinBump.y).rg * 2.0 - 1.0) * skinBump.x;
    float2 ty = (skinBumpMap.sample(skinSmp, bp.xz * skinBump.y).rg * 2.0 - 1.0) * skinBump.x;
    float2 tz = (skinBumpMap.sample(skinSmp, bp.xy * skinBump.y).rg * 2.0 - 1.0) * skinBump.x;
    nO = normalize(nO + w.x * float3(0.0, tx.y, tx.x) + w.y * float3(ty.x, 0.0, ty.y) + w.z * float3(tz.x, tz.y, 0.0));
    nO.z = -nO.z;
    _surface.normal = normalize((scn_node.normalTransform * float4(nO, 0.0)).xyz);
    """

    /// Cloth with no UVs (the racket grip): the role colour, the rim; no seam map and no weave (it would read one texel).
    static let clothSurfaceFlat = """
    #pragma arguments
    float4 clothTint;
    float4 rimParams;
    float4 rimLight;
    #pragma body
    float3 albedo = clothTint.rgb * 1.07;
    float3 n = normalize(_surface.normal);
    _surface.diffuse = float4(albedo, 1.0);
    _surface.specular = float4(1.0, 1.0, 1.0, 1.0);
    float ndv = saturate(dot(n, normalize(_surface.view)));
    float rim = pow(1.0 - ndv, rimParams.y) * rimParams.x;
    _surface.emission = float4(rimLight.rgb * rim * (0.35 + 0.65 * albedo), 0.0);
    """

    /// Cloth surface: the seam map (already in _surface.diffuse) times the role colour, the weave tilted into the normal and multiplied in as thread break; the rim goes in as emission.
    /// The tangent frame comes from screen-space derivatives of the UV (the kit's UVs are all the mesh has).
    static let clothSurface = """
    #pragma arguments
    texture2d<float> weaveMap;
    float4 clothTint;
    float4 weaveParams;
    float4 weaveParams2;
    float4 rimParams;
    float4 rimLight;
    #pragma body
    float2 uv = _surface.diffuseTexcoord;
    float3 albedo = _surface.diffuse.rgb * clothTint.rgb;
    float3 n = normalize(_surface.normal);
    float thr = 1.0;
    if (weaveParams.z > 0.001 || weaveParams.w > 0.001) {
        constexpr sampler wsmp(filter::linear, mip_filter::linear, address::repeat, max_anisotropy(4));
        float sn = sin(weaveParams.y), cs = cos(weaveParams.y);
        float2 wuv = float2(cs * uv.x - sn * uv.y, sn * uv.x + cs * uv.y) * weaveParams.x;
        float4 wv = weaveMap.sample(wsmp, wuv, bias(weaveParams2.x));
        // the weave is 8 threads per tile: where a thread is down to ~1 px (a whole body on a phone) it can only alias, and aliasing differs with each island's orientation. Fade the weave by the
        // pixels a thread covers on screen: the nominal tile (weaveParams2.w scene units) over the surface's world-space pixel footprint (the minor axis, or a quarter of the major: anisotropic x4)
        float3 dpx = dfdx(_surface.position), dpy = dfdy(_surface.position);
        float footprint = max(min(length(dpx), length(dpy)), max(length(dpx), length(dpy)) / 4.0) + 1e-7;
        float threadPixels = weaveParams2.w / footprint / 8.0;
        float fade = saturate((threadPixels - weaveParams2.y) / (weaveParams2.z - weaveParams2.y));
        wv = mix(float4(0.5, 0.5, 0.7629, 1.0), wv, fade);   // the flat weave: no slope, thread break at the map's mean (0.763 x 1.28 = 0.977)
        if (weaveParams.z > 0.001) {
            float2 txy = (wv.rg * 2.0 - 1.0) * weaveParams.z;
            txy = float2(cs * txy.x + sn * txy.y, -sn * txy.x + cs * txy.y);
            float3 ts = float3(txy, sqrt(saturate(1.0 - dot(txy, txy))));
            float3 dp1 = dfdx(_surface.position), dp2 = dfdy(_surface.position);
            float2 duv1 = dfdx(uv), duv2 = dfdy(uv);
            float3 dp2perp = cross(dp2, n), dp1perp = cross(n, dp1);
            float3 T = dp2perp * duv1.x + dp1perp * duv2.x;
            float3 B = dp2perp * duv1.y + dp1perp * duv2.y;
            float invmax = rsqrt(max(max(dot(T, T), dot(B, B)), 1e-20));
            n = normalize(T * invmax * ts.x + B * invmax * ts.y + n * ts.z);
        }
        thr = mix(1.0, wv.b * 1.28, weaveParams.w);
    }
    albedo *= 1.07 * thr;
    _surface.normal = n;
    _surface.diffuse = float4(albedo, 1.0);
    _surface.specular = float4(1.0, 1.0, 1.0, 1.0);
    float ndv = saturate(dot(n, normalize(_surface.view)));
    float rim = pow(1.0 - ndv, rimParams.y) * rimParams.x;
    _surface.emission = float4(rimLight.rgb * rim * (0.35 + 0.65 * albedo), 0.0);
    """

    /// Cloth lighting, per light: wrapped diffuse, a faint broad gloss, and the grazing sheen (tinted by sqrt of the cloth colour, gated by the light on that side).
    static let clothLighting = """
    #pragma arguments
    float4 clothLook;
    #pragma body
    float3 n = _surface.normal;
    float3 v = normalize(_surface.view);
    float ndl = dot(n, _light.direction);
    float wrapped = saturate((ndl + clothLook.x) / (1.0 + clothLook.x));
    float3 h = normalize(_light.direction + v);
    float spec = pow(saturate(dot(n, h)), clothLook.y * 28.0 + 2.0) * clothLook.y * 0.35 * saturate(ndl * 4.0);
    float ndv = saturate(dot(n, v));
    float graze = pow(1.0 - ndv, clothLook.w);
    float3 sheenTint = sqrt(max(_surface.diffuse.rgb, float3(0.0)));
    _lightingContribution.diffuse += _light.intensity.rgb * wrapped;
    _lightingContribution.specular += _light.intensity.rgb * (float3(spec) + sheenTint * (graze * saturate(ndl * 1.5) * clothLook.z));
    """

    /// Exposure, then roll the brightest channel off above the knee (hue kept): a lit white keeps a gradient instead of clipping.
    static let clothShoulder = """
    #pragma arguments
    float4 shoulder;
    #pragma body
    float3 c = _output.color.rgb * shoulder.x;
    float peak = max(max(c.r, c.g), max(c.b, 1e-4));
    float k = shoulder.y;
    float rolled = peak <= k ? peak : k + (1.0 - k) * (1.0 - exp(-(peak - k) / (1.0 - k)));
    _output.color.rgb = c * (rolled / peak);
    """
}


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
    /// Nil when one of the garment's maps is not in the app (the plain cloth stands in): a missing texture must never end the game.
    static func garment(_ look: MatchHeroData.Look, tint: SIMD3<Float>, trim: SIMD3<Float>?, edges: Bool = false) -> SCNMaterial? {
        guard let n = compressed(look.normalMap ?? ""), let mask = compressed(look.maskMap ?? ""), let atlas = compressed(look.weaveMap) else {
            SportsDiagnostics.write("garment maps missing: \(look.normalMap ?? "-") \(look.maskMap ?? "-") \(look.weaveMap)")
            return nil
        }
        let m = SCNMaterial(); m.lightingModel = .blinn
        m.diffuse.contents = flatColour(tint)
        for (key, tex) in [("garmentN", n), ("garmentM", mask), ("fabricAtlas", atlas)] {
            let prop = SCNMaterialProperty(contents: tex); prop.wrapS = .clamp; prop.wrapT = .clamp
            prop.mipFilter = .linear; prop.minificationFilter = .linear; prop.magnificationFilter = .linear; prop.maxAnisotropy = 4
            m.setValue(prop, forKey: key)
        }
        let fallback = look.trimColor ?? [0.035, 0.035, 0.0401]
        let c = trim ?? SIMD3(fallback[0], fallback[1], fallback[2])
        m.setValue(SCNVector4(srgbToLinear(tint.x), srgbToLinear(tint.y), srgbToLinear(tint.z), 1), forKey: "clothTint")
        if let bindingTone = look.bindingTone, bindingTone > 0 {
            m.setValue(SCNVector4(srgbToLinear(tint.x) * bindingTone, srgbToLinear(tint.y) * bindingTone, srgbToLinear(tint.z) * bindingTone, 1), forKey: "trimTint")
        } else {
            m.setValue(SCNVector4(srgbToLinear(c.x), srgbToLinear(c.y), srgbToLinear(c.z), 1), forKey: "trimTint")
        }
        m.setValue(SCNVector4(look.weaveTile, look.weaveAngle * .pi / 180, look.weaveNormal, look.weaveThread), forKey: "weaveParams")
        m.setValue(SCNVector4(look.normalStrength ?? 1, 0, 0, 0), forKey: "normalParams")
        m.setValue(SCNVector4(look.wrap, look.smoothness, look.sheenStrength, look.sheenPower), forKey: "clothLook")
        m.setValue(SCNVector4(look.rimStrength, look.rimPower, 0, 0), forKey: "rimParams")
        m.setValue(SCNVector4(rimLight.x, rimLight.y, rimLight.z, 0), forKey: "rimLight")
        m.setValue(SCNVector4(look.exposure * 1.0, look.knee, 0, 0), forKey: "shoulder")
        let golf = (look.fabricVersion ?? 1) > 1.5
        var surface = golf ? garmentSurfaceV2 : garmentSurface
        var lighting = golf ? garmentLightingV2 : garmentLighting
        var finish = garmentShoulder
        if (look.femaleSurface ?? 0) > 0.5 {
            surface = surface.replacingOccurrences(of:"cavity=mix(0.4,1.0,mask.g)",with:"cavity=mix(0.88,1.0,mask.g)")
            surface = surface.replacingOccurrences(of:"#pragma body",with:femaleGrainFunctions+"\n#pragma body")
            surface = surface.replacingOccurrences(of:"_surface.normal=n;",with:femaleGrainBody+"\n    _surface.normal=n;")
            surface += femaleClothAmbient
            if edges, (look.edgeLines ?? 0)>0.5, (look.edgeLines ?? 0)<1.5 {
                surface=surface.replacingOccurrences(of:"float3 nts =",with:"id=in.kitEdge.x>=0.0?3.0:2.0;\nfloat3 nts =")
            }
            if (look.femaleSurface ?? 0)>1.5 {
                surface=surface.replacingOccurrences(of:"float2 slope = (detail.rg*2.0-1.0)*weaveParams.z*fade;",with:"float2 slope = (detail.rg*2.0-1.0)*weaveParams.z*fade*(1.0-mask.b);")
                surface=surface.replacingOccurrences(of:"weaveParams.w*fade)",with:"weaveParams.w*fade*(1.0-mask.b))")
                surface=surface.replacingOccurrences(of:"cluster=(FemaleClothGrain(grainUV)-0.5)*grainFade;",with:"cluster=(FemaleClothGrain(grainUV)-0.5)*grainFade*(1.0-mask.b);")
                surface=surface.replacingOccurrences(of:"_surface.shininess=cluster;",with:"_surface.shininess=mask.b;")
            }
            lighting = femaleFabricLighting(golf:golf,garment:true)
            if (look.femaleSurface ?? 0)>1.5 {
                lighting=lighting.replacingOccurrences(of:"smooth*=0.65*(1.0+_surface.shininess*0.25);sheen*=0.90;",with:"smooth*=0.65;sheen*=0.90*(1.0-_surface.shininess);")
            }
            finish = finish.replacingOccurrences(of:"mix(0.75, 1.0, _surface.specular.a)",with:"mix(0.95, 1.0, _surface.specular.a)")
        }
        m.shaderModifiers = [.surface: surface, .lightingModel: lighting, .fragment: finish]
        if edges, let kind = look.edgeLines, kind > 0.5 {
            // TennisCloth's kit edge lines (HeroKitEdges data in texcoord channels 1-2), multiplied into the finished colour as Unity does
            m.setValue(kind, forKey: "kitEdgeLines")
            m.shaderModifiers?[.geometry] = kitEdgeGeometry
            m.shaderModifiers?[.fragment] = finish.replacingOccurrences(of: "#pragma body", with: "float kitEdgeLines;\n#pragma body") + kitEdgeFragment
        }
        return m
    }
    // Same neutral, derivative-filtered knit clusters as TennisCloth's female branch.
    static let femaleGrainFunctions = """
    #pragma declaration
    float FemaleClothHash(float2 p){float3 h=fract(float3(p.x,p.y,p.x)*0.1031);h+=dot(h,h.yzx+33.33);return fract((h.x+h.y)*h.z);}
    float FemaleClothGrain(float2 p){float2 c=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(FemaleClothHash(c),FemaleClothHash(c+float2(1.0,0.0)),f.x),mix(FemaleClothHash(c+float2(0.0,1.0)),FemaleClothHash(c+1.0),f.x),f.y);}
    """
    static let femaleGrainBody = """
    float cluster=0.0;
    if(!(id>2.5&&id<4.5)){
        float2 grainUV=wu*9.0;
        float grainFade=1.0-smoothstep(0.35,0.85,max(length(dfdx(grainUV)),length(dfdy(grainUV))));
        cluster=(FemaleClothGrain(grainUV)-0.5)*grainFade;
        albedo*=1.0+cluster*0.09;
    }
    _surface.shininess=cluster;
    """
    static func femaleFabricLighting(golf: Bool, garment: Bool) -> String {
        let id=garment ? "float id=floor(_surface.roughness*\(golf ? "9.0":"5.0")+0.5);":"float id=femaleClothKind;"
        let parameters=garment ? """
        float smooth=id==0.0?0.10:id==1.0?0.13:id==2.0?0.16:id==3.0?0.04:id==4.0?0.08:0.10;
        float sheen=id==0.0?0.55:id==1.0?0.38:id==2.0?0.24:id==5.0?0.18:0.0;
        if(id>5.5){smooth=id<6.5?0.09:id<7.5?0.12:id<8.5?0.18:0.08;sheen=id<6.5?0.24:id<7.5?0.32:id<8.5?0.10:0.18;}
        smooth*=0.65*(1.0+_surface.shininess*0.25);sheen*=0.90;
        """:"float smooth=clothLook.y,sheen=clothLook.z;"
        return """
        #pragma arguments
        float4 clothLook;
        float femaleClothKind;
        #pragma body
        \(id)
        \(parameters)
        float3 n=normalize(_surface.normal),v=normalize(_surface.view),l=normalize(_light.direction);
        float nl=saturate(dot(n,l)),nv=saturate(dot(n,v)),nh=saturate(dot(n,normalize(l+v)));
        float wrapped=saturate((dot(n,l)+clothLook.x)/(1.0+clothLook.x));
        // FemaleClothShade (2026-10-16): matte Lambert form, a terminator band in the
        // colour's own deeper hue, rounded volume toward the silhouette and a Charlie
        // velvet lobe for knit; rubber keeps a small highlight and no sheen.
        float rubber=id>2.5&&id<4.5?1.0:0.0;
        float3 albedo=max(_surface.diffuse.rgb,float3(0.001));
        float band=saturate(wrapped-nl);
        float3 deep=saturate(albedo*albedo/max(dot(albedo,float3(0.2126,0.7152,0.0722)),0.04));
        float charlie=(2.0+1.55)*pow(max(1.0-nh*nh,0.0001),0.775)*0.15915494;
        float visibility=1.0/max(4.0*(nl+nv-nl*nv),0.10);
        float3 fibreTint=mix(albedo,sqrt(albedo),0.45);
        float3 velvet=fibreTint*(charlie*visibility*nl*sheen*2.4)*(1.0-rubber);
        float spec=pow(nh,24.0+smooth*60.0)*0.035*nl*rubber;
        float body=mix(1.0,mix(0.64,1.0,sqrt(nv)),1.0-rubber);
        _lightingContribution.diffuse+=_light.intensity.rgb*(float3(nl*0.96)+mix(float3(1.0),deep/albedo,0.65)*band*0.85*(1.0-rubber*0.5))*body;
        _lightingContribution.specular+=_light.intensity.rgb*(velvet+spec);
        """
    }

    /// TennisCloth female ambient: the folds' own deeper colour, darker on downward planes and toward the silhouette.
    static let femaleClothAmbient = """

    {
        float3 clothA=max(_surface.diffuse.rgb,float3(0.001));
        float3 clothDeep=saturate(clothA*clothA/max(dot(clothA,float3(0.2126,0.7152,0.0722)),0.04));
        float3 clothUp=normalize((scn_frame.viewTransform*float4(0.0,1.0,0.0,0.0)).xyz);
        float clothUpness=saturate(dot(normalize(_surface.normal),clothUp)*0.5+0.5);
        float clothNv=saturate(dot(normalize(_surface.normal),normalize(_surface.view)));
        float3 clothAmbient=mix(float3(1.0),clothDeep/clothA,0.40)*mix(0.58,0.98,clothUpness*clothUpness)*mix(0.80,1.0,sqrt(clothNv));
        _surface.ambient.rgb+=_surface.diffuse.rgb*(clothAmbient-1.0);
    }

    """
    static let garmentShoulder = clothShoulder + "\n_output.color.rgb *= mix(0.68, 1.0, _surface.metalness) * mix(0.75, 1.0, _surface.specular.a);\n"
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
    float threadVisibility=mix(1.0,detail.b*1.28,weaveParams.w*fade);
    float ao=max(mask.r,0.7), cavity=mix(0.4,1.0,mask.g);
    float3 albedo=mix(clothTint.rgb,trimTint.rgb,mask.b)*threadVisibility*cavity;
    _surface.normal=n;
    _surface.diffuse=float4(albedo*mix(1.0,ao,0.5),1.0);
    _surface.specular=float4(albedo,mask.g);
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
    // v2 extends the same cloth modifier; v1 source and all tennis values stay exact.
    static var garmentSurfaceV2: String {
        garmentSurface.replacingOccurrences(of: "mask.a * 5.0", with: "mask.a * 9.0")
            .replacingOccurrences(of: "_surface.roughness=id/5.0", with: "_surface.roughness=id/9.0")
            .replacingOccurrences(of: "float freq = id==1.0 || id==5.0 ? 12.0 : 8.0;", with: "if(id>5.5)quad=id<6.5?float2(0.0):id<7.5?float2(0.5,0.0):id<8.5?float2(0.0,0.5):float2(0.5,0.5);\nfloat freq=id==7.0?10.0:id==1.0 || id==5.0 ?12.0:8.0;")
    }
    static var garmentLightingV2: String {
        garmentLighting.replacingOccurrences(of: "_surface.roughness*5.0", with: "_surface.roughness*9.0")
            .replacingOccurrences(of: "float3 n=normalize(_surface.normal)", with: "if(id>5.5){smooth=id<6.5?0.09:id<7.5?0.12:id<8.5?0.18:0.08;sheen=id<6.5?0.24:id<7.5?0.32:id<8.5?0.10:0.18;}\nfloat3 n=normalize(_surface.normal)")
    }
}
