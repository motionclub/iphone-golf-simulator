using System.Linq;
using UnityEditor;
using UnityEngine;

/// Clone-only: builds the macOS standalone player MenuProfileBoot measures (frame timing stats on, the project's own scenes).
///   Unity -batchmode -quit -projectPath <clone> -executeMethod MenuProfileBuild.Build -menuBuildOut <app path>
public static class MenuProfileBuild
{
    public static void Build()
    {
        var args = System.Environment.GetCommandLineArgs(); int i = System.Array.IndexOf(args, "-menuBuildOut");
        string outPath = i >= 0 ? args[i + 1] : "Builds/MenuProfile.app";
        PlayerSettings.enableFrameTimingStats = true;
        PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);
        var scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray();
        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions { scenes = scenes, locationPathName = outPath, target = BuildTarget.StandaloneOSX, options = BuildOptions.None });
        Debug.Log("MenuProfileBuild: " + report.summary.result + " " + report.summary.totalSize + " bytes, " + report.summary.totalTime);
        EditorApplication.Exit(report.summary.result == UnityEditor.Build.Reporting.BuildResult.Succeeded ? 0 : 1);
    }
}
