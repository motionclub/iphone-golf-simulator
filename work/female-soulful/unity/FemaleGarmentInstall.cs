#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;
namespace GolfArcade.EditorTools {
 public static class FemaleGarmentInstall {
  // Top-only installation: accepted skirt meshes, maps and coverage are never copied.
  public static void RefreshTennisTop() {
   string hero="MatchHero_Female",dir=Path.Combine(Environment.GetEnvironmentVariable("CV2_SRC"),hero+"/unity");
   var type=typeof(ClothingV2Install);var mt=type.GetNestedType("Manifest",BindingFlags.NonPublic);
   var manifest=JsonUtility.FromJson(File.ReadAllText(Path.Combine(dir,"manifest.json")),mt);
   var pieces=(Array)mt.GetField("pieces").GetValue(manifest);
   var top=pieces.Cast<object>().First(p=>(string)p.GetType().GetField("name").GetValue(p)=="Kit_Top");
   type.GetMethod("BuildMesh",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,new object[]{dir,top,"Assets/Characters/KitsV2/"+hero+"/Kit_Top.asset"});
   string prefab="Assets/Resources/Tennis/Customization/PlayerFemale.prefab";
   var root=PrefabUtility.LoadPrefabContents(prefab);
   try {
    var look=root.GetComponent<GolfArcade.Tennis.MatchHeroLook>();
    var names=(string[])top.GetType().GetField("bones").GetValue(top);
    int slot=Array.FindIndex(look.kit,r=>r&&r.name=="Kit_Top");
    var all=root.GetComponentsInChildren<Transform>(true);
    look.kit[slot].bones=names.Select(n=>all.FirstOrDefault(t=>t.name==n)??look.body.transform).ToArray();
    look.kitV2Bones[slot]=new GolfArcade.Tennis.MatchHeroLook.KitBones{names=names};
    PrefabUtility.SaveAsPrefabAsset(root,prefab);
   }finally{PrefabUtility.UnloadPrefabContents(root);}
   string dest="Assets/Resources/Tennis/KitsV2/Female/KitV2_Tennis_Female_Top";
   File.Copy(Path.Combine(dir,"Kit_Top_correctives.json"),dest+"_correctives.json",true);
   foreach(string kind in new[]{"N","M"})File.Copy(Path.Combine(dir,"Top_"+kind+".png"),dest+"_"+kind+".png",true);
   Finish();AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
  }
  public static void RefreshGolfTop() {
   string dir=Path.Combine(Environment.GetEnvironmentVariable("CV2_SRC"),"GolfKitHero_Female/unity");
   var type=typeof(ClothingV2Install);var mt=type.GetNestedType("Manifest",BindingFlags.NonPublic);
   var manifest=JsonUtility.FromJson(File.ReadAllText(Path.Combine(dir,"manifest.json")),mt);
   var pieces=(Array)mt.GetField("pieces").GetValue(manifest);
   var top=pieces.Cast<object>().First(p=>(string)p.GetType().GetField("name").GetValue(p)=="Kit_Top");
   type.GetMethod("BuildMesh",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,new object[]{dir,top,"Assets/Characters/KitsV2/GolfKitHero_Female/Kit_Top.asset"});
   File.Copy(Path.Combine(dir,"Kit_Top_correctives.json"),"Assets/Resources/Golf/KitsV2/Female/KitV2_Golf_Female_Top_correctives.json",true);
   Finish();AssetDatabase.Refresh();
  }
  public static void Finish() {
   foreach(var id in new[]{"MatchHero_Female","GolfKitHero_Female"}) {
    string path=$"Assets/Characters/KitsV2/{id}/Kit_Top.asset";
    var mesh=AssetDatabase.LoadAssetAtPath<Mesh>(path);if(!mesh)throw new FileNotFoundException(path);
    // Runtime recognizes this independently authored garment and bypasses the
    // retired torso binding / tank shoulder morphs from the earlier body shell.
    mesh.name="KitV2 FemaleSoulful "+id+" Kit_Top";EditorUtility.SetDirty(mesh);
   }
   AssetDatabase.SaveAssets();
  }
 }
}
#endif
