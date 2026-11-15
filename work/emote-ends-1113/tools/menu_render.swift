import SceneKit
import AppKit
import Metal
import simd

// Menu line-up mock renderer: several real exported heroes in one SceneKit scene, transparent background, shadow-only floor,
// bright studio rig (key + fill + two rims). usage: lineup_render <spec.json>   or   lineup_render --clips
let repo = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
let assetsDir = repo + "/GolfArcade/Unity/CharacterAssets"

struct HeroSpec: Decodable {
    var female: Bool; var kit: String          // tennis | golf | bowling
    var skin: String?; var shirt: String?; var shorts: String?; var shoes: String?
    var clip: String?; var t: Double?; var racketBack: Bool?; var menu: Bool?; var empty: Bool?
    var x: Float; var z: Float; var yaw: Float  // degrees, 0 = facing camera
}
struct LightSpec: Decodable { var ray: [Float]; var color: [Float]; var intensity: Float; var shadow: Bool?; var shadowAlpha: Float? }
struct Spec: Decodable {
    var out: String; var width: Int; var height: Int
    var cam: [Float]; var look: [Float]; var fov: Float
    var key: Float?; var fill: Float?; var rim: Float?; var ambient: Float?; var exposure: Float?
    var heroes: [HeroSpec]; var shadowPass: Bool?; var rimL: String?; var rimR: String?; var pads: [[Float]]?; var padColor: String?; var padRing: String?; var heroesOff: Bool?; var lights: [LightSpec]?; var ambientColor: [Float]?
}

func png(_ image: NSImage, _ path: String) {
    guard let tiff = image.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff), let data = rep.representation(using: .png, properties: [:]) else { return }
    try? data.write(to: URL(fileURLWithPath: path))
}
func sRGB(_ hex: String) -> SIMD3<Float> {
    let n = UInt32(hex, radix: 16) ?? 0xFFFFFF
    return SIMD3(Float((n >> 16) & 255) / 255, Float((n >> 8) & 255) / 255, Float(n & 255) / 255)
}
func kitTint(_ p: SIMD3<Float>) -> SIMD3<Float> { SIMD3(max(0.93 * p.x, 0.035), max(0.93 * p.y, 0.035), max(0.93 * p.z, 0.0401)) }
func kitDerive(_ p: SIMD3<Float>) -> SIMD3<Float> { let l = 0.2126 * p.x + 0.7152 * p.y + 0.0722 * p.z; return l >= 0.5 ? p * 0.65 : p + (SIMD3<Float>(repeating: 1) - p) * 0.35 }

