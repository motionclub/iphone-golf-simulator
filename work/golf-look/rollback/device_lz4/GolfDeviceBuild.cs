using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;
namespace GolfArcade.EditorTools
{
 public static class GolfDeviceBuild
 {
  public static void Run()
  {
   var output=Path.GetFullPath(Environment.GetEnvironmentVariable("GOLF_DEVICE_BUILD_OUT"));
   if(!output.Contains("/work/golf-look/"))throw new InvalidOperationException("Diagnostic output must remain in golf-look work");
   if(EditorUserBuildSettings.activeBuildTarget!=BuildTarget.iOS)throw new InvalidOperationException("Use -buildTarget iOS");
   PlayerSettings.enableFrameTimingStats=true;
   PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.iOS,"com.partytennis.GolfLookProof");
   PlayerSettings.bundleVersion=Environment.GetEnvironmentVariable("GOLF_DEVICE_VARIANT");
   var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions{scenes=new[]{"Assets/Scenes/Golf.unity"},target=BuildTarget.iOS,locationPathName=output,options=BuildOptions.DetailedBuildReport});
   var summary=report.summary;
   File.WriteAllText(Path.Combine(output,"build_summary.txt"),summary.result+"\nseconds="+summary.totalTime.TotalSeconds+"\nerrors="+summary.totalErrors+"\n"+string.Join("\n",report.steps.SelectMany(x=>x.messages).Where(x=>x.type==LogType.Error).Select(x=>x.content)));
   EditorApplication.Exit(summary.result==BuildResult.Succeeded&&summary.totalErrors==0?0:1);
  }
 }
}
