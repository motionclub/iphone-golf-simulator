using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// Builds the iOS Xcode project to Builds/iOS and writes a one-line verdict to
    /// Library/BuildResults/ios.txt, so the build can be kicked off from the menu bar by a
    /// script and its outcome read back. Sign and install with xcodebuild/devicectl after.
    public static class BuildMenu
    {
        public const string OutputPath = "Builds/iOS";

        [MenuItem("Golf Arcade/Build iOS Xcode Project")]
        public static void BuildIOS()
        {
            TropicalArenaImporter.Prepare();
            Directory.CreateDirectory("Library/BuildResults");
            File.Delete("Library/BuildResults/ios.txt");
            ProjectSetup.EnsureShadersShip();   // shaders made at runtime must be in the build
            // the game server at home is plain http on the Wi-Fi (server/README.md): let the
            // app reach it (Unity refuses http downloads otherwise, and iOS wants the reason)
            PlayerSettings.insecureHttpOption = InsecureHttpOption.AlwaysAllowed;
            var scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray();
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = scenes,
                locationPathName = OutputPath,
                target = BuildTarget.iOS,
                // 11-22 size audit: the player data compressed (LZ4HC, read back in chunks as it loads): resources.assets and its .resS came to
                // 62-63 % of their size in a sample of build 25 (was BuildOptions.None: 1.5 GB stored raw). The App Store download was already
                // zipped, so this is mostly installed size.
                options = BuildOptions.CompressWithLz4HC,
            });
            var summary = report.summary;
            string verdict = $"{summary.result} {summary.totalTime.TotalSeconds:F0}s errors={summary.totalErrors} warnings={summary.totalWarnings} -> {summary.outputPath}";
            foreach (var step in report.steps)
                foreach (var m in step.messages)
                    if (m.type == LogType.Error || m.type == LogType.Exception) verdict += "\n  " + m.content.Trim();
            File.WriteAllText("Library/BuildResults/ios.txt", verdict + "\n");
            Debug.Log("iOS build: " + verdict);
        }

        /// The local network, in words, for the permission iOS asks for the first time the phone
        /// looks for the Mac (to be its club) or the game server at home.
        [UnityEditor.Callbacks.PostProcessBuild]
        public static void LocalNetwork(BuildTarget target, string path)
        {
            if (target != BuildTarget.iOS) return;
            var plistPath = Path.Combine(path, "Info.plist");
            var plist = new UnityEditor.iOS.Xcode.PlistDocument();
            plist.ReadFromFile(plistPath);
            plist.root.SetString("NSLocalNetworkUsageDescription", "Golf Arcade finds your Mac on the Wi-Fi to use the phone as its club, and plays online rooms through the game server at home.");
            var ats = plist.root["NSAppTransportSecurity"]?.AsDict() ?? plist.root.CreateDict("NSAppTransportSecurity");
            ats.SetBoolean("NSAllowsLocalNetworking", true);
            plist.WriteToFile(plistPath);
        }
    }
}
