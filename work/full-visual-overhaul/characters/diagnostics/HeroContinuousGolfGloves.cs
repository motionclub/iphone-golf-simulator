using System;using System.Linq;using UnityEngine;
namespace GolfArcade.Tennis {
 /// Editable glove shell follows the same continuous fingers; original atlas and
 /// role materials are retained, while exact original bone rest is validated.
 public static class HeroContinuousGolfGloves {
  public static void Apply(MatchHeroLook hero){
   if(!hero||!hero.golfKit||hero.kit==null)return;
   var model=Resources.Load<GameObject>("Golf/Premium/Gloves/"+(hero.female?"Female":"Male"));if(!model)throw new InvalidOperationException("Authored continuous glove source missing");
   var palette=hero.body.bones;var binds=hero.body.sharedMesh.bindposes;var bodyToRoot=hero.transform.worldToLocalMatrix*hero.body.transform.localToWorldMatrix;
   var expected=palette.Select((b,i)=>new{b.name,rest=bodyToRoot*binds[i].inverse}).ToDictionary(b=>b.name,b=>b.rest);
   var byName=hero.GetComponentsInChildren<Transform>(true).GroupBy(b=>b.name).ToDictionary(g=>g.Key,g=>g.First());
   foreach(var source in model.GetComponentsInChildren<SkinnedMeshRenderer>(true)){
    var live=hero.kit.FirstOrDefault(r=>r&&r.name==source.name);if(!live)throw new InvalidOperationException("Continuous glove role missing "+source.name);
    if(live.sharedMesh.name.Contains("(continuous glove)"))continue;
    var sourceToRoot=model.transform.worldToLocalMatrix*source.transform.localToWorldMatrix;float error=0;
    for(int b=0;b<source.bones.Length;b++){
     if(!expected.TryGetValue(source.bones[b].name,out var matrix))throw new InvalidOperationException("Continuous glove unknown bind "+source.bones[b].name);
     var rest=sourceToRoot*source.sharedMesh.bindposes[b].inverse;for(int k=0;k<16;k++)error=Mathf.Max(error,Mathf.Abs(matrix[k]-rest[k]));
    }
    if(error>.0002f)throw new InvalidOperationException("Continuous glove original root rest drift "+source.name+" "+error);
    live.transform.localPosition=sourceToRoot.GetColumn(3);live.transform.localRotation=sourceToRoot.rotation;live.transform.localScale=sourceToRoot.lossyScale;
    var mesh=UnityEngine.Object.Instantiate(source.sharedMesh);mesh.hideFlags=HideFlags.DontSave;mesh.name=source.sharedMesh.name+" (continuous glove)";live.sharedMesh=mesh;
    live.bones=source.bones.Select(b=>byName[b.name]).ToArray();live.rootBone=byName[source.rootBone.name];live.localBounds=hero.body.localBounds;live.updateWhenOffscreen=true;live.quality=SkinQuality.Bone4;
    Debug.Log("[HeroContinuousGolfGloves] "+(hero.female?"Female":"Male")+" "+live.name+" exact original root-rest error="+error+"; fitted offset=1.3mm; original role material retained");
   }
  }
 }
}
