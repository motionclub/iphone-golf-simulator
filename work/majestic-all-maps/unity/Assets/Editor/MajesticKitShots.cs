#if UNITY_EDITOR
// Chat 10: Unity import check of the landmark kit (work/majestic-landmarks). Each asset alone in an empty lit scene,
// spawned exactly as the course kit does (MajesticKit.Spawn), rendered with LOD 0, 1 and 2 forced, 640x360 each, plus a
// report of LODGroups, renderers, materials/shaders and vertex colours. MAM_OUT=<dir>; play mode, muted, clone only.
using System;
using System.IO;
using System.Linq;
using System.Text;
using GolfArcade.Majestic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class MajesticKitShots
    {
        const string Key = "MajesticKitShots";
        static int frame = -1, state = 0;
        static MajesticKitShots() { EditorApplication.update += Tick; }

        public static void Run()
        {
            var o = Environment.GetEnvironmentVariable("MAM_OUT"); if (string.IsNullOrEmpty(o)) throw new ArgumentException("MAM_OUT");
            Directory.CreateDirectory(o); SessionState.SetString(Key + "out", Path.GetFullPath(o)); SessionState.SetBool(Key, true);
            EditorUtility.audioMasterMute = true;
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            EditorSceneManager.SaveScene(scene, "Assets/MajesticKitShots.unity");
            EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Key, false) || !EditorApplication.isPlaying) return;
            if (Time.frameCount - frame < 5) return; frame = Time.frameCount;
            try { if (state++ == 1) { Shoot(); SessionState.SetBool(Key, false); EditorApplication.Exit(0); } }
            catch (Exception e) { Debug.LogException(e); SessionState.SetBool(Key, false); EditorApplication.Exit(1); }
        }

        static void Shoot()
        {
            string Out = SessionState.GetString(Key + "out", "/tmp/kitshots");
            var sun = new GameObject("sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.intensity = 1.6f; sun.color = new Color(1f, .95f, .85f);
            sun.transform.rotation = Quaternion.Euler(40, -35, 0); sun.shadows = LightShadows.Soft; RenderSettings.sun = sun;
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.6f, .7f, .9f); RenderSettings.ambientEquatorColor = new Color(.6f, .6f, .55f); RenderSettings.ambientGroundColor = new Color(.35f, .32f, .28f);
            var cam = new GameObject("cam").AddComponent<Camera>(); cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.62f, .75f, .9f); cam.fieldOfView = 40; cam.farClipPlane = 5000;
            var rt = new RenderTexture(640, 360, 24) { antiAliasing = 4 }; var tex = new Texture2D(640, 360, TextureFormat.RGB24, false);
            var names = Resources.LoadAll<GameObject>("Majestic/Kit").Select(g => g.name).OrderBy(n => n).ToArray();
            var rep = new StringBuilder();
            foreach (var n in names)
            {
                var go = MajesticKit.Spawn(n, null, Vector3.zero, Quaternion.identity, 1, true); if (!go) continue;
                var b = new Bounds(go.transform.position, Vector3.zero); foreach (var r in go.GetComponentsInChildren<Renderer>()) b.Encapsulate(r.bounds);
                var lg = go.GetComponentInChildren<LODGroup>();
                rep.AppendLine($"{n}: bounds {b.size} lodgroup={(lg ? lg.lodCount.ToString() : "NONE")} renderers={go.GetComponentsInChildren<Renderer>().Length}");
                foreach (var r in go.GetComponentsInChildren<Renderer>())
                {
                    var mf = r.GetComponent<MeshFilter>(); var mesh = mf ? mf.sharedMesh : null;
                    rep.AppendLine($"   {r.name}: {string.Join(",", r.sharedMaterials.Select(m => m ? m.shader.name : "null"))} tris={(mesh ? mesh.triangles.Length / 3 : 0)} colors={(mesh ? mesh.colors.Length : 0)} uv2={(mesh ? mesh.uv3.Length : 0)}");
                }
                float d = b.extents.magnitude * 2.6f;
                cam.transform.position = b.center + new Vector3(0, b.extents.y * .25f, d); cam.transform.LookAt(b.center);
                for (int lod = 0; lod < 3; lod++)
                {
                    if (lg) lg.ForceLOD(lod);
                    cam.targetTexture = rt; cam.Render(); RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, 640, 360), 0, 0); tex.Apply(); RenderTexture.active = null; cam.targetTexture = null;
                    File.WriteAllBytes(Path.Combine(Out, $"{n}_lod{lod}.jpg"), tex.EncodeToJPG(85));
                    if (!lg) break;
                }
                Object.DestroyImmediate(go);
            }
            File.WriteAllText(Path.Combine(Out, "kit_report.txt"), rep.ToString());
            Debug.Log("[MajesticKitShots] " + names.Length + " assets");
        }
    }
}
#endif
