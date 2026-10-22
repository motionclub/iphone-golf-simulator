import SceneKit
import AppKit
import Metal
import simd

// LOCKER_MIRROR render harness (macOS): compiles the app's own MatchHeroData / MatchHeroSurfaces / MatchHeroMotion files and renders the hero with the locker's lights.
// usage: harness <outDir> <scenario> [male|female] [more...]

let repo = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
let assetsDir = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/golf-look/locker/assets"

func png(_ image: NSImage, _ path: String) {
    guard let tiff = image.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff), let data = rep.representation(using: .png, properties: [:]) else { return }
    try? data.write(to: URL(fileURLWithPath: path))
}

@MainActor let sharedRenderer = SCNRenderer(device: MTLCreateSystemDefaultDevice()!, options:nil)

@MainActor
final class Stage {
    let scene = SCNScene(), character = SCNNode(), cameraNode = SCNNode()
    init(cameraDistance: Float) {
        scene.rootNode.addChildNode(character)
        cameraNode.camera = SCNCamera(); cameraNode.camera?.fieldOfView = 32; cameraNode.camera?.zNear = 0.05
        cameraNode.position = SCNVector3(0, 1.0, CGFloat(cameraDistance)); cameraNode.look(at: SCNVector3(0, 0.92, 0))
        scene.rootNode.addChildNode(cameraNode)
        func light(_ type: SCNLight.LightType, _ intensity: CGFloat, _ color: NSColor, elevation: Float, azimuth: Float, shadow: Bool = false) {
            let node = SCNNode(), l = SCNLight(); l.type = type; l.intensity = intensity; l.color = color
            if shadow {
                l.castsShadow = true; l.shadowRadius = 6; l.shadowSampleCount = 8; l.shadowMode = .deferred
                l.shadowColor = NSColor(red: 0.12, green: 0.14, blue: 0.24, alpha: 0.35); l.orthographicScale = 2.2
            }
            node.light = l
            let e = elevation * .pi / 180, a = azimuth * .pi / 180
            node.position = SCNVector3(CGFloat(-sin(a) * cos(e) * 6), CGFloat(sin(e) * 6), CGFloat(cos(a) * cos(e) * 6))
            node.look(at: SCNVector3(0, 0.8, 0)); scene.rootNode.addChildNode(node)
        }
        light(.directional, 1050, NSColor(red: 1, green: 0.92, blue: 0.82, alpha: 1), elevation: 40, azimuth: 38, shadow: true)
        light(.directional, 370, NSColor(red: 0.84, green: 0.9, blue: 1, alpha: 1), elevation: 18, azimuth: -55)
        light(.directional, 520, NSColor(red: 1, green: 0.96, blue: 0.9, alpha: 1), elevation: 35, azimuth: 160)
        let amb = SCNNode(); amb.light = SCNLight(); amb.light?.type = .ambient; amb.light?.intensity = 210
        amb.light?.color = NSColor(red: 0.86, green: 0.88, blue: 0.96, alpha: 1); scene.rootNode.addChildNode(amb)
        scene.background.contents = NSColor(red: 0.93, green: 0.62, blue: 0.48, alpha: 1)
    }
    func frame(_ framing: String, cameraDistance: Float, headCentre: Float) {
        let dist = max(2.4, cameraDistance) * 1.05
        switch framing {
        case "head": cameraNode.position = SCNVector3(0, CGFloat(headCentre + 0.04), 1.15); cameraNode.look(at: SCNVector3(0, CGFloat(headCentre), 0))
        case "torso": cameraNode.position = SCNVector3(0, CGFloat(headCentre - 0.40 + 0.06), 2.1); cameraNode.look(at: SCNVector3(0, CGFloat(headCentre - 0.40), 0))
        case "feet": cameraNode.position = SCNVector3(0.15, 0.30 + 0.22, 1.5); cameraNode.look(at: SCNVector3(0, 0.30, 0))
        case "shirt": cameraNode.position = SCNVector3(0, CGFloat(headCentre - 0.40 + 0.06), 1.15); cameraNode.look(at: SCNVector3(0, CGFloat(headCentre - 0.40), 0))
        default: cameraNode.position = SCNVector3(0, 0.9, CGFloat(dist)); cameraNode.look(at: SCNVector3(0, 0.76, 0))
        }
    }
    func snapshot(_ size: CGSize, device: MTLDevice) -> NSImage {
        sharedRenderer.scene=scene;sharedRenderer.pointOfView=cameraNode
        return sharedRenderer.snapshot(atTime:0,with:size,antialiasingMode:.multisampling4X)
    }
}

