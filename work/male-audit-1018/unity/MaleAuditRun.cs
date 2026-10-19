#if UNITY_EDITOR
using System;
using System.IO;
using UnityEngine;
using UnityEditor;
namespace GolfArcade.EditorTools {
 /// 2026-10-18 male audit: one Unity launch = HeroTurnaround (all four heroes, ref-sheet hues, no video) + male/female face reviews.
 /// AUDIT_OUT = folder. Proof only; nothing is saved to any asset.
 public static class MaleAuditRun {
  static void Step(string name,Action a){try{Debug.Log("[MaleAudit] "+name);a();}catch(Exception e){Debug.LogException(e);File.AppendAllText(Path.Combine(Out,"errors.txt"),name+": "+e+"\n");}}
  static string Out=>Environment.GetEnvironmentVariable("AUDIT_OUT");
  public static void Run() {
   EditorUtility.audioMasterMute=true;AudioListener.volume=0;
   Directory.CreateDirectory(Out);
   Environment.SetEnvironmentVariable("TURNAROUND_OUT",Path.Combine(Out,"turnaround"));
   Environment.SetEnvironmentVariable("TURNAROUND_LOOK","target");
   Environment.SetEnvironmentVariable("TURNAROUND_VIDEO","0");
   Step("turnaround",HeroTurnaround.Capture);
   foreach(var set in new[]{"views","dressed","body"}){
    Environment.SetEnvironmentVariable("FACE_REVIEW_SET",set);
    Environment.SetEnvironmentVariable("FACE_REVIEW_OUT",Path.Combine(Out,"male_"+set));
    Step("male "+set,MaleFaceReview.Run);
   }
   Environment.SetEnvironmentVariable("FACE_REVIEW_SET","views");
   Environment.SetEnvironmentVariable("FACE_REVIEW_OUT",Path.Combine(Out,"female_views"));
   Step("female views",FemaleFaceReview.Run);
   File.WriteAllText(Path.Combine(Out,"DONE"),DateTime.Now.ToString("s"));
   if(Application.isBatchMode)EditorApplication.Exit(0);
  }
 }
}
#endif
