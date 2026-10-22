using System.Linq;using UnityEngine;
namespace GolfArcade.Tennis {
 /// Authored regional skin response in unanimated bind coordinates. No skin-tone
 /// replacement: the chosen tone receives restrained cheek/ear/nose warmth and
 /// broad T-zone roughness variation, without pores or procedural noise.
 public static class HeroHeadSurface {
  public static void Configure(MatchHeroLook hero,Material material){
   if(!hero.body||!hero.face||!material)return;var head=hero.Bone(HumanBodyBones.Head);int index=System.Array.IndexOf(hero.body.bones,head);if(index<0)return;
   var mesh=hero.face.GetComponent<MeshFilter>().sharedMesh;var materials=hero.face.sharedMaterials;var points=new System.Collections.Generic.List<Vector3>();
   for(int s=0;s<Mathf.Min(materials.Length,mesh.subMeshCount);s++)if(materials[s]&&materials[s].name.Contains("Sclera"))points.AddRange(mesh.GetTriangles(s).Select(i=>mesh.vertices[i]));if(points.Count==0)return;
   var rest=hero.body.sharedMesh.bindposes[index].inverse;var map=rest*head.worldToLocalMatrix*hero.face.transform.localToWorldMatrix;
   HeroFaceBasis.Get(hero,out var faceRight,out var faceUp,out var faceForward);var r=map.MultiplyVector(faceRight).normalized;var u=map.MultiplyVector(faceUp).normalized;var f=map.MultiplyVector(faceForward).normalized;
   Vector3 origin=rest.GetColumn(3),eye=map.MultiplyPoint3x4(points.Aggregate(Vector3.zero,(sum,p)=>sum+p)/points.Count)-origin;
   float Gaussian(Vector3 point,Vector3 centre,Vector3 radius){var q=point-centre;q=new Vector3(q.x/radius.x,q.y/radius.y,q.z/radius.z);return Mathf.Exp(-2*q.sqrMagnitude);}
   float cheekMaximum=0,noseMaximum=0;foreach(var point in hero.body.sharedMesh.vertices){var d=point-origin;var hp=new Vector3(Vector3.Dot(d,r),Vector3.Dot(d,u),Vector3.Dot(d,f));var e=new Vector3(Vector3.Dot(eye,r),Vector3.Dot(eye,u),Vector3.Dot(eye,f));hp-=e;cheekMaximum=Mathf.Max(cheekMaximum,Gaussian(hp,new Vector3(.044f,-.052f,-.005f),new Vector3(.032f,.031f,.080f)));noseMaximum=Mathf.Max(noseMaximum,Gaussian(hp,new Vector3(0,-.040f,.018f),new Vector3(.022f,.038f,.070f)));}
   Debug.Log("[HeroHeadSurface] "+(hero.female?"Female":"Male")+" origin="+origin.ToString("F6")+" eye="+eye.ToString("F6")+" frame="+r.ToString("F6")+"/"+u.ToString("F6")+"/"+f.ToString("F6")+" cheekMaskMax="+cheekMaximum+" noseMaskMax="+noseMaximum+" shader="+material.shader.name+" hasHeadUniform="+material.HasProperty("_HeadOrigin"));
   material.SetVector("_HeadOrigin",new Vector4(origin.x,origin.y,origin.z,1));material.SetVector("_HeadRight",r);material.SetVector("_HeadUp",u);material.SetVector("_HeadForward",f);material.SetVector("_HeadEye",new Vector4(Vector3.Dot(eye,r),Vector3.Dot(eye,u),Vector3.Dot(eye,f),0));
  }
 }
}
