// DRAFT. Copy into the approved scratch namespace only after current Unity batch exits.
// Reuses the unchanged existing checker. No installed-mesh gate is relabeled or hidden.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using GolfArcade.Course;

namespace GolfArcade.EditorTools
{
    public static class PostcardV3FixtureSway
    {
        const BindingFlags Private=BindingFlags.NonPublic|BindingFlags.Static;
        const string Tag="[v3 P1 new fixture] ";
        static readonly Type Checker=typeof(GolfPlantSwayCheck);
        static MethodInfo Method(string name,params Type[] args)
        {
            var m=Checker.GetMethod(name,Private,null,args,null);
            if(m==null||m.ReturnType!=typeof(void)||!m.IsStatic)throw new InvalidOperationException("Unchanged checker API missing/version mismatch: "+name);
            return m;
        }
        static FieldInfo Field(string name,Type expected)
        {
            var f=Checker.GetField(name,Private);
            if(f==null||f.FieldType!=expected)throw new InvalidOperationException("Unchanged checker state API missing/version mismatch: "+name);
            return f;
        }
        static void Invoke(MethodInfo method,params object[] args)
        {
            try {method.Invoke(null,args);}
            catch(TargetInvocationException e) {throw e.InnerException??e;}
        }
        public static void Run()
        {
            string output=Environment.GetEnvironmentVariable("GOLF_SWAY_REPORT");bool outputValidated=false;
            var lines=new List<string>();int code=1;
            try {
                if(string.IsNullOrEmpty(output))throw new InvalidOperationException("GOLF_SWAY_REPORT is required");
                output=Path.GetFullPath(output);string v3=Path.Combine((Environment.GetEnvironmentVariable("GOLF_PROOF_REPO_ROOT") ?? Directory.GetParent(Application.dataPath).Parent.FullName),"work/postcard-look/v3")+Path.DirectorySeparatorChar;
                if(!output.StartsWith(v3,StringComparison.Ordinal))throw new InvalidOperationException("Sway report must be under v3");outputValidated=true;
                string extra=Environment.GetEnvironmentVariable("GOLF_SWAY_EXTRA_FBX");
                if(string.IsNullOrWhiteSpace(extra))throw new InvalidOperationException("GOLF_SWAY_EXTRA_FBX requires only the new P1 fixture asset path(s)");
                var paths=extra.Split(',').Select(s=>s.Trim()).Where(s=>s.Length>0).ToArray();
                var prefabs=new List<(string,GameObject)>();
                foreach(var path in paths) {
                    if(!path.StartsWith("Assets/Editor/PostcardV3Scratch/",StringComparison.Ordinal))throw new InvalidOperationException("Fixture path outside approved scratch namespace: "+path);
                    AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
                    var model=AssetDatabase.LoadAssetAtPath<GameObject>(path);if(!model)throw new InvalidOperationException("Fixture missing/import failed: "+path);
                    if(!model.GetComponentsInChildren<MeshFilter>(true).Any(m=>m.name.StartsWith("PLANT_",StringComparison.Ordinal)&&m.sharedMesh))throw new InvalidOperationException("Fixture has no PLANT_* mesh: "+path);
                    prefabs.Add((Path.GetFileName(path),model));
                }
                if(prefabs.Count==0)throw new InvalidOperationException("No fixture prefabs supplied");
                var reportField=Field("report",typeof(List<string>));var gatesField=Field("gates",typeof(int));var failsField=Field("fails",typeof(int));var tagField=Field("tagNow",typeof(string));
                var mesh=Method("MeshGates",typeof(List<(string,GameObject)>));
                var shared=new[]{"ShaderCompiles","MaterialUnchanged","WindMath","PhaseDecorrelated","GentleContract","GpuSuite"}.Select(n=>Method(n)).ToArray();
                var original=(List<string>)reportField.GetValue(null);original.Clear();gatesField.SetValue(null,0);failsField.SetValue(null,0);tagField.SetValue(null,Tag);
                var saved=LookPixels.SaveRenderSettings();var previousWind=GolfWindSway.ForcedWind;var previousTime=GolfWindSway.FreezeTime;var previousGlobal=Shader.GetGlobalVector("_GolfWind");
                try {
                    EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
                    GolfWindSway.ForcedWind=null;GolfWindSway.FreezeTime=null;Shader.SetGlobalVector("_GolfWind",Vector4.zero);
                    original.Add("INFO: fixture-only input list: "+string.Join(", ",paths)+"; Unity "+Application.unityVersion+"; graphics API "+SystemInfo.graphicsDeviceType);
                    // Exact existing source thresholds and real imported color attributes.
                    Invoke(shared[0]);Invoke(shared[1]);Invoke(shared[2]);Invoke(shared[3]);Invoke(shared[4]);
                    Invoke(mesh,prefabs);
                    // Actual GPU mirror/root/direction, FBX strip chain, shadow, and only-plants rigs.
                    // This is the unchanged active-pipeline suite, not a synthetic replacement.
                    Invoke(shared[5]);
                } catch(Exception e) {
                    original.Add("GATE: "+Tag+"FIXTURE_SWAY_EXECUTION FAIL - "+e);
                    failsField.SetValue(null,(int)failsField.GetValue(null)+1);gatesField.SetValue(null,(int)gatesField.GetValue(null)+1);
                } finally {
                    tagField.SetValue(null,"");GolfWindSway.ForcedWind=previousWind;GolfWindSway.FreezeTime=previousTime;Shader.SetGlobalVector("_GolfWind",previousGlobal);LookPixels.RestoreRenderSettings(saved);
                }
                lines.AddRange(original);int gates=(int)gatesField.GetValue(null),fails=(int)failsField.GetValue(null);
                var colors=original.Where(l=>l.StartsWith("GATE: "+Tag+"PLANT_SWAY_COLORS_UNITY ",StringComparison.Ordinal)).ToArray();
                var caps=original.Where(l=>l.StartsWith("GATE: "+Tag+"SWAY_GENTLE ",StringComparison.Ordinal)).ToArray();
                bool colorPass=colors.Length==1&&colors[0].Contains(" PASS - "),capPass=caps.Length==1&&caps[0].Contains(" PASS - ");
                lines.Add("GATE: "+Tag+"PLANT_SWAY_COLORS "+(colorPass?"PASS":"FAIL")+" - exact alias of the retained fixture PLANT_SWAY_COLORS_UNITY line; missing/duplicate line fails");
                lines.Add("GATE: "+Tag+"PLANT_SWAY_CAPS "+(capPass?"PASS":"FAIL")+" - exact alias of retained fixture SWAY_GENTLE, same original per-kind caps and full-loop mirror samples; shared actual GPU suite must also pass");
                bool pass=fails==0&&colorPass&&capPass;
                lines.Add("SUMMARY: "+(gates-fails)+"/"+gates+" original fixture/shared GPU gates PASS; fixture aliases "+(colorPass&&capPass?"PASS":"FAIL")+"; P1 fixture sway "+(pass?"PASS":"FAIL"));
                lines.Add("INFO: installed hole meshes were not input to this entrypoint; their separate failures remain in their own original full-check reports. Active pipeline only; target iOS compilation is separate.");
                if(pass)code=0;
            } catch(Exception e) {lines.Add("GATE: "+Tag+"FIXTURE_SWAY_ENTRYPOINT FAIL - "+e);}
            finally {
                if(outputValidated) {Directory.CreateDirectory(Path.GetDirectoryName(output));File.WriteAllLines(output,lines);}
                foreach(var line in lines)Debug.Log(line);
                if(Application.isBatchMode)EditorApplication.Exit(code);
            }
        }
    }
}
