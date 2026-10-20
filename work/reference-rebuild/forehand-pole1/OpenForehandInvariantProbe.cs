using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEngine;
using GolfArcade.Tennis;
namespace GolfArcade.EditorTools {
 // Work-only proof hook. Root may call Save immediately after driver.Sample.
 // The paired control/candidate runs keep all upstream graph/contact setup identical.
 public static class OpenForehandInvariantProbe {
  [Serializable] public sealed class Row { public string name; public float[] matrix; }
  [Serializable] public sealed class Snapshot {
   public string label,control; public float sampleTime,contactTime,length;
   public Row[] preserved,arm; public float[] authoredContactLocal;
  }
  const BindingFlags Fields=BindingFlags.Instance|BindingFlags.NonPublic;
  static Transform Field(HeroTennisDriver driver,string name)=>(Transform)typeof(HeroTennisDriver).GetField(name,Fields).GetValue(driver);
  static float[] Matrix(Matrix4x4 m)=>Enumerable.Range(0,16).Select(i=>m[i/4,i%4]).ToArray();
  public static void Save(HeroTennisDriver driver,string label,float sampleTime,string output) {
   if(!driver||!driver.matchLook||driver.matchLook.female)return;
   var hero=driver.matchLook;var toRoot=hero.transform.worldToLocalMatrix;
   var hand=hero.Bone(HumanBodyBones.RightHand);
   var retained=hand.GetComponentsInChildren<Transform>(true).ToList();
   foreach(var n in new[]{"stringCentre","stringRight","stringUp","stringNormal"}){var t=Field(driver,n);if(t&&!retained.Contains(t))retained.Add(t);}
   if(hero.racketGrip&&!retained.Contains(hero.racketGrip))retained.Add(hero.racketGrip);
   string PathOf(Transform t){string n=t.name;for(var q=t.parent;q&&q!=hero.transform;q=q.parent)n=q.name+"/"+n;return n;}
   Row Read(Transform t)=>new Row{name=PathOf(t),matrix=Matrix(toRoot*t.localToWorldMatrix)};
   var contacts=(Vector3[])typeof(HeroTennisDriver).GetField("contactLocal",Fields).GetValue(driver);
   var at=contacts[(int)HeroTennisDriver.Clip.ForehandOpen];
   var report=new Snapshot{label=label,control=Environment.GetEnvironmentVariable("VISUAL_OPEN_FOREHAND_CLEARANCE")??"enabled",sampleTime=sampleTime,
    contactTime=driver.ContactOf(HeroTennisDriver.Clip.ForehandOpen),length=driver.LengthOf(HeroTennisDriver.Clip.ForehandOpen),
    preserved=retained.Select(Read).ToArray(),arm=new[]{hero.Bone(HumanBodyBones.RightUpperArm),hero.Bone(HumanBodyBones.RightLowerArm)}.Select(Read).ToArray(),authoredContactLocal=new[]{at.x,at.y,at.z}};
   Directory.CreateDirectory(output);File.WriteAllText(Path.Combine(output,label+".json"),JsonUtility.ToJson(report));
  }
 }
}
