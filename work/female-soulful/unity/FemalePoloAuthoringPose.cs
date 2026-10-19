#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using GolfArcade.Tennis;
using UnityEngine;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools {
 public static class FemalePoloAuthoringPose {
  static void Floats(string path,float[] values){using var w=new BinaryWriter(File.Create(path));foreach(var v in values)w.Write(v);}
  static float[] Matrix(Matrix4x4 m)=>Enumerable.Range(0,16).Select(i=>m[i%4,i/4]).ToArray();
  public static void Run(){
   var type=typeof(HeroTurnaround);object[] args={"GolfKitHero_Female",null,null};
   var root=(GameObject)type.GetMethod("BuildHero",BindingFlags.NonPublic|BindingFlags.Static).Invoke(null,args);
   try {
    type.GetMethod("RestPose",BindingFlags.NonPublic|BindingFlags.Static).Invoke(null,new object[]{root});
    var look=root.GetComponent<MatchHeroLook>();
    foreach(var pair in new[]{(HumanBodyBones.LeftUpperArm,HumanBodyBones.LeftLowerArm),(HumanBodyBones.RightUpperArm,HumanBodyBones.RightLowerArm)}){
     var upper=look.Bone(pair.Item1);var elbow=look.Bone(pair.Item2);float sign=Mathf.Sign(upper.position.x-root.transform.position.x);
     var direction=Vector3.down*Mathf.Cos(25*Mathf.Deg2Rad)+Vector3.right*sign*Mathf.Sin(25*Mathf.Deg2Rad);
     upper.rotation=Quaternion.FromToRotation(elbow.position-upper.position,direction)*upper.rotation;
    }
    type.GetMethod("Correctives",BindingFlags.NonPublic|BindingFlags.Static).Invoke(null,new object[]{root});
    var body=look.body;var baked=new Mesh();body.BakeMesh(baked,false);
    string folder=Environment.GetEnvironmentVariable("POLO_APOSE_OUT");Directory.CreateDirectory(folder);
    Floats(Path.Combine(folder,"body_pos.f32"),baked.vertices.SelectMany(v=>new[]{v.x,v.y,v.z}).ToArray());
    Floats(Path.Combine(folder,"body_nrm.f32"),baked.normals.SelectMany(v=>new[]{v.x,v.y,v.z}).ToArray());
    Floats(Path.Combine(folder,"bind.f32"),body.bones.SelectMany(b=>Matrix(b.worldToLocalMatrix*body.transform.localToWorldMatrix)).ToArray());
    Floats(Path.Combine(folder,"rest_bones.f32"),body.bones.SelectMany(b=>Matrix(b.localToWorldMatrix)).ToArray());
    Floats(Path.Combine(folder,"rest_body_world.f32"),baked.vertices.SelectMany(v=>{var q=body.transform.TransformPoint(v);return new[]{q.x,q.y,q.z};}).ToArray());
    File.WriteAllText(Path.Combine(folder,"bones.json"),"["+string.Join(",",body.bones.Select(b=>"\""+b.name+"\""))+"]");
    Object.DestroyImmediate(baked);
   }finally{Object.DestroyImmediate(root);}
  }
 }
}
#endif
