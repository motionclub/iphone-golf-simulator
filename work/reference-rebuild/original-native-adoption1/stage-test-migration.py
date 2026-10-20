"""Work-only exact accepted contract migration. Legacy branches remain strict."""
from pathlib import Path
import difflib,json,hashlib
TASK=Path(__file__).resolve().parent;REPO=TASK.parents[2];patch=[];rows=[]
def stage(name,transform):
 path='GolfArcadeTests/'+name;source=REPO/path;old=source.read_text();new=transform(old);assert new!=old
 target=TASK/path;target.parent.mkdir(exist_ok=True);target.write_text(new)
 patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=path,tofile=path))
 rows.append({'file':path,'source_sha256':hashlib.sha256(old.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(new.encode()).hexdigest()})
def locker(s):
 s=s.replace('body.vertexCount, female ? 23683 : 33196','body.vertexCount, (body.submeshes.first?.look?.skinPigmentUV ?? 0) > 0.5 ? (female ? 23230 : 33705) : (female ? 23683 : 33196)')
 s=s.replace('bodyGeometry.sources(for: .vertex).first?.vectorCount, female ? 23683 : 33196','bodyGeometry.sources(for: .vertex).first?.vectorCount, (MatchHeroSurfaces.made(bodyGeometry.materials[0])?.look?.skinPigmentUV ?? 0) > 0.5 ? (female ? 23230 : 33705) : (female ? 23683 : 33196)')
 old='for material in bodyGeometry.materials { assertColour(try XCTUnwrap(material.diffuse.contents as? UIColor), hex: p.skinHex, "skin pick on the body") }'
 new='''for material in bodyGeometry.materials {
                let made = try XCTUnwrap(MatchHeroSurfaces.made(material))
                if (made.look?.skinPigmentUV ?? 0) > 0.5 {
                    let c = made.colour
                    assertColour(UIColor(red: CGFloat(c.x), green: CGFloat(c.y), blue: CGFloat(c.z), alpha: 1), hex: p.skinHex, "relative pigment retains the selected skin tint")
                    XCTAssertTrue(made.look?.baseMapLinear == true)
                    XCTAssertEqual(made.look?.baseMap, "MatchHero_OriginalSeam_RelativeSkinPigment")
                    XCTAssertNotNil(material.value(forKey: "heroTint"))
                } else {
                    assertColour(try XCTUnwrap(material.diffuse.contents as? UIColor), hex: p.skinHex, "legacy skin pick on the body")
                }
            }'''
 assert old in s;s=s.replace(old,new);return s
def mirror(s):
 s=s.replace('func testOnlyTheKitHasUVsInTheExport()', 'func testTextureChannelsMatchTheirDeclaredMaterialRole()')
 start=s.index('    /// "Export UVs for kit parts only"');end=s.index('    func testTextureChannels',start)
 s=s[:start]+'''    /// OriginalSeam uses Body UV0 plus bind xy/z, and Face eye UV0.
    /// Legacy exports retain exactly their previous two bind channels / rigid Face.
'''+s[end:]
 old='''                    XCTAssertTrue((part.uvOffset ?? -1) < 0, "the body has no UVs"); XCTAssertGreaterThanOrEqual(part.bindPositionOffset ?? -1, 0, "the body carries its bind pose"); XCTAssertEqual(channels, 2)
                default:'''
 new='''                    let pigment = (part.submeshes.first?.look?.skinPigmentUV ?? 0) > 0.5
                    XCTAssertEqual((part.uvOffset ?? -1) >= 0, pigment, "UV0 exists exactly when relative pigment uses it")
                    XCTAssertGreaterThanOrEqual(part.bindPositionOffset ?? -1, 0, "the body carries its bind pose")
                    XCTAssertEqual(channels, pigment ? 3 : 2)
                case "face":
                    let anatomical = part.submeshes.allSatisfy { $0.look?.anatomicalFace == true }
                    XCTAssertEqual((part.uvOffset ?? -1) >= 0, anatomical)
                    XCTAssertTrue((part.bindPositionOffset ?? -1) < 0)
                    XCTAssertEqual(channels, anatomical ? 1 : 0)
                default:'''
 assert old in s;s=s.replace(old,new)
 s=s.replace('let url = repo.appendingPathComponent("work/locker-mirror/data/MatchHero_\\(female ? "Female" : "Male")_golden.json")', 'let fixtureDir = ProcessInfo.processInfo.environment["VISUAL_GOLDEN_DIR"].map { URL(fileURLWithPath: $0) } ?? repo.appendingPathComponent("work/locker-mirror/data")\n            let url = fixtureDir.appendingPathComponent("MatchHero_\\(female ? "Female" : "Male")_golden.json")')
 s=s.replace('let file = repo.appendingPathComponent("work/online-lobby/emote_parity/data/MatchHero_\\(female ? "Female" : "Male")_emote_parity.json")', 'let fixtureDir = ProcessInfo.processInfo.environment["VISUAL_GOLDEN_DIR"].map { URL(fileURLWithPath: $0) } ?? repo.appendingPathComponent("work/online-lobby/emote_parity/data")\n            let file = fixtureDir.appendingPathComponent("MatchHero_\\(female ? "Female" : "Male")_emote_parity.json")')
 start=s.index('            XCTAssertEqual(sl.smoothness, 0.2');end=s.index('            // eyes stay smoother',start)
 old=s[start:end]
 new='''            let original = (sl.skinPigmentUV ?? 0) > 0.5
            if original {
                XCTAssertEqual(sl.skinFinish, female ? 2 : 1, "accepted gender response, same selected skin")
                XCTAssertEqual(sl.skinPigmentUV, 1)
                XCTAssertEqual(sl.smoothness, 0.38, accuracy: 0.001)
                XCTAssertEqual(sl.bumpScale, 0)
                XCTAssertEqual(sl.bumpTriplanar, 0)
                XCTAssertEqual(sl.baseMap, "MatchHero_OriginalSeam_RelativeSkinPigment")
                XCTAssertEqual(sl.baseMapLinear, true)
                XCTAssertNotNil(cgImage(skin.diffuse.contents), "linear relative pigment LUT is bound")
                XCTAssertNotNil(skin.value(forKey: "heroTint"))
                XCTAssertTrue(skin.shaderModifiers?[.surface]?.contains("skinPigmentUV") == true)
                XCTAssertEqual(try XCTUnwrap(hero.childNode(withName: "Body", recursively: false)?.geometry).sources(for: .texcoord).count, 3)
            } else {
'''+''.join('    '+line+'\n'for line in old.splitlines())+'''            }
'''
 s=s[:start]+new+s[end:]
 s=s.replace('for name in ["Face_Sclera", "Face_Iris", "Face_Pupil", "Face_Catch"] {','for role in ["Sclera", "Iris", "Pupil", "Catch"] {\n                let name = (original ? "Reference_Face_" : "Face_") + role')
 s=s.replace('name.hasPrefix("Face_") || name == "Skin"','name.hasPrefix("Face_") || name.hasPrefix("Reference_Face_") || name == "Skin"')
 s=s.replace('if name != "Skin" { XCTAssertNil(m.shaderModifiers,', 'if name != "Skin" && !name.hasPrefix("Reference_Face_") { XCTAssertNil(m.shaderModifiers,')
 return s
def visual(s):
 where='    func testShippedGolfAndTennisRigsMatchUnityGoldenVertices() throws {'
 addition='''    /// Adoption is exact, including the distance heroes used in party previews.
    func testOriginalSurfaceAndBlinkContractAcrossAllShippedVariants() throws {
        let faceRoles: Set<String> = ["Reference_Face_Brow", "Reference_Face_Sclera", "Reference_Face_Iris", "Reference_Face_Pupil", "Reference_Face_Limbal", "Reference_Face_Catch"]
        let resources = ["MatchHero_OriginalEye_RelativeIris", "MatchHero_OriginalEye_RelativeSclera", "MatchHero_OriginalSeam_RelativeSkinPigment"]
        for name in resources { XCTAssertNotNil(Bundle.main.url(forResource: name, withExtension: "png"), name) }
        for golf in [false, true] { for female in [false, true] { for distance in golf ? [false] : [false, true] {
            let asset = try XCTUnwrap(MatchHero.asset(female: female, golf: golf, distance: distance))
            let rig = try XCTUnwrap(asset.rig())
            XCTAssertEqual(rig.info.bones.count, golf ? 54 : 53)
            if golf { XCTAssertEqual(rig.info.bones.last, "Club") }
            for role in ["Body", "Face"] {
                let index = try XCTUnwrap(asset.manifest.parts.firstIndex { $0.name == role })
                let part = asset.manifest.parts[index]
                XCTAssertEqual(part.vertexCount, role == "Body" ? (female ? 23230 : 33705) : (female ? 3004 : 3824), "accepted source exact count")
                XCTAssertEqual(asset.geometry[index].sources(for: .texcoord).count, role == "Body" ? 3 : 1)
                let skin = try XCTUnwrap(rig.skinned.first { $0.name == role })
                XCTAssertEqual(skin.morphTargets.map(\\.name), ["Hero_Blink_Half", "Hero_Blink"])
                if role == "Body" {
                    let look = try XCTUnwrap(part.submeshes.first?.look)
                    XCTAssertEqual(look.skinFinish, female ? 2 : 1)
                    XCTAssertEqual(look.skinPigmentUV, 1)
                    XCTAssertEqual(look.baseMapLinear, true)
                    XCTAssertEqual(look.baseMap, resources[2])
                } else {
                    XCTAssertEqual(Set(part.submeshes.map(\\.material)), faceRoles.union(female ? ["Reference_Face_IrisIn"] : []))
                    XCTAssertTrue(part.submeshes.allSatisfy { $0.look?.anatomicalFace == true })
                }
            }
        } } }
    }
'''
 assert where in s;return s.replace(where,addition+where)
stage('MatchHeroLockerTests.swift',locker);stage('LockerMirrorTests.swift',mirror);stage('VisualOverhaulNativeTests.swift',visual)
(TASK/'test-contract-migration.patch').write_text(''.join(patch));(TASK/'test-migration.json').write_text(json.dumps({'status':'STAGED; XCTest not run','files':rows,'counts':'exact accepted source counts; legacy exact counts remain; no tolerance relaxation','fixtures':'All six fresh Unity golden/emote/blink files required. Do not run against stale old-index fixtures.'},indent=2)+'\n')
