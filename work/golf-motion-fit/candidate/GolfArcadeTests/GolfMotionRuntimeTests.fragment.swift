
import SceneKit
import simd

@MainActor final class GolfMotionRuntimeTests: XCTestCase {
    func testAllGolfClipsAt120HzKeepHandsOnTheSharedHandle() throws {
        var checked=0, maximum:Float=0
        for female in [false,true] {
            let asset=try XCTUnwrap(MatchHero.asset(female:female,golf:true))
            XCTAssertTrue(asset.manifest.isGolf)
            let data=try XCTUnwrap(asset.rig())
            XCTAssertEqual(data.info.bones.count,53)
            XCTAssertEqual(data.info.clips.count,48)
            let track=data.boneCount+(try XCTUnwrap(data.info.rigid.firstIndex(of:"GolfHandle")))
            for info in data.info.clips {
                let left=info.handedness == "left"
                let clip=try XCTUnwrap(data.clip(info.id,left:left)),coeff=try XCTUnwrap(data.coefficients(clip)),anchors=try XCTUnwrap(data.golfAnchors(left:left))
                XCTAssertEqual(info.fps,120);XCTAssertEqual(clip.frames,Int((clip.length*120).rounded())+1)
                for f in 0..<clip.frames {
                    let pose=clip.pose(at:Double(f)/120,loop:false)
                    for row in pose { XCTAssertTrue(row.t.x.isFinite && row.t.y.isFinite && row.t.z.isFinite && row.s.x.isFinite && row.s.y.isFinite && row.s.z.isFinite);XCTAssertEqual(simd_length(row.q.vector),1,accuracy:0.00001) }
                    for (i,side) in ["Left","Right"].enumerated() {
                        if (coeff.trailRelease?[f] ?? 0)>0.000001 && side==(left ? "Left":"Right") { continue }
                        let hand=try XCTUnwrap(data.info.bones.firstIndex(of:side+"Hand"));let target=pose[track].matrix*SIMD4(anchors[i],1)
                        let drift=simd_distance(pose[hand].t,SIMD3(target.x,target.y,target.z));maximum=max(maximum,drift)
                        XCTAssertLessThan(drift,0.001,"\(info.id) frame \(f) \(side)")
                    }
                };checked+=1
            }
        }
        XCTAssertEqual(checked,96);print("GOLF_NATIVE_120HZ clips=\(checked) maximumDriftM=\(maximum)")
    }
    func testSportSwitchingRebuildsTheSamePlayerAndPreservesExplicitHandedness() throws {
        for female in [false,true] { for left in [false,true] {
            var player=Player(name:"Golf check",colorIndex:0);player.standardFemale=female;player.handedness=left ? .left:.right
            let c=CharacterModelPreview.Coordinator()
            for _ in 0..<3 {
                c.update(player,sport:.golf);let golf=try XCTUnwrap(c.hero)
                XCTAssertEqual(golf.value(forKey:"heroGolf") as? Bool,true);XCTAssertEqual(golf.value(forKey:"heroLeft") as? Bool,left)
                XCTAssertGreaterThan(golf.scale.x,0,"explicit left-hand clip must not be mirrored at runtime")
                XCTAssertNotNil(golf.childNode(withName:"Golf_Polo",recursively:true));XCTAssertNil(golf.childNode(withName:"Kit_Top",recursively:true))
                XCTAssertNotNil(golf.childNode(withName:"GolfHandle",recursively:true));XCTAssertEqual(golf.childNode(withName:left ? "Golf_Glove_Right":"Golf_Glove_Left",recursively:true)?.isHidden,false)
                c.update(player,sport:.tennis);let tennis=try XCTUnwrap(c.hero);XCTAssertFalse(golf === tennis)
                XCTAssertEqual(tennis.value(forKey:"heroGolf") as? Bool,false);XCTAssertNotNil(tennis.childNode(withName:"Kit_Top",recursively:true))
                XCTAssertNil(tennis.childNode(withName:"Golf_Polo",recursively:true))
            }
        } }
    }
    func testEveryNativeGolfTransitionAt120HzKeepsTheGrip() throws {
        var checked=0,maximum:Float=0
        for female in [false,true] { for left in [false,true] {
            var player=Player(name:"Transitions",colorIndex:0);player.standardFemale=female;player.handedness=left ? .left:.right
            let c=CharacterModelPreview.Coordinator();c.update(player,sport:.golf)
            let root=try XCTUnwrap(c.hero),asset=try XCTUnwrap(MatchHero.asset(female:female,golf:true)),rig=try XCTUnwrap(HeroRig(root:root,asset:asset));rig.attach()
            let entries=rig.data.info.clips.filter{$0.handedness==(left ? "left":"right")},anchors=try XCTUnwrap(rig.data.golfAnchors(left:left))
            for from in entries { for to in entries {
                let a=try XCTUnwrap(rig.data.clip(from.id,left:left)),b=try XCTUnwrap(rig.data.clip(to.id,left:left))
                let ca=try XCTUnwrap(rig.data.coefficients(a)),cb=try XCTUnwrap(rig.data.coefficients(b)),fa=min(a.frames-1,Int(a.length*60))
                for f in 0...24 {
                    let x=min(Float(f)/120/0.18,1),w=x*x*(3-2*x);rig.previewGolfTransition(a,b,weight:w)
                    let released=(ca.trailRelease?[fa] ?? 0)*(1-w)+(cb.trailRelease?.first ?? 0)*w
                    let handle=try XCTUnwrap(root.childNode(withName:"GolfHandle",recursively:true))
                    for (i,side) in ["Left","Right"].enumerated() {
                        if released>0.000001 && side==(left ? "Left":"Right") { continue }
                        let hand=try XCTUnwrap(rig.boneNodes.first(where:{$0.name==side+"Hand"}))
                        let target=handle.simdTransform*SIMD4(anchors[i],1),drift=simd_distance(hand.simdPosition,SIMD3(target.x,target.y,target.z));maximum=max(maximum,drift)
                        XCTAssertLessThan(drift,0.001,"Transition \(from.id) → \(to.id), frame \(f)")
                    }
                };checked+=1
            } }
        } }
        XCTAssertEqual(checked,2304);print("GOLF_NATIVE_TRANSITIONS count=\(checked) maximumDriftM=\(maximum)")
    }
    func testGolfMorphTargetsAreFiniteDeltasAndMaterialsKeepTheirRoles() throws {
        for female in [false,true] {
            let asset=try XCTUnwrap(MatchHero.asset(female:female,golf:true)),rig=try XCTUnwrap(asset.rig())
            for part in rig.skinned { for geometry in part.correctives.values { for source in geometry.sources(for:.vertex) {
                let count=source.vectorCount*3;var values=[Float](repeating:0,count:count);values.withUnsafeMutableBytes{$0.copyBytes(from:source.data.prefix(count*4))}
                for i in stride(from:0,to:count,by:3) {let v=SIMD3(values[i],values[i+1],values[i+2]);XCTAssertTrue(v.x.isFinite && v.y.isFinite && v.z.isFinite);XCTAssertLessThan(simd_length(v),0.081)}
            } } }
            for part in asset.manifest.parts { for sub in part.submeshes {
                if part.name.contains("Hair") { XCTAssertEqual(sub.look?.bumpMap,"") }
            } }
        }
    }
    func testRenderGolfRuntimeProofsWithMetal() throws {
        let directory=URL(fileURLWithPath:#filePath).deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("work/golf-motion-fit/proof-native")
        try FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true)
        for female in [false,true] { for left in [false,true] {
            var player=Player(name:"Proof",colorIndex:0);player.standardFemale=female;player.handedness=left ? .left:.right;player.setSkin(0.35)
            let c=CharacterModelPreview.Coordinator(cameraDistance:4.3);c.update(player,sport:.golf)
            let root=try XCTUnwrap(c.hero),asset=try XCTUnwrap(MatchHero.asset(female:female,golf:true)),rig=try XCTUnwrap(HeroRig(root:root,asset:asset));rig.attach()
            let sex=female ? "Female":"Male",hand=left ? "LH":"RH",clip=try XCTUnwrap(rig.data.clip("Drive_\(sex)_\(hand)",left:left))
            let renderer=SCNRenderer(device:nil,options:nil);renderer.scene=c.scene;renderer.pointOfView=c.camera
            for (stage,time) in [("Address",0.0),("Top",Double(clip.info.backswingTop ?? 0)),("Impact",Double(clip.info.impact ?? 0)),("Finish",clip.length)] {
                rig.previewGolfClip(clip,at:time)
                for angle in stride(from:0,to:360,by:45) { root.eulerAngles.y=Float(angle)*Float.pi/180
                    let png=try XCTUnwrap(renderer.snapshot(atTime:0,with:CGSize(width:480,height:640),antialiasingMode:.multisampling4X).pngData())
                    try png.write(to:directory.appendingPathComponent("\(sex)_\(hand)_\(stage)_\(angle).png"))
                }
            }
        } }
    }
    func testThumbnailKeysIncludeSportAndHandEvenForTheSameItem() throws {
        var p=Player(name:"Thumb",colorIndex:0)
        let item=try XCTUnwrap(LockerCatalog.items(sport:.golf,slot:.shoes).first)
        let rh=LockerThumbs.key(p,slot:.shoes,item:item,sport:.golf)
        XCTAssertNotEqual(rh,LockerThumbs.key(p,slot:.shoes,item:item,sport:.tennis))
        p.handedness = .left
        XCTAssertNotEqual(rh,LockerThumbs.key(p,slot:.shoes,item:item,sport:.golf))
    }
}
