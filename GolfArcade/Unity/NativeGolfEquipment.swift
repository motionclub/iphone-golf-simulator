import Foundation
import UIKit
import SceneKit
import simd

/// The four actual golf meshes, exported from blender/scripts/golf_clubs.py.
/// Metres; origin is the original grip socket. Butt +Y, shaft down -Y, toe +X,
/// striking face +Z. Keep this root at the hand socket before applying a display pose.
@MainActor enum NativeGolfEquipment {
    struct Finish: Decodable {
        let name: String, color: [Float], metallic: Float, roughness: Float
        let texture: String?
        let indices: [UInt32]
    }
    struct Asset: Decodable {
        let id: String, positions: [Float], normals: [Float], materials: [Finish]
        let soleY: Float, loftDegrees: Float
        let uvs: [Float]?
    }
    static var locate: (_ name: String, _ ext: String) -> URL? = { name, ext in
        Bundle.main.url(forResource: name, withExtension: ext)
    }
    private static var assets: [String: Asset] = [:]
    static func asset(_ id: String) -> Asset? {
        let families = ["Driver", "Iron", "Wedge", "Putter"]
        var keys = families
        for style in ["hockey", "slugger", "balloon", "candy"] {
            for family in families { keys.append(style + "_" + family) }
        }
        let key = keys.first { $0.caseInsensitiveCompare(id) == .orderedSame }
        guard let key else { return nil }
        if let a = assets[key] { return a }
        guard let u = locate("NativeGolfEquipment_" + key, "json"), let d = try? Data(contentsOf: u),
              let a = try? JSONDecoder().decode(Asset.self, from: d),
              a.positions.count == a.normals.count, a.positions.count % 3 == 0 else { return nil }
        assets[key] = a; return a
    }
    /// Returns a fresh independently tintable node. A reward tint preserves the authored
    /// roughness/metal identity; rubber, scorelines and white alignment marks stay legible.
    static func make(_ id: String, tint: SIMD3<Float>? = nil) -> SCNNode? {
        guard let a = asset(id) else { return nil }
        func source(_ values: [Float], _ semantic: SCNGeometrySource.Semantic) -> SCNGeometrySource {
            let data = values.withUnsafeBytes { Data($0) }
            return SCNGeometrySource(data: data, semantic: semantic, vectorCount: values.count / 3,
                usesFloatComponents: true, componentsPerVector: 3, bytesPerComponent: 4, dataOffset: 0, dataStride: 12)
        }
        let count = a.positions.count / 3
        var elements: [SCNGeometryElement] = [], materials: [SCNMaterial] = []
        for finish in a.materials {
            guard finish.indices.count % 3 == 0, finish.indices.allSatisfy({ Int($0) < count }), finish.color.count == 3 else { return nil }
            let data = finish.indices.withUnsafeBytes { Data($0) }
            elements.append(SCNGeometryElement(data: data, primitiveType: .triangles,
                primitiveCount: finish.indices.count / 3, bytesPerIndex: 4))
            let m = SCNMaterial(); m.name = "CLUB " + finish.name; m.lightingModel = .physicallyBased
            let authored = SIMD3<Float>(finish.color[0], finish.color[1], finish.color[2])
            let c = ["grip", "groove", "white"].contains(finish.name) ? authored : (tint ?? authored)
            m.diffuse.contents = CGColor(red: CGFloat(c.x), green: CGFloat(c.y), blue: CGFloat(c.z), alpha: 1)
            m.metalness.contents = finish.metallic; m.roughness.contents = finish.roughness
            if let texture = finish.texture, !texture.isEmpty,
               let url = locate("Cosmetic_" + texture, "png") {
                m.multiply.contents = m.diffuse.contents; m.diffuse.contents = url
                m.diffuse.wrapS = .repeat; m.diffuse.wrapT = .repeat
            }
            m.isDoubleSided = false; materials.append(m)
        }
        var sources = [source(a.positions, .vertex), source(a.normals, .normal)]
        if let uv = a.uvs, uv.count == count * 2 {
            sources.append(SCNGeometrySource(data: uv.withUnsafeBytes { Data($0) }, semantic: .texcoord, vectorCount: count,
                usesFloatComponents: true, componentsPerVector: 2, bytesPerComponent: 4, dataOffset: 0, dataStride: 8))
        }
        let geometry = SCNGeometry(sources: sources, elements: elements)
        geometry.materials = materials
        let node = SCNNode(geometry: geometry); node.name = "nativeGolfEquipment_" + a.id
        node.setValue(a.soleY, forKey: "clubSoleY"); node.setValue(a.loftDegrees, forKey: "clubLoftDegrees")
        return node
    }
}

/// Original equipment is shared with Unity's bound FBXs, with the same grip-local geometry.
@MainActor enum PartyCosmeticPreview {
    static func clubAsset(_ id: String) -> String {
        let style = ["party.hockey", "party.slugger", "party.balloon", "party.candy"].contains(id) ? String(id.dropFirst(6)) : nil
        return style.map { $0 + "_Iron" } ?? "Iron"
    }
    static func extraColours(_ id: String) -> (String, String)? {
        switch id {
        case "extra.mint": return ("23C8A5", "173247")
        case "extra.neon": return ("7748CB", "EFFF62")
        case "extra.caramel": return ("BA783F", "FFF0D6")
        default: return nil
        }
    }
    static func ballMaterial(_ id: String) -> SCNMaterial {
        let m = SCNMaterial(); m.lightingModel = .physicallyBased; m.roughness.contents = 0.3
        if ["ball.orbit", "ball.melon", "ball.checker", "ball.sunset"].contains(id),
           let u = NativeGolfEquipment.locate(id.replacingOccurrences(of: ".", with: "_"), "png") {
            m.diffuse.contents = u
        } else { m.diffuse.contents = CGColor(gray: 0.97, alpha: 1) }
        return m
    }
    private static func snapshot(_ node: SCNNode, target: SIMD3<Float>, span: Double) -> UIImage? {
        let scene = SCNScene(); scene.rootNode.addChildNode(node)
        let camera = SCNNode(); camera.camera = SCNCamera(); camera.camera?.usesOrthographicProjection = true
        camera.camera?.orthographicScale = span; camera.position = SCNVector3(target.x, target.y, target.z + 3)
        camera.look(at: SCNVector3(target)); scene.rootNode.addChildNode(camera)
        let key = SCNNode(); key.light = SCNLight(); key.light?.type = .omni; key.light?.intensity = 1100
        key.position = SCNVector3(-1, 2, 3); scene.rootNode.addChildNode(key)
        let fill = SCNNode(); fill.light = SCNLight(); fill.light?.type = .ambient; fill.light?.intensity = 650; scene.rootNode.addChildNode(fill)
        scene.background.contents = CGColor(red: 0.88, green: 0.94, blue: 0.92, alpha: 1)
        let r = SCNRenderer(device: nil, options: nil); r.scene = scene; r.pointOfView = camera
        return r.snapshot(atTime: 0, with: CGSize(width: 240, height: 240), antialiasingMode: .multisampling4X)
    }
    static func clubThumbnail(_ id: String) -> UIImage? {
        guard let node = NativeGolfEquipment.make(clubAsset(id)) else { return nil }
        node.eulerAngles.z = -.pi / 7
        return snapshot(node, target: SIMD3(-0.16, -0.43, 0), span: 0.65)
    }
    static func ballThumbnail(_ id: String) -> UIImage? {
        let n = SCNNode(geometry: SCNSphere(radius: 0.28)); n.geometry?.materials = [ballMaterial(id)]
        return snapshot(n, target: .zero, span: 0.38)
    }
}
