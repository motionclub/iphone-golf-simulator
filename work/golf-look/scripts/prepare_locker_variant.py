"""Golf locker resources through the shared exporter and SceneKit loader."""
from pathlib import Path
import shutil,json,hashlib
W=Path(__file__).resolve().parents[1];R=W.parents[1];C=W/'candidate';U=W/'isolation/PostClothUnity';changed=[]
def read(rel):return (R/rel).read_text()
def rep(s,a,b):
 if b in s:return s
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def write(rel,s):
 p=C/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s);changed.append(rel)
 if rel.startswith('Unity/'):
  d=U/rel.removeprefix('Unity/');d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
s=read('Unity/Assets/Editor/MatchHeroLockerExport.cs')
s=rep(s,'public float[] trimColor; public float normalStrength, useGarmentMaps;','public float[] trimColor; public float normalStrength, useGarmentMaps, fabricVersion;')
s=rep(s,'static string ExportSex(string sex)','public static void RunGolf() { RunVariant(true); }\n        static void RunVariant(bool golf) {\n            try { Directory.CreateDirectory(OutDir); foreach(string sex in new[]{"Male","Female"}) Debug.Log(ExportSex(sex,golf)); if(Application.isBatchMode)EditorApplication.Exit(0); }\n            catch(Exception e){Debug.LogException(e);if(Application.isBatchMode)EditorApplication.Exit(1);else throw;}\n        }\n\n        static string ExportSex(string sex, bool golf = false)')
s=rep(s,'var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "Player" + sex + ".prefab");','var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "Player" + sex + (golf ? "GolfKit" : "") + ".prefab");')
s=rep(s,'string baseName = "MatchHero_" + sex;','string baseName = (golf ? "GolfHero_" : "MatchHero_") + sex;')
s=rep(s,'look.useGarmentMaps = F("_UseGarmentMaps");','look.useGarmentMaps = F("_UseGarmentMaps"); look.fabricVersion = F("_FabricVersion");')
s=rep(s,'var unfit = infos.SelectMany(i => i.submeshes.Select(s => (i.name, s))).Where(x => x.s.look.shader != "TennisCloth" && x.s.look.shader != "TennisCharacter").ToList();','var unfit = infos.SelectMany(i => i.submeshes.Select(s => (i.name, s))).Where(x => x.s.look.shader != "TennisCloth" && x.s.look.shader != "TennisCharacter" && !(golf && x.name == "Hair_F" && x.s.look.shader == "Universal Render Pipeline/Lit")).ToList();')
# Hair remains an opaque, unchanged separate mesh, not a cloth role.
s=rep(s,'            var racket = root.GetComponentsInChildren<Transform>(true).First(t => t.name == "Racket_Classic");','            var hair = root.GetComponentsInChildren<SkinnedMeshRenderer>(true).FirstOrDefault(r => r.name == "Hair_F");\n            if (hair) list.Add(new PartSource { name=hair.name,kind="hair",mesh=hair.sharedMesh,renderer=hair,skinned=hair,materials=hair.sharedMaterials });\n            var rigidHair = root.GetComponentsInChildren<MeshRenderer>(true).FirstOrDefault(r => r.name == "Hair_F");\n            if (rigidHair) list.Add(new PartSource {name=rigidHair.name,kind="hair",mesh=rigidHair.GetComponent<MeshFilter>().sharedMesh,renderer=rigidHair,materials=rigidHair.sharedMaterials});\n            if (root.GetComponent<MatchHeroLook>().golfKit) return list;\n            var racket = root.GetComponentsInChildren<Transform>(true).First(t => t.name == "Racket_Classic");')
# Golf remains the static Ready sample; no tennis swing/emote is packaged as golf motion.
s=rep(s,'for (int k = 0; k < SwingTimes.Length; k++)', 'for (int k = 0; !golf && k < SwingTimes.Length; k++)')
s=rep(s,'man.rig = ExportRig(root, driver, sources, ready, sb, baseName);', 'man.rig = golf ? null : ExportRig(root, driver, sources, ready, sb, baseName);')
s=rep(s,'man.swingFrames = frames.ToArray();', 'man.swingFrames = frames.ToArray();\n                if(golf){man.swingTimes=Array.Empty<float>();man.swingClip="";man.swingLength=0;man.swingContact=0;}')
write('Unity/Assets/Editor/MatchHeroLockerExport.cs',s)
s=read('GolfArcade/Unity/MatchHeroData.swift')
s=rep(s,'let tileMetres: Float?','let tileMetres: Float?\n        let fabricVersion: Float?')
s=rep(s,'private static var assets: [Bool: Asset] = [:]','private static var assets: [String: Asset] = [:]')
s=rep(s,'static func asset(female: Bool) -> Asset? {\n        if let a = assets[female] { return a }\n        let name = female ? "MatchHero_Female" : "MatchHero_Male"','static func asset(female: Bool, golf: Bool = false) -> Asset? {\n        let name = (golf ? "GolfHero_" : "MatchHero_") + (female ? "Female" : "Male")\n        if let a = assets[name] { return a }')
s=rep(s,'assets[female] = a','assets[name] = a')
# The whole root is mirrored for a left-hander, including the left-hand glove.
# Hide the unused mesh before mirroring, so the glove remains on the lead hand.
s=rep(s,'let node = SCNNode(geometry: geometry); node.name = part.name','let node = SCNNode(geometry: geometry); node.name = part.name\n            if part.name == "Kit_Glove_R" { node.isHidden = true }')
s=rep(s,'let trimRole = (sub.material == "Kit_Shirt" || sub.material == "Kit_ShirtTrim")','let trimRole = (sub.material == "Kit_Shirt" || sub.material == "Kit_ShirtTrim" || sub.material == "Kit_GolfHead" || sub.material == "Kit_GolfGlove")')
write('GolfArcade/Unity/MatchHeroData.swift',s)
s=read('GolfArcade/Unity/MatchHeroSurfaces.swift')
s=rep(s,'m.shaderModifiers = [.surface: garmentSurface, .lightingModel: garmentLighting, .fragment: garmentShoulder]', 'let golf = (look.fabricVersion ?? 1) > 1.5\n        m.shaderModifiers = [.surface: golf ? garmentSurfaceV2 : garmentSurface, .lightingModel: golf ? garmentLightingV2 : garmentLighting, .fragment: garmentShoulder]')
v2 = r'''
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
'''
if 'static var garmentSurfaceV2:' not in s:s=s.rsplit('}',1)[0]+v2+'}\n'
write('GolfArcade/Unity/MatchHeroSurfaces.swift',s)
s=read('GolfArcade/Unity/CharacterModelPreview.swift');tail=s[s.index('/// One SceneKit surface for the whole party.'):]
s=rep(s,'var framing: PreviewFraming = .body\n    var idleSport:','var framing: PreviewFraming = .body\n    var outfitSport: Sport = .tennis\n    var idleSport:')
s=s.replace('context.coordinator.update(player)','context.coordinator.update(player, sport: outfitSport)')
s=rep(s,'var previous: Player?','var previous: Player?\n        private var outfitSport: Sport = .tennis')
if 'racket?.isHidden = framing == .head || outfitSport == .golf' not in s:s=rep(s,'racket?.isHidden = framing == .head\n            let t','racket?.isHidden = framing == .head || outfitSport == .golf\n            let t')
s=rep(s,'func update(_ p: Player) {\n            guard p != previous else { return }; previous=p; idleKey = nil','func update(_ p: Player, sport: Sport = .tennis) {\n            guard p != previous || sport != outfitSport else { return }; previous=p; outfitSport=sport; idleKey = nil')
s=rep(s,'guard let hero = MatchHero.build(p), let asset = MatchHero.asset(female: p.standardFemale) else { return }','guard let hero = MatchHero.build(p, sport: sport), let asset = MatchHero.asset(female: p.standardFemale, golf: sport == .golf) else { return }')
s=rep(s,'racket?.isHidden = framing == .head\n            if let playing','racket?.isHidden = framing == .head || sport == .golf\n            if let playing')
s=rep(s,'static func asset(female: Bool) -> Asset? { MatchHeroData.asset(female: female) }','static func asset(female: Bool, golf: Bool = false) -> Asset? { MatchHeroData.asset(female: female, golf: golf) }')
s=rep(s,'static func build(_ p: Player) -> SCNNode? {\n        guard let asset = asset(female: p.standardFemale)','static func build(_ p: Player, sport: Sport = .tennis) -> SCNNode? {\n        guard let asset = asset(female: p.standardFemale, golf: sport == .golf)')
if 'case let role where role.hasPrefix("Kit_")' not in s:s=rep(s,'case "Kit_Shirt": return pick("shirt").map(kitTint)','case "Kit_Shirt", "Kit_GolfGlove", "Kit_GolfHead": return pick("shirt").map(kitTint)')
if 'case let role where role.hasPrefix("Kit_")' not in s:s=rep(s,'case "Kit_ShortsBand": return pick("shorts").map { kitTint(kitDerive($0)) }','case "Kit_ShortsBand", "Kit_GolfHardware": return pick("shorts").map { kitTint(kitDerive($0)) }')
s=rep(s,'let playing = motion', 'let playing = sport == .tennis ? motion : nil')
s=rep(s,'guard sequence != lastPractice else { return }; lastPractice = sequence', 'guard outfitSport == .tennis, sequence != lastPractice else { return }; lastPractice = sequence')
s=rep(s,'stopLink(); rig?.detach(); rig = nil\n            motion = m', 'stopLink(); rig?.detach(); rig = nil\n            guard outfitSport == .tennis else { motion = nil; return }\n            motion = m')
s=s.replace('case "Kit_Shirt", "Kit_GolfGlove":', 'case "Kit_Shirt", "Kit_GolfGlove", "Kit_GolfHead":')
s=s.replace('case "Kit_ShortsBand": return pick', 'case "Kit_ShortsBand", "Kit_GolfHardware": return pick')
assert s[s.index('/// One SceneKit surface for the whole party.'):]==tail,'Protected lobby suffix changed'
write('GolfArcade/Unity/CharacterModelPreview.swift',s)
s=read('GolfArcade/Unity/LockerStudio.swift')
s=rep(s,'CharacterModelPreview(player: player, cameraDistance: 2.7, framing: framing)','CharacterModelPreview(player: player, cameraDistance: 2.7, framing: framing, outfitSport: menu.lockerSport)')
s=rep(s,'let c = CharacterModelPreview.Coordinator(cameraDistance: 3.1); c.update(p)','let c = CharacterModelPreview.Coordinator(cameraDistance: 3.1); c.update(p, sport: item.sports == [.golf] ? .golf : .tennis)')
write('GolfArcade/Unity/LockerStudio.swift',s)
(W/'data/locker_variant_candidates.json').write_text(json.dumps(dict(files=changed,protectedLobbySuffixSHA=hashlib.sha256(tail.encode()).hexdigest(),status='candidate; compile/resources/render/parity outstanding'),indent=2)+'\n')