@MainActor func run() {
    MatchHeroData.locate = { name, ext in
        let u = URL(fileURLWithPath: assetsDir + "/" + name + "." + ext); return FileManager.default.fileExists(atPath: u.path) ? u : nil
    }
    let args = CommandLine.arguments
    if args.count > 1, args[1] == "--clips" {
        for (g, b) in [(false, false), (true, false), (false, true)] { for f in [false, true] {
            guard let a = MatchHeroData.asset(female: f, golf: g, distance: !g && !b, bowling: b), let r = a.rig() else { print("no asset g\(g) b\(b) f\(f)"); continue }
            print("golf=\(g) bowling=\(b) female=\(f):", r.clips.map { "\($0.key)(\(String(format: "%.1f", $0.value.length)))" }.sorted().joined(separator: " "))
        } }
        return
    }
    guard args.count > 1, let d = try? Data(contentsOf: URL(fileURLWithPath: args[1])), let spec = try? JSONDecoder().decode(Spec.self, from: d) else { print("bad spec"); return }
    if let e = spec.exposure { MatchHeroSurfaces.sceneExposure = e }
    let scene = SCNScene()
    scene.background.contents = NSColor.clear
    let cam = SCNNode(); cam.camera = SCNCamera(); cam.camera!.fieldOfView = CGFloat(spec.fov); cam.camera!.zNear = 0.05
    cam.position = SCNVector3(CGFloat(spec.cam[0]), CGFloat(spec.cam[1]), CGFloat(spec.cam[2])); cam.look(at: SCNVector3(CGFloat(spec.look[0]), CGFloat(spec.look[1]), CGFloat(spec.look[2])))
    scene.rootNode.addChildNode(cam)
    func light(_ intensity: Float, _ c: NSColor, elevation: Float, azimuth: Float, shadow: Bool = false) {
        let node = SCNNode(), l = SCNLight(); l.type = .directional; l.intensity = CGFloat(intensity); l.color = c
        if shadow {
            l.castsShadow = true; l.shadowRadius = 8; l.shadowSampleCount = 16; l.shadowMode = .deferred; l.shadowMapSize = CGSize(width: 4096, height: 4096)
            l.shadowColor = NSColor(red: 0.05, green: 0.07, blue: 0.16, alpha: 0.55); l.orthographicScale = 5
        }
        node.light = l
        let e = elevation * .pi / 180, a = azimuth * .pi / 180
        node.position = SCNVector3(CGFloat(-sin(a) * cos(e) * 8), CGFloat(sin(e) * 8), CGFloat(cos(a) * cos(e) * 8))
        node.look(at: SCNVector3(0, 0.8, 0)); scene.rootNode.addChildNode(node)
    }
    // studio rig: soft warm-neutral key from camera-left-high, cool fill camera-right, two back rims, bright neutral ambient
    func ns(_ h: String?, _ d: NSColor) -> NSColor { guard let h else { return d }; let c = sRGB(h); return NSColor(red: CGFloat(c.x), green: CGFloat(c.y), blue: CGFloat(c.z), alpha: 1) }
    if spec.lights == nil {
    light(spec.key ?? 1200, NSColor(red: 1, green: 0.97, blue: 0.93, alpha: 1), elevation: 38, azimuth: 30, shadow: true)
    light(spec.fill ?? 520, NSColor(red: 0.88, green: 0.93, blue: 1, alpha: 1), elevation: 15, azimuth: -45)
    light(spec.rim ?? 650, ns(spec.rimL, NSColor(red: 0.85, green: 0.92, blue: 1, alpha: 1)), elevation: 30, azimuth: 150)
    light(spec.rim ?? 650, ns(spec.rimR, NSColor(red: 1, green: 0.93, blue: 0.85, alpha: 1)), elevation: 30, azimuth: -150)
    }
    // venue-matched rig: each light is a world-space ray direction (the way the light travels), linear-ish colour, intensity in SceneKit units
    for L in spec.lights ?? [] {
        let node = SCNNode(), l = SCNLight(); l.type = .directional; l.intensity = CGFloat(L.intensity)
        l.color = NSColor(red: CGFloat(L.color[0]), green: CGFloat(L.color[1]), blue: CGFloat(L.color[2]), alpha: 1)
        if L.shadow == true {
            l.castsShadow = true; l.shadowRadius = 6; l.shadowSampleCount = 16; l.shadowMode = .deferred; l.shadowMapSize = CGSize(width: 4096, height: 4096)
            l.shadowColor = NSColor(red: 0.04, green: 0.05, blue: 0.12, alpha: CGFloat(L.shadowAlpha ?? 0.6)); l.orthographicScale = 5
        }
        node.light = l
        let d = simd_normalize(SIMD3<Float>(L.ray[0], L.ray[1], L.ray[2]))
        node.position = SCNVector3(CGFloat(-d.x * 8), CGFloat(0.8 - d.y * 8), CGFloat(-d.z * 8)); node.look(at: SCNVector3(0, 0.8, 0)); scene.rootNode.addChildNode(node)
    }
    // stage pads [x, z, radius]: a low disc with a glowing ring, heroes stand on top
    let padH: Float = 0.07
    for p in spec.pads ?? [] {
        let disc = SCNCylinder(radius: CGFloat(p[2]), height: CGFloat(padH)); disc.radialSegmentCount = 96
        let dm = SCNMaterial(); dm.lightingModel = .physicallyBased; dm.diffuse.contents = ns(spec.padColor, NSColor(red: 0.07, green: 0.13, blue: 0.40, alpha: 1)); dm.roughness.contents = 0.35; dm.metalness.contents = 0.0
        disc.materials = [dm]
        let dn = SCNNode(geometry: disc); dn.position = SCNVector3(CGFloat(p[0]), CGFloat(padH / 2), CGFloat(p[1])); scene.rootNode.addChildNode(dn)
        let ring = SCNTorus(ringRadius: CGFloat(p[2]) - 0.02, pipeRadius: 0.018); ring.ringSegmentCount = 120
        let rm = SCNMaterial(); rm.lightingModel = .constant; rm.diffuse.contents = ns(spec.padRing, NSColor(red: 0.95, green: 0.69, blue: 0.07, alpha: 1)); ring.materials = [rm]
        let rn = SCNNode(geometry: ring); rn.position = SCNVector3(CGFloat(p[0]), CGFloat(padH), CGFloat(p[1])); scene.rootNode.addChildNode(rn)
    }
    let lift: Float = (spec.pads?.isEmpty ?? true) ? 0 : padH
    let amb = SCNNode(); amb.light = SCNLight(); amb.light!.type = .ambient; amb.light!.intensity = CGFloat(spec.ambient ?? 300)
    if let c = spec.ambientColor { amb.light!.color = NSColor(red: CGFloat(c[0]), green: CGFloat(c[1]), blue: CGFloat(c[2]), alpha: 1) } else { amb.light!.color = NSColor(red: 0.92, green: 0.94, blue: 1, alpha: 1) }; scene.rootNode.addChildNode(amb)
    // shadow catcher
    let floor = SCNFloor(); floor.reflectivity = 0
    let fm = SCNMaterial(); if spec.shadowPass == true { fm.lightingModel = .lambert; scene.background.contents = NSColor.white } else { fm.lightingModel = .shadowOnly }; fm.diffuse.contents = NSColor.white; floor.materials = [fm]
    let fn = SCNNode(geometry: floor); scene.rootNode.addChildNode(fn)

    for h in (spec.heroesOff == true ? [] : spec.heroes) {
        guard let asset = MatchHeroData.asset(female: h.female, golf: h.kit == "golf", distance: h.kit == "tennis", bowling: h.kit == "bowling") else { print("no asset", h.kit); continue }
        let picks = MatchHeroData.Picks(colour: { name in
            switch name {
            case "Skin": return h.skin.map(sRGB)
            case "Kit_Shirt": return h.shirt.map { kitTint(sRGB($0)) }
            case "Kit_ShirtTrim": return h.shirt.map { kitTint(kitDerive(sRGB($0))) }
            case "Kit_Shorts": return h.shorts.map { kitTint(sRGB($0)) }
            case "Kit_ShortsBand": return h.shorts.map { kitTint(kitDerive(sRGB($0))) }
            case "Kit_Shoe": return h.shoes.map { kitTint(sRGB($0)) }
            default: return nil
            }
        })
        let hero = MatchHeroData.buildHero(asset, picks: picks)
        hero.eulerAngles.y = .pi + CGFloat(h.yaw * .pi / 180)
        let holder = SCNNode(); holder.position = SCNVector3(CGFloat(h.x), CGFloat(lift), CGFloat(h.z)); holder.addChildNode(hero)
        scene.rootNode.addChildNode(holder)
        if h.kit == "bowling" { hero.childNode(withName: MatchHeroData.racketName, recursively: true)?.isHidden = true }
        if let rig = HeroRig(root: hero, asset: asset) {
            rig.attach(); if h.racketBack == true { rig.racketOnBack = true }
            if let id = h.clip {
                if h.menu == true {
                    // the phone menu's emote exactly as CharacterModelPreview.playEmote builds it (racket on the back)
                    var m = MenuMotion(kind: .clipOnce(id), lead: 0, fadeIn: 0.15, fadeOut: 0.25, freezeIdle: true)
                    m.idle = MenuMotion.relaxed.idle
                    if h.empty == true { m.emptyHands = true; m.fadeIn = 0.2; m.fadeOut = 0.35 }
                    rig.apply(m, at: h.t ?? 0)
                    if let w = rig.data.emptyHandWindow(id) { print("window", id, w.start, w.end, "settled", m.settledAfter(rig.data)) }
                } else if let clip = rig.data.clips[id] {
                    rig.apply(clip.pose(at: h.t ?? 0, loop: false))
                } else { print("no clip", id) }
            }
        }
    }
    let r = SCNRenderer(device: MTLCreateSystemDefaultDevice()!, options: nil); r.scene = scene; r.pointOfView = cam
    png(r.snapshot(atTime: 0, with: CGSize(width: spec.width, height: spec.height), antialiasingMode: .multisampling4X), spec.out)
    print("wrote", spec.out)
}
@main struct LineupRender { static func main() { MainActor.assumeIsolated { run() } } }
