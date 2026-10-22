using System;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using GolfArcade.Tennis;
using Object = UnityEngine.Object;
namespace GolfArcade.EditorTools {
 public static class ClothingLodSmoke {
  public static void Run() {
   try {
    HeroGarmentLOD.ForceFullDetail=false; HeroGarmentLOD.ForceMatchDetailForReview=false;
    var camera=new GameObject("Clothing LOD test").AddComponent<Camera>(); camera.orthographic=true;
    foreach(var sex in new[]{"Female"}) {
     var root=Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Resources/Tennis/Customization/Player"+sex+".prefab"));
     var look=root.GetComponent<MatchHeroLook>();
     typeof(MatchHeroLook).GetMethod("OwnMaterials",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(look,null);
     var driver=root.GetComponent<HeroTennisDriver>(); driver.ResolvePerformanceClips();
     var slot=driver.slots.First(s=>s.id==HeroTennisDriver.Clip.Serve); slot.clip.SampleAnimation(root,slot.clip.length*.57f);
     var lod=root.GetComponent<HeroGarmentLOD>(); if(!lod)lod=root.AddComponent<HeroGarmentLOD>();lod.look=look; var deformation=root.GetComponent<TailoredPoloDeformation>();
     var top=look.kit.First(r=>r&&r.name=="Kit_Top"); Mesh full=null; Vector3[] first=null;
     for(int step=0;step<3;step++) {
      camera.orthographicSize=step==1?8:1; lod.Prepare(camera); deformation.Apply();
      if(lod.UsingMatchDetail!=(step==1)) throw new Exception(sex+" LOD threshold transition failed");
      var baked=new Mesh(); top.BakeMesh(baked); var vertices=baked.vertices;
      if(vertices.Any(v=>!float.IsFinite(v.sqrMagnitude))) throw new Exception("Nonfinite garment after LOD transition");
      if(step==0){full=top.sharedMesh;first=vertices;}
      if(step==1&&top.sharedMesh==full)throw new Exception("Distance mesh not selected");
      if(step==2&&(top.sharedMesh!=full||vertices.Length!=first.Length||vertices.Where((v,i)=>(v-first[i]).sqrMagnitude>1e-12f).Any()))throw new Exception("Full mesh did not round trip exactly");
      Object.DestroyImmediate(baked);
     }
     Debug.Log("CLOTHING LOD PASS "+sex+" Full > Distance > Full, exact vertex return, finite morph skinning");
     Object.DestroyImmediate(root);
    }
    Object.DestroyImmediate(camera.gameObject);EditorApplication.Exit(0);
   } catch(Exception e){Debug.LogException(e);EditorApplication.Exit(1);}
  }
 }
}