@MainActor
func capture(_ st: Stage, _ size: CGSize, _ path: String, _ device: MTLDevice) {
    for i in 0..<9 { png(st.snapshot(size, device: device), path + ".r" + String(i) + ".png") }
}

@MainActor
func runOriginal() {
    let args = CommandLine.arguments
    let out = (args.count > 1 ? args[1] : ".") + "/before"
    let scenario = args.count > 2 ? args[2] : "static"
    if let e = ProcessInfo.processInfo.environment["LM_EXPOSURE"], let v = Float(e) { FrozenMatchHeroSurfaces.sceneExposure = v }
    if let e = ProcessInfo.processInfo.environment["LM_BIAS"], let v = Float(e) { FrozenMatchHeroSurfaces.weaveMipBias = v }
    if let e = ProcessInfo.processInfo.environment["LM_THOFF"], let v = Float(e) { FrozenMatchHeroSurfaces.weaveThreadPixelsOff = v }
    if let e = ProcessInfo.processInfo.environment["LM_THFULL"], let v = Float(e) { FrozenMatchHeroSurfaces.weaveThreadPixelsFull = v }
    let bigSize = ProcessInfo.processInfo.environment["LM_BIG"] != nil
    try? FileManager.default.createDirectory(atPath: out, withIntermediateDirectories: true)
    FrozenMatchHeroData.locate = { name, ext in
        let u = URL(fileURLWithPath: assetsDir + "/" + name + "." + ext); return FileManager.default.fileExists(atPath: u.path) ? u : nil
    }
    let device = MTLCreateSystemDefaultDevice()!
    func sRGB(_ hex: String) -> SIMD3<Float> {
        let n = UInt32(hex, radix: 16) ?? 0xFFFFFF
        return SIMD3(Float((n >> 16) & 255) / 255, Float((n >> 8) & 255) / 255, Float(n & 255) / 255)
    }
    func kitTint(_ pick: SIMD3<Float>) -> SIMD3<Float> { SIMD3(max(0.93 * pick.x, 0.035), max(0.93 * pick.y, 0.035), max(0.93 * pick.z, 0.0401)) }
    func kitDerive(_ pick: SIMD3<Float>) -> SIMD3<Float> { let l = 0.2126 * pick.x + 0.7152 * pick.y + 0.0722 * pick.z; return l >= 0.5 ? pick * 0.65 : pick + (SIMD3<Float>(repeating: 1) - pick) * 0.35 }
    let dummyFile = ProcessInfo.processInfo.environment["CLOTH_DUMMY_FILE"]
    let dummyData = dummyFile.flatMap { try? Data(contentsOf: URL(fileURLWithPath: $0)) }
    let dummy = dummyData.flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String: String] }
    let dummyHex = dummy?["main_hex"]
    let skins: [Bool: String] = [false: "E3A06E", true: "E6B396"]
    for female in [false, true] {
        let sex = female ? "female" : "male"
        guard let asset = FrozenMatchHeroData.asset(female: female) else { print("no asset"); return }
        let picked = args.contains("picked")
        let picks = FrozenMatchHeroData.Picks(colour: { name in
            if let hex = dummyHex {
                if name == "Kit_Shirt" { return kitTint(sRGB(hex)) }
                if name == "Kit_ShirtTrim" { return kitTint(kitDerive(sRGB(hex))) }
            }
            switch name {
            case "Skin": return sRGB(skins[female]!)
            case "Kit_Shirt": return picked ? kitTint(sRGB("FF6B4A")) : nil
            case "Kit_ShirtTrim": return picked ? kitTint(kitDerive(sRGB("FF6B4A"))) : nil
            case "Kit_Shorts": return picked ? kitTint(sRGB("1E2A6E")) : nil
            case "Kit_ShortsBand": return picked ? kitTint(kitDerive(sRGB("1E2A6E"))) : nil
            case "Kit_Shoe": return picked ? kitTint(sRGB("9EE63A")) : nil
            default: return nil
            }
        })
        let headCentre = asset.manifest.headCentreY * asset.scale
        func stage(_ framing: String, dist: Float = 3.25) -> Stage {
            let st = Stage(cameraDistance: dist); st.frame(framing, cameraDistance: dist, headCentre: headCentre)
            return st
        }
        switch scenario {
        case "cloth":
            for framing in ["shirt", "collar", "shoe_side"] {
                let st = stage("shirt")
                let hero = FrozenMatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
                if framing == "collar" { st.cameraNode.camera?.fieldOfView = 24; st.cameraNode.position = SCNVector3(0.03, CGFloat(headCentre-0.15), 0.75); st.cameraNode.look(at:SCNVector3(0,CGFloat(headCentre-0.20),0)) }
                if framing == "shoe_side", let shoe=hero.childNode(withName:"Kit_Shoe_R",recursively:true), let g=shoe.geometry {
                    let bounds=g.boundingBox;let mid=SCNVector3((bounds.min.x+bounds.max.x)/2,(bounds.min.y+bounds.max.y)/2,(bounds.min.z+bounds.max.z)/2)
                    let t=shoe.convertPosition(mid,to:st.scene.rootNode)
                    st.cameraNode.camera?.fieldOfView=34;st.cameraNode.position=SCNVector3(t.x-CGFloat(0.65*asset.scale),t.y+CGFloat(0.04*asset.scale),t.z+CGFloat(0.08*asset.scale));st.cameraNode.look(at:t)
                }
                if dummyHex != nil, let top=hero.childNode(withName:"Kit_Top",recursively:true) {
                    let duplicate=top.clone();duplicate.name="Dummy_Polo_Duplicate";top.parent?.addChildNode(duplicate);top.removeFromParentNode()
                }
                png(st.snapshot(CGSize(width:1080,height:1080),device:device), "\(out)/cloth_\(sex)_\(framing)\(dummyHex == nil ? "" : "_dummy").png")
            }
        case "static":
            for framing in ["body", "shirt", "torso", "feet", "head"] {
                let st = stage(framing)
                let hero = FrozenMatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
                capture(st, bigSize ? CGSize(width: 1080, height: 1500) : CGSize(width: 720, height: 1000), "\(out)/static_\(sex)_\(framing)\(picked ? "_picked" : "").png", device)
            }
        case "dbg":
            // which part of the cloth look makes the patches: seam map off, weave normal off, both
            for variant in ["full", "single", "plain", "plainsingle"] {
                let st = stage("shirt")
                let hero = FrozenMatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
                hero.enumerateChildNodes { node, _ in
                    for m in node.geometry?.materials ?? [] where m.shaderModifiers?[.lightingModel] != nil {
                        if variant == "single" || variant == "plainsingle" { m.isDoubleSided = false }
                        if variant == "plain" || variant == "plainsingle" { m.diffuse.contents = CGColor(gray: 1, alpha: 1) }
                        if variant == "plain" || variant == "plainsingle" { if let v = m.value(forKey: "weaveParams") as? SCNVector4 { m.setValue(SCNVector4(v.x, v.y, 0, 0), forKey: "weaveParams") } }
                    }
                }
                capture(st, CGSize(width: 720, height: 1000), "\(out)/dbg_\(sex)_\(variant).png", device)
            }
        case "uvchecker":
            let st = stage("shirt")
            let hero = FrozenMatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
            hero.enumerateChildNodes { node, _ in
                for m in node.geometry?.materials ?? [] where m.shaderModifiers?[.lightingModel] != nil && m.value(forKey: "weaveParams") != nil {
                    m.shaderModifiers = [.surface: """
                    #pragma body
                    float2 g = floor(_surface.diffuseTexcoord * 40.0);
                    float c = fmod(g.x + g.y, 2.0);
                    _surface.diffuse = float4(float3(0.15 + 0.7 * c), 1.0);
                    _surface.emission = float4(0.0);
                    """]
                }
            }
            capture(st, CGSize(width: 720, height: 1000), "\(out)/uvchecker_\(sex).png", device)
        case "skinbump":
            // exaggerate the skin normal to check it is wired (x scale), then the real strength
            for (label, scale) in [("real", Float(1)), ("x6", Float(6))] {
                let st = stage("torso")
                let hero = FrozenMatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
                hero.enumerateChildNodes { node, _ in
                    for m in node.geometry?.materials ?? [] where m.name == "Skin" { if let v = m.value(forKey: "skinBump") as? SCNVector4 { m.setValue(SCNVector4(v.x * CGFloat(scale), v.y, 0, 0), forKey: "skinBump") } }
                }
                capture(st, CGSize(width: 720, height: 1000), "\(out)/skinbump_\(sex)_\(label).png", device)
            }
        case "lod":
            let st = stage("shirt")
            let hero = FrozenMatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
            hero.enumerateChildNodes { node, _ in
                for m in node.geometry?.materials ?? [] where m.shaderModifiers?[.lightingModel] != nil && m.value(forKey: "weaveParams") != nil {
                    m.shaderModifiers = [.surface: """
                    #pragma arguments
                    float4 weaveParams;
                    float4 clothTint;
                    #pragma body
                    float2 uv = _surface.diffuseTexcoord * weaveParams.x * 256.0;
                    float lod = log2(max(length(dfdx(uv)), length(dfdy(uv))) + 1e-6);
                    float3 c = float3(saturate(lod / 8.0), saturate(1.0 - fabs(lod - 4.0) / 4.0), saturate(1.0 - lod / 6.0));
                    _surface.diffuse = float4(c, 1.0);
                    _surface.emission = float4(0.0);
                    """]
                    m.setValue(SCNVector4(1,1,1,1), forKey: "clothTint")
                }
            }
            capture(st, CGSize(width: 720, height: 1000), "\(out)/lod_\(sex).png", device)
        case "shoedbg":
            for variant in ["full", "noseam", "noweave", "plain"] {
                let st = stage("feet")
                st.cameraNode.position = SCNVector3(0.30, 0.34, 0.95); st.cameraNode.look(at: SCNVector3(0, 0.10, 0))
                let hero = FrozenMatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
                hero.enumerateChildNodes { node, _ in
                    guard node.name?.hasPrefix("Kit_Shoe") == true || node.name?.hasPrefix("Kit_Sock") == true else { return }
                    for m in node.geometry?.materials ?? [] {
                        if variant == "noseam" || variant == "plain" { m.diffuse.contents = CGColor(gray: 1, alpha: 1) }
                        if variant == "noweave" || variant == "plain" { if let v = m.value(forKey: "weaveParams") as? SCNVector4 { m.setValue(SCNVector4(v.x, v.y, 0, 0), forKey: "weaveParams") } }
                    }
                }
                capture(st, CGSize(width: 900, height: 900), "\(out)/shoedbg_\(sex)_\(variant).png", device)
            }
        case "rig":
            // static vs rigged at ReadyIdle frame 0
            var imgs: [NSImage] = []
            for rigged in [false, true] {
                let st = stage("body")
                let hero = FrozenMatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
                if rigged, let rig = FrozenHeroRig(root: hero, asset: asset) { rig.attach() }
                let img = st.snapshot(CGSize(width: 720, height: 1000), device: device); imgs.append(img)
                png(img, "\(out)/rig_\(sex)_\(rigged ? "skinned" : "static").png")
            }
            func px(_ i: NSImage) -> [UInt8] { let r = NSBitmapImageRep(data: i.tiffRepresentation!)!; var o = [UInt8](); for y in 0..<r.pixelsHigh { for x in 0..<r.pixelsWide { let c = r.colorAt(x: x, y: y)!.usingColorSpace(.sRGB)!; o += [UInt8(c.redComponent * 255), UInt8(c.greenComponent * 255), UInt8(c.blueComponent * 255)] } }; return o }
            let a = px(imgs[0]), b = px(imgs[1]); var d = 0, over = 0
            for i in 0..<a.count { let e = abs(Int(a[i]) - Int(b[i])); d += e; if e > 24 { over += 1 } }
            print("\(sex): static vs skinned ReadyIdle[0]: mean abs diff \(Double(d) / Double(a.count)), channels > 24: \(over) of \(a.count)")
        case "serveend":
            let st = stage("body", dist: 3.6)
            let hero = FrozenMatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
            guard let rig = FrozenHeroRig(root: hero, asset: asset) else { print("no rig"); return }
            rig.attach()
            for (k, t) in stride(from: 2.4, through: 3.9, by: 0.1).enumerated() {
                rig.apply(FrozenMenuMotion.serveOnce, at: t)
                capture(st, CGSize(width: 480, height: 640), "\(out)/serveend_\(sex)_\(String(format: "%02d", k)).png", device)
            }
        case "ready", "serve":
            let st = stage("body", dist: scenario == "serve" ? 4.4 : 3.25)
            let hero = FrozenMatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
            guard let rig = FrozenHeroRig(root: hero, asset: asset) else { print("no rig"); return }
            rig.attach()
            let motion: FrozenMenuMotion = scenario == "serve" ? .serveOnce : .ready
            let times = scenario == "serve" ? stride(from: 0.0, through: 4.2, by: 0.3).map { $0 } : stride(from: 0.0, through: 2.2, by: 0.275).map { $0 }
            for (k, t) in times.enumerated() {
                rig.apply(motion, at: t)
                capture(st, CGSize(width: 480, height: 640), "\(out)/\(scenario)_\(sex)_\(String(format: "%02d", k)).png", device)
            }
        default: print("unknown scenario")
        }
    }
}
@MainActor
func runCandidate() {
    let args = CommandLine.arguments
    let out = (args.count > 1 ? args[1] : ".") + "/after"
    let scenario = args.count > 2 ? args[2] : "static"
    if let e = ProcessInfo.processInfo.environment["LM_EXPOSURE"], let v = Float(e) { MatchHeroSurfaces.sceneExposure = v }
    if let e = ProcessInfo.processInfo.environment["LM_BIAS"], let v = Float(e) { MatchHeroSurfaces.weaveMipBias = v }
    if let e = ProcessInfo.processInfo.environment["LM_THOFF"], let v = Float(e) { MatchHeroSurfaces.weaveThreadPixelsOff = v }
    if let e = ProcessInfo.processInfo.environment["LM_THFULL"], let v = Float(e) { MatchHeroSurfaces.weaveThreadPixelsFull = v }
    let bigSize = ProcessInfo.processInfo.environment["LM_BIG"] != nil
    try? FileManager.default.createDirectory(atPath: out, withIntermediateDirectories: true)
    MatchHeroData.locate = { name, ext in
        let u = URL(fileURLWithPath: assetsDir + "/" + name + "." + ext); return FileManager.default.fileExists(atPath: u.path) ? u : nil
    }
    let device = MTLCreateSystemDefaultDevice()!
    func sRGB(_ hex: String) -> SIMD3<Float> {
        let n = UInt32(hex, radix: 16) ?? 0xFFFFFF
        return SIMD3(Float((n >> 16) & 255) / 255, Float((n >> 8) & 255) / 255, Float(n & 255) / 255)
    }
    func kitTint(_ pick: SIMD3<Float>) -> SIMD3<Float> { SIMD3(max(0.93 * pick.x, 0.035), max(0.93 * pick.y, 0.035), max(0.93 * pick.z, 0.0401)) }
    func kitDerive(_ pick: SIMD3<Float>) -> SIMD3<Float> { let l = 0.2126 * pick.x + 0.7152 * pick.y + 0.0722 * pick.z; return l >= 0.5 ? pick * 0.65 : pick + (SIMD3<Float>(repeating: 1) - pick) * 0.35 }
    let dummyFile = ProcessInfo.processInfo.environment["CLOTH_DUMMY_FILE"]
    let dummyData = dummyFile.flatMap { try? Data(contentsOf: URL(fileURLWithPath: $0)) }
    let dummy = dummyData.flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String: String] }
    let dummyHex = dummy?["main_hex"]
    let skins: [Bool: String] = [false: "E3A06E", true: "E6B396"]
    for female in [false, true] {
        let sex = female ? "female" : "male"
        guard let asset = MatchHeroData.asset(female: female) else { print("no asset"); return }
        let picked = args.contains("picked")
        let picks = MatchHeroData.Picks(colour: { name in
            if let hex = dummyHex {
                if name == "Kit_Shirt" { return kitTint(sRGB(hex)) }
                if name == "Kit_ShirtTrim" { return kitTint(kitDerive(sRGB(hex))) }
            }
            switch name {
            case "Skin": return sRGB(skins[female]!)
            case "Kit_Shirt": return picked ? kitTint(sRGB("FF6B4A")) : nil
            case "Kit_ShirtTrim": return picked ? kitTint(kitDerive(sRGB("FF6B4A"))) : nil
            case "Kit_Shorts": return picked ? kitTint(sRGB("1E2A6E")) : nil
            case "Kit_ShortsBand": return picked ? kitTint(kitDerive(sRGB("1E2A6E"))) : nil
            case "Kit_Shoe": return picked ? kitTint(sRGB("9EE63A")) : nil
            default: return nil
            }
        })
        let headCentre = asset.manifest.headCentreY * asset.scale
        func stage(_ framing: String, dist: Float = 3.25) -> Stage {
            let st = Stage(cameraDistance: dist); st.frame(framing, cameraDistance: dist, headCentre: headCentre)
            return st
        }
        switch scenario {
        case "cloth":
            for framing in ["shirt", "collar", "shoe_side"] {
                let st = stage("shirt")
                let hero = MatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
                if framing == "collar" { st.cameraNode.camera?.fieldOfView = 24; st.cameraNode.position = SCNVector3(0.03, CGFloat(headCentre-0.15), 0.75); st.cameraNode.look(at:SCNVector3(0,CGFloat(headCentre-0.20),0)) }
                if framing == "shoe_side", let shoe=hero.childNode(withName:"Kit_Shoe_R",recursively:true), let g=shoe.geometry {
                    let bounds=g.boundingBox;let mid=SCNVector3((bounds.min.x+bounds.max.x)/2,(bounds.min.y+bounds.max.y)/2,(bounds.min.z+bounds.max.z)/2)
                    let t=shoe.convertPosition(mid,to:st.scene.rootNode)
                    st.cameraNode.camera?.fieldOfView=34;st.cameraNode.position=SCNVector3(t.x-CGFloat(0.65*asset.scale),t.y+CGFloat(0.04*asset.scale),t.z+CGFloat(0.08*asset.scale));st.cameraNode.look(at:t)
                }
                if dummyHex != nil, let top=hero.childNode(withName:"Kit_Top",recursively:true) {
                    let duplicate=top.clone();duplicate.name="Dummy_Polo_Duplicate";top.parent?.addChildNode(duplicate);top.removeFromParentNode()
                }
                png(st.snapshot(CGSize(width:1080,height:1080),device:device), "\(out)/cloth_\(sex)_\(framing)\(dummyHex == nil ? "" : "_dummy").png")
            }
        case "static":
            for framing in ["body", "shirt", "torso", "feet", "head"] {
                let st = stage(framing)
                let hero = MatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
                capture(st, bigSize ? CGSize(width: 1080, height: 1500) : CGSize(width: 720, height: 1000), "\(out)/static_\(sex)_\(framing)\(picked ? "_picked" : "").png", device)
            }
        case "dbg":
            // which part of the cloth look makes the patches: seam map off, weave normal off, both
            for variant in ["full", "single", "plain", "plainsingle"] {
                let st = stage("shirt")
                let hero = MatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
                hero.enumerateChildNodes { node, _ in
                    for m in node.geometry?.materials ?? [] where m.shaderModifiers?[.lightingModel] != nil {
                        if variant == "single" || variant == "plainsingle" { m.isDoubleSided = false }
                        if variant == "plain" || variant == "plainsingle" { m.diffuse.contents = CGColor(gray: 1, alpha: 1) }
                        if variant == "plain" || variant == "plainsingle" { if let v = m.value(forKey: "weaveParams") as? SCNVector4 { m.setValue(SCNVector4(v.x, v.y, 0, 0), forKey: "weaveParams") } }
                    }
                }
                capture(st, CGSize(width: 720, height: 1000), "\(out)/dbg_\(sex)_\(variant).png", device)
            }
        case "uvchecker":
            let st = stage("shirt")
            let hero = MatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
            hero.enumerateChildNodes { node, _ in
                for m in node.geometry?.materials ?? [] where m.shaderModifiers?[.lightingModel] != nil && m.value(forKey: "weaveParams") != nil {
                    m.shaderModifiers = [.surface: """
                    #pragma body
                    float2 g = floor(_surface.diffuseTexcoord * 40.0);
                    float c = fmod(g.x + g.y, 2.0);
                    _surface.diffuse = float4(float3(0.15 + 0.7 * c), 1.0);
                    _surface.emission = float4(0.0);
                    """]
                }
            }
            capture(st, CGSize(width: 720, height: 1000), "\(out)/uvchecker_\(sex).png", device)
        case "skinbump":
            // exaggerate the skin normal to check it is wired (x scale), then the real strength
            for (label, scale) in [("real", Float(1)), ("x6", Float(6))] {
                let st = stage("torso")
                let hero = MatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
                hero.enumerateChildNodes { node, _ in
                    for m in node.geometry?.materials ?? [] where m.name == "Skin" { if let v = m.value(forKey: "skinBump") as? SCNVector4 { m.setValue(SCNVector4(v.x * CGFloat(scale), v.y, 0, 0), forKey: "skinBump") } }
                }
                capture(st, CGSize(width: 720, height: 1000), "\(out)/skinbump_\(sex)_\(label).png", device)
            }
        case "lod":
            let st = stage("shirt")
            let hero = MatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
            hero.enumerateChildNodes { node, _ in
                for m in node.geometry?.materials ?? [] where m.shaderModifiers?[.lightingModel] != nil && m.value(forKey: "weaveParams") != nil {
                    m.shaderModifiers = [.surface: """
                    #pragma arguments
                    float4 weaveParams;
                    float4 clothTint;
                    #pragma body
                    float2 uv = _surface.diffuseTexcoord * weaveParams.x * 256.0;
                    float lod = log2(max(length(dfdx(uv)), length(dfdy(uv))) + 1e-6);
                    float3 c = float3(saturate(lod / 8.0), saturate(1.0 - fabs(lod - 4.0) / 4.0), saturate(1.0 - lod / 6.0));
                    _surface.diffuse = float4(c, 1.0);
                    _surface.emission = float4(0.0);
                    """]
                    m.setValue(SCNVector4(1,1,1,1), forKey: "clothTint")
                }
            }
            capture(st, CGSize(width: 720, height: 1000), "\(out)/lod_\(sex).png", device)
        case "shoedbg":
            for variant in ["full", "noseam", "noweave", "plain"] {
                let st = stage("feet")
                st.cameraNode.position = SCNVector3(0.30, 0.34, 0.95); st.cameraNode.look(at: SCNVector3(0, 0.10, 0))
                let hero = MatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
                hero.enumerateChildNodes { node, _ in
                    guard node.name?.hasPrefix("Kit_Shoe") == true || node.name?.hasPrefix("Kit_Sock") == true else { return }
                    for m in node.geometry?.materials ?? [] {
                        if variant == "noseam" || variant == "plain" { m.diffuse.contents = CGColor(gray: 1, alpha: 1) }
                        if variant == "noweave" || variant == "plain" { if let v = m.value(forKey: "weaveParams") as? SCNVector4 { m.setValue(SCNVector4(v.x, v.y, 0, 0), forKey: "weaveParams") } }
                    }
                }
                capture(st, CGSize(width: 900, height: 900), "\(out)/shoedbg_\(sex)_\(variant).png", device)
            }
        case "rig":
            // static vs rigged at ReadyIdle frame 0
            var imgs: [NSImage] = []
            for rigged in [false, true] {
                let st = stage("body")
                let hero = MatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
                if rigged, let rig = HeroRig(root: hero, asset: asset) { rig.attach() }
                let img = st.snapshot(CGSize(width: 720, height: 1000), device: device); imgs.append(img)
                png(img, "\(out)/rig_\(sex)_\(rigged ? "skinned" : "static").png")
            }
            func px(_ i: NSImage) -> [UInt8] { let r = NSBitmapImageRep(data: i.tiffRepresentation!)!; var o = [UInt8](); for y in 0..<r.pixelsHigh { for x in 0..<r.pixelsWide { let c = r.colorAt(x: x, y: y)!.usingColorSpace(.sRGB)!; o += [UInt8(c.redComponent * 255), UInt8(c.greenComponent * 255), UInt8(c.blueComponent * 255)] } }; return o }
            let a = px(imgs[0]), b = px(imgs[1]); var d = 0, over = 0
            for i in 0..<a.count { let e = abs(Int(a[i]) - Int(b[i])); d += e; if e > 24 { over += 1 } }
            print("\(sex): static vs skinned ReadyIdle[0]: mean abs diff \(Double(d) / Double(a.count)), channels > 24: \(over) of \(a.count)")
        case "serveend":
            let st = stage("body", dist: 3.6)
            let hero = MatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
            guard let rig = HeroRig(root: hero, asset: asset) else { print("no rig"); return }
            rig.attach()
            for (k, t) in stride(from: 2.4, through: 3.9, by: 0.1).enumerated() {
                rig.apply(MenuMotion.serveOnce, at: t)
                capture(st, CGSize(width: 480, height: 640), "\(out)/serveend_\(sex)_\(String(format: "%02d", k)).png", device)
            }
        case "ready", "serve":
            let st = stage("body", dist: scenario == "serve" ? 4.4 : 3.25)
            let hero = MatchHeroData.buildHero(asset, picks: picks); st.character.addChildNode(hero)
            guard let rig = HeroRig(root: hero, asset: asset) else { print("no rig"); return }
            rig.attach()
            let motion: MenuMotion = scenario == "serve" ? .serveOnce : .ready
            let times = scenario == "serve" ? stride(from: 0.0, through: 4.2, by: 0.3).map { $0 } : stride(from: 0.0, through: 2.2, by: 0.275).map { $0 }
            for (k, t) in times.enumerated() {
                rig.apply(motion, at: t)
                capture(st, CGSize(width: 480, height: 640), "\(out)/\(scenario)_\(sex)_\(String(format: "%02d", k)).png", device)
            }
        default: print("unknown scenario")
        }
    }
}

MainActor.assumeIsolated { runOriginal(); runCandidate() }
