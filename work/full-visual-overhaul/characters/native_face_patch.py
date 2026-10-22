from pathlib import Path
R=Path(__file__).resolve().parents[3]
p=R/'GolfArcade/Unity/MatchHeroSurfaces.swift';s=p.read_text()
s=s.replace('mat.name = sub.material   //','configurePaint(mat, role: sub.material)\n        mat.name = sub.material   //')
anchor='    // ---- TennisCloth: the kit and the racket grip'
code='''    private static func configurePaint(_ material: SCNMaterial, role: String) {
        guard role.hasPrefix("Face_") else { return }
        var group: Float = 0, lift: Float = 0.00015
        if role.contains("Sclera") { group=1;lift=0.00025 }
        else if ["Iris","Pupil","Limbal","Catch"].contains(where: {role.contains($0)}) { group=2;lift=role.contains("Catch") ? 0.0006:role.contains("Pupil") ? 0.0005:0.0004 }
        else if role.contains("LidLine") { group=3;lift=0.00045 }
        else if role.contains("Brow") { group=4;lift=role.contains("BrowSoft") ? 0.00015:0.00045 }
        material.setValue(SCNVector4(group,lift,0,0),forKey:"facePaint")
        material.setValue(SCNVector4(0,0,0,0),forKey:"facePerformance")
        material.setValue(SCNVector4(0,1,0,0),forKey:"faceUp")
        material.setValue(SCNVector4(1,0,0,0),forKey:"faceRight")
        var modifiers=material.shaderModifiers ?? [:];modifiers[.geometry]=faceGeometry;material.shaderModifiers=modifiers
    }
    /// Eye centres measured from the actual exported sclera geometry, in that face's own space.
    static func configureFace(_ root: SCNNode) {
        guard let node=root.childNode(withName:"Face",recursively:true),let geometry=node.geometry,
              let vertices=geometry.sources(for:.vertex).first else{return}
        func vertex(_ i:Int)->SIMD3<Float>{
            vertices.data.withUnsafeBytes { raw in
                let at=vertices.dataOffset+i*vertices.dataStride
                return SIMD3(raw.loadUnaligned(fromByteOffset:at,as:Float.self),raw.loadUnaligned(fromByteOffset:at+4,as:Float.self),raw.loadUnaligned(fromByteOffset:at+8,as:Float.self))
            }
        }
        var lo=[SIMD3<Float>(repeating:Float.greatestFiniteMagnitude),SIMD3<Float>(repeating:Float.greatestFiniteMagnitude)]
        var hi=lo.map {-$0};var found=[false,false]
        for (sub,material) in geometry.materials.enumerated() where material.name?.contains("Sclera") == true {
            let element=geometry.elements[sub]
            element.data.withUnsafeBytes { raw in
                for k in 0..<(element.primitiveCount*3) {
                    let i=element.bytesPerIndex==4 ? Int(raw.loadUnaligned(fromByteOffset:k*4,as:UInt32.self)):Int(raw.loadUnaligned(fromByteOffset:k*2,as:UInt16.self))
                    let v=vertex(i),side=v.x<0 ? 0:1;lo[side]=simd_min(lo[side],v);hi[side]=simd_max(hi[side],v);found[side]=true
                }
            }
        }
        guard found.allSatisfy({$0}) else{return}
        let left=(lo[0]+hi[0])*0.5,right=(lo[1]+hi[1])*0.5
        for material in geometry.materials {
            material.setValue(SCNVector4(left.x,left.y,left.z,0),forKey:"faceEyeL")
            material.setValue(SCNVector4(right.x,right.y,right.z,0),forKey:"faceEyeR")
        }
    }
    static func performFace(on root: SCNNode, blink: Float, gaze: SIMD2<Float> = .zero, brow: Float = 0) {
        guard let node=root.childNode(withName:"Face",recursively:true) else{return}
        for material in node.geometry?.materials ?? [] {
            guard let p=material.value(forKey:"facePaint") as? SCNVector4 else{continue}
            material.setValue(SCNVector4(p.x,p.y,CGFloat(max(0,min(1,blink))),CGFloat(max(-0.001,min(0.001,brow)))),forKey:"facePaint")
            material.setValue(SCNVector4(gaze.x,gaze.y,0,0),forKey:"facePerformance")
        }
    }
    static func performFace(on root: SCNNode, at time: Double, happy: Bool = false) {
        let interval=3.4,phase=time.truncatingRemainder(dividingBy:interval)
        let blink=phase<0.16 ? Float(sin(phase/0.16*Double.pi)):0
        performFace(on:root,blink:max(blink,happy ? 0.16:0),gaze:SIMD2(Float(sin(time*0.47))*0.00045,0),brow:happy ? 0.00065:0)
    }
    static let faceGeometry = """
    #pragma arguments
    float4 faceEyeL;
    float4 faceEyeR;
    float4 faceUp;
    float4 faceRight;
    float4 facePaint;
    float4 facePerformance;
    #pragma body
    float3 facePos=_geometry.position.xyz;
    if(facePaint.x>0.5){
        float3 eye=dot(facePos-(faceEyeL.xyz+faceEyeR.xyz)*0.5,faceRight.xyz)<0.0 ? faceEyeL.xyz:faceEyeR.xyz;
        if(facePaint.x<3.5){
            float eyeHeight=dot(facePos-eye,faceUp.xyz);
            facePos-=faceUp.xyz*eyeHeight*facePaint.z;
            if(facePaint.x>1.5 && facePaint.x<2.5)facePos+=(faceRight.xyz*facePerformance.x+faceUp.xyz*facePerformance.y)*(1.0-facePaint.z);
        }else facePos+=faceUp.xyz*facePaint.w;
    }
    facePos+=_geometry.normal.xyz*facePaint.y;
    _geometry.position.xyz=facePos;
    """

'''
s=s.replace(anchor,code+anchor)
# Remove unused failed surface modifier; saturation is applied to the native tint in Swift.
start=s.index('    static let athleteSurfaceBody');end=s.index('    static let athleteLighting',start);s=s[:start]+s[end:]
s=s.replace('m.diffuse.contents = flatColour(tint)\n        // Same broad', 'let lum=simd_dot(tint,SIMD3<Float>(0.2126,0.7152,0.0722))\n        m.diffuse.contents = flatColour(SIMD3<Float>(repeating:lum)+(tint-SIMD3<Float>(repeating:lum))*look.saturation)\n        // Same broad')
p.write_text(s)
p=R/'GolfArcade/Unity/MatchHeroData.swift';s=p.read_text().replace('        if picks.leftHanded { root.scale.x = -root.scale.x }','        MatchHeroSurfaces.configureFace(root)\n        if picks.leftHanded { root.scale.x = -root.scale.x }');p.write_text(s)
p=R/'GolfArcade/Unity/MatchHeroMotion.swift';s=p.read_text().replace('func apply(_ motion: MenuMotion, at time: Double) { apply(motion.pose(data, at: time)) }','''func apply(_ motion: MenuMotion, at time: Double) {
        apply(motion.pose(data, at: time))
        let happy: Bool
        if case .clipOnce(let id) = motion.kind { happy = ["celebratePoint","matchWin","hitPerfect","introWave"].contains(id) } else { happy = false }
        MatchHeroSurfaces.performFace(on:root,at:time,happy:happy)
    }''');p.write_text(s)
