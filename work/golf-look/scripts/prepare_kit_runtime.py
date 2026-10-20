"""Add the golf variant to the shared kit path; tennis defaults stay unchanged."""
from pathlib import Path
import shutil,json,hashlib
W=Path(__file__).resolve().parents[1];R=W.parents[1];C=W/'candidate';U=W/'isolation/PostClothUnity';changes=[]
def write(rel,s):
 p=C/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s);changes.append(rel)
 if rel.startswith('Unity/'):
  d=U/rel.removeprefix('Unity/');d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
def rep(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
s=(R/'Unity/Assets/Scripts/Tennis/MatchHeroLook.cs').read_text()
s=rep(s,'public bool female;','public bool female;\n        public bool golfKit;\n        public const string RoleGolfHead = "Kit_GolfHead", RoleGolfGlove = "Kit_GolfGlove", RoleGolfHardware = "Kit_GolfHardware";\n        public void SetGolfHand(bool leftHanded)\n        {\n            if (!golfKit || kit == null) return;\n            foreach (var r in kit) if (r && (r.name == "Kit_Glove_L" || r.name == "Kit_Glove_R"))\n                r.enabled = r.name == (leftHanded ? "Kit_Glove_R" : "Kit_Glove_L");\n        }')
s=rep(s,'static Texture2D weaveMap, skinBumpMap, fabricAtlas;','static Texture2D weaveMap, skinBumpMap, fabricAtlas, golfFabricAtlas;\n        static Texture2D GolfFabricAtlas => golfFabricAtlas ? golfFabricAtlas : golfFabricAtlas = Resources.Load<Texture2D>("Golf/HeroDetail/Golf_FabricAtlas");')
s=rep(s,'string garment = $"Tennis/HeroDetail/Kit_{(female ? "Female" : "Male")}_{tag}";','string garment = golfKit ? $"Golf/HeroDetail/Golf_{(female ? "Female" : "Male")}_{tag}" : $"Tennis/HeroDetail/Kit_{(female ? "Female" : "Male")}_{tag}";')
s=rep(s,'if (FabricAtlas) m.SetTexture("_WeaveMap", FabricAtlas);','var atlas = golfKit ? GolfFabricAtlas : FabricAtlas;\n                if (atlas) m.SetTexture("_WeaveMap", atlas);\n                if (golfKit) m.SetFloat("_FabricVersion", 2);')
s=rep(s,'Put(RoleShoe, ho, KitTint(shoes));','Put(RoleShoe, ho, KitTint(shoes));\n            if (golfKit) { Put(RoleGolfHead, hs, KitTint(shirt)); Put(RoleGolfGlove, hs, KitTint(shirt)); Put(RoleGolfHardware, hh, KitTint(KitDerive(shorts))); }')
s=rep(s,'Trim(RoleShorts, hh, shorts); Trim(RoleShortsBand, hh, shorts); Trim(RoleShoe, ho, shoes);','Trim(RoleShorts, hh, shorts); Trim(RoleShortsBand, hh, shorts); Trim(RoleShoe, ho, shoes);\n            if (golfKit) { Trim(RoleGolfHead, hs, shirt); Trim(RoleGolfGlove, hs, shirt); }')
write('Unity/Assets/Scripts/Tennis/MatchHeroLook.cs',s)
s=(R/'Unity/Assets/Editor/MatchHeroKit.cs').read_text()
s=rep(s,'path.StartsWith(MatchHeroKit.KitRoot) && path.EndsWith(".fbx")','(path.StartsWith(MatchHeroKit.KitRoot) || path.StartsWith(GolfHeroKit.KitRoot)) && path.EndsWith(".fbx")')
s=rep(s,'            var sb = new StringBuilder();\n            var model = AssetDatabase.LoadAssetAtPath<GameObject>(FbxPath(sex));','            return AttachVariant(root, sex, look, body, FbxPath(sex), Pieces, EnsureMaterials());\n        }\n\n        public static string AttachVariant(GameObject root, string sex, MatchHeroLook look, SkinnedMeshRenderer body, string fbxPath, string[] pieces, Dictionary<string, Material> mats)\n        {\n            var sb = new StringBuilder();\n            var model = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);')
s=rep(s,'if (!model) throw new FileNotFoundException("kit FBX not imported: " + FbxPath(sex));\n            var mats = EnsureMaterials();','if (!model) throw new FileNotFoundException("kit FBX not imported: " + fbxPath);')
s=s.replace('kitSmrs.Length != Pieces.Length || Pieces.Any','kitSmrs.Length != pieces.Length || pieces.Any').replace('foreach (var name in Pieces)','foreach (var name in pieces)')
# Optional unchanged hair from the same golf export is attached through the exact bone-binding path.
write('Unity/Assets/Editor/MatchHeroKit.cs',s)
write('Unity/Assets/Editor/GolfHeroKit.cs','''using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEngine;
namespace GolfArcade.EditorTools {
 public static class GolfHeroKit {
  public const string KitRoot="Assets/Characters/GolfHeroKit/";
  public static readonly string[] Pieces={"Kit_Top","Kit_Bottom","Kit_Head","Kit_Glove_L","Kit_Glove_R","Kit_Shoe_L","Kit_Shoe_R"};
  public static void Build() {
   try {
    Directory.CreateDirectory(KitRoot);
    string source=Environment.GetEnvironmentVariable("GOLF_KIT_SOURCE"); if(string.IsNullOrEmpty(source))throw new ArgumentException("GOLF_KIT_SOURCE required");
    foreach(string sex in new[]{"Male","Female"})File.Copy(Path.Combine(source,"Golf_"+sex+"_Kit.fbx"),KitRoot+sex+"_Kit.fbx",true);
    AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
    string matDir=KitRoot+"Materials/";Directory.CreateDirectory(matDir);
    var mats=new Dictionary<string,Material>();
    foreach(string role in new[]{MatchHeroLook.RoleShirt,MatchHeroLook.RoleShorts,MatchHeroLook.RoleShoe,MatchHeroLook.RoleGolfHead,MatchHeroLook.RoleGolfGlove,MatchHeroLook.RoleGolfHardware}) {
     var mat=AssetDatabase.LoadAssetAtPath<Material>(matDir+role+".mat");if(!mat){mat=new Material(Shader.Find("Universal Render Pipeline/Lit"));AssetDatabase.CreateAsset(mat,matDir+role+".mat");}
     mat.name=role;Color col=role==MatchHeroLook.RoleShorts?new Color(.065f,.069f,.077f):role==MatchHeroLook.RoleGolfHead?new Color(.035f,.035f,.0401f):role==MatchHeroLook.RoleGolfHardware?new Color(.72f,.73f,.74f):new Color(.93f,.93f,.93f);
     mat.SetColor("_BaseColor",col);mat.SetFloat("_Smoothness",.30f);mat.SetFloat("_Metallic",0);EditorUtility.SetDirty(mat);mats[role]=mat;
    }
    foreach(string sex in new[]{"Male","Female"}) {
     var root=PrefabUtility.LoadPrefabContents("Assets/Resources/Tennis/Customization/Player"+sex+".prefab");
     try {
      var look=root.GetComponent<MatchHeroLook>();look.golfKit=true;
      foreach(var r in root.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(r=>r.name.StartsWith("Kit_")).ToArray())UnityEngine.Object.DestroyImmediate(r.gameObject);
      var model=AssetDatabase.LoadAssetAtPath<GameObject>(KitRoot+sex+"_Kit.fbx");
      Debug.Log(MatchHeroKit.AttachVariant(root,sex,look,look.body,KitRoot+sex+"_Kit.fbx",Pieces,mats));
      if(sex=="Female") {
       var sourceHair=model.GetComponentsInChildren<MeshRenderer>(true).Single(r=>r.name=="Hair_F");
       var sourceHead=model.GetComponentsInChildren<Transform>(true).Single(t=>t.name=="Head");
       var head=root.transform.Find("Rig_"+sex).GetComponentsInChildren<Transform>(true).Single(t=>t.name=="Head");
       var local=sourceHead.worldToLocalMatrix*sourceHair.transform.localToWorldMatrix;
       var hairNode=new GameObject("Hair_F");hairNode.transform.SetParent(head,false);
       hairNode.transform.localPosition=local.GetColumn(3);hairNode.transform.localRotation=local.rotation;hairNode.transform.localScale=local.lossyScale;
       hairNode.AddComponent<MeshFilter>().sharedMesh=sourceHair.GetComponent<MeshFilter>().sharedMesh;
       var hair=hairNode.AddComponent<MeshRenderer>();hair.sharedMaterials=sourceHair.sharedMaterials;
       hair.shadowCastingMode=look.body.shadowCastingMode;hair.receiveShadows=look.body.receiveShadows;
       Debug.Log("GOLF_HAIR rigid existing Head attachment: "+hair.GetComponent<MeshFilter>().sharedMesh.vertexCount+" vertices, unchanged source mesh");
      }
      Debug.Log("GOLF_CORRECTIVES "+sex+" shapes="+look.kit.Single(r=>r.name=="Kit_Top").sharedMesh.blendShapeCount);
      look.SetGolfHand(false);
      var corrective=root.GetComponent<GolfGarmentCorrectives>() ?? root.AddComponent<GolfGarmentCorrectives>();corrective.look=look;
      PrefabUtility.SaveAsPrefabAsset(root,"Assets/Resources/Tennis/Customization/Player"+sex+"GolfKit.prefab");
     }finally{PrefabUtility.UnloadPrefabContents(root);}
    }
    AssetDatabase.SaveAssets();if(Application.isBatchMode)EditorApplication.Exit(0);
   }catch(Exception e){Debug.LogException(e);if(Application.isBatchMode)EditorApplication.Exit(1);else throw;}
  }
 }
}
''')
(W/'data/kit_runtime_candidates.json').write_text(json.dumps(dict(files=changes,status='candidate; compile, import, recolour and parity checks required'),indent=2)+'\n')
