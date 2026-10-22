#if UNITY_EDITOR
using System.IO;
using System.Text;
using UnityEditor.TestTools.TestRunner.Api;
using UnityEngine;
namespace GolfArcade.EditorTools
{
    /// Diagnostic: run named EditMode test classes from a CLI eval and write results to a file.
    public static class FemaleTestRun
    {
        sealed class Sink : ICallbacks
        {
            public string path;
            public void RunStarted(ITestAdaptor t) {}
            public void TestStarted(ITestAdaptor t) {}
            public void TestFinished(ITestResultAdaptor r) {}
            public void RunFinished(ITestResultAdaptor r)
            {
                var sb = new StringBuilder(); sb.AppendLine($"TOTAL pass={r.PassCount} fail={r.FailCount} skip={r.SkipCount}"); Write(r, sb);
                File.WriteAllText(path, sb.ToString());
            }
            static void Write(ITestResultAdaptor r, StringBuilder sb)
            {
                if (!r.HasChildren) sb.AppendLine($"{r.TestStatus} {r.FullName} {(r.Message ?? "").Replace("\n", " ")}");
                else foreach (var c in r.Children) Write(c, sb);
            }
        }
        public static void Run(string output, params string[] classes)
        {
            var api = ScriptableObject.CreateInstance<TestRunnerApi>();
            api.RegisterCallbacks(new Sink { path = output });
            api.Execute(new ExecutionSettings(new Filter { testMode = TestMode.EditMode, groupNames = classes }));
        }
    }
}
#endif
