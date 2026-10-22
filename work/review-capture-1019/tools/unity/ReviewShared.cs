#if UNITY_EDITOR
// Review capture 10-19 (work/review-capture-1019): extra cameras that copy the gameplay camera's look and render a review angle
// into their own RenderTexture each frame, plus character still sets (front .. low angle) around a humanoid hero.
using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEngine;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    public sealed class ReviewAngle
    {
        public readonly string Name; public readonly Camera Cam; readonly RenderTexture rt; readonly Texture2D tex; readonly int w, h;
        public string Dir; public int Saved;
        public Vector3 Pos, Look, Up = Vector3.up; public float Fov = 40; bool placed;
        public ReviewAngle(string name, string dir, int width, int height)
        {
            Name = name; Dir = dir; w = width; h = height;
            Cam = new GameObject("Review cam " + name).AddComponent<Camera>(); Cam.enabled = false;
            rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32) { antiAliasing = 2 };
            tex = new Texture2D(w, h, TextureFormat.RGB24, false);
            if (dir != null) Directory.CreateDirectory(dir);
        }
        /// Move toward (pos, look): k = 1 snaps, smaller follows smoothly.
        public void Aim(Vector3 pos, Vector3 look, float k = 1)
        {
            if (!placed || k >= 1) { Pos = pos; Look = look; placed = true; return; }
            Pos = Vector3.Lerp(Pos, pos, k); Look = Vector3.Lerp(Look, look, k);
        }
        public void Snap() { placed = false; }
        public void Render(Camera main, string path = null)
        {
            ReviewShared.CopyLook(main, Cam);
            var dir = Look - Pos; if (dir.sqrMagnitude < 1e-6f) dir = Vector3.forward;
            Cam.transform.SetPositionAndRotation(Pos, Quaternion.LookRotation(dir, Up));
            Cam.fieldOfView = Fov; Cam.rect = new Rect(0, 0, 1, 1); Cam.aspect = w / (float)h; Cam.targetTexture = rt;
            Cam.Render();
            var prev = RenderTexture.active; RenderTexture.active = rt;
            tex.ReadPixels(new Rect(0, 0, w, h), 0, 0); tex.Apply(); RenderTexture.active = prev;
            Cam.targetTexture = null;
            File.WriteAllBytes(path ?? Path.Combine(Dir, $"f_{Saved++:D5}.jpg"), tex.EncodeToJPG(88));
        }
    }

    public static class ReviewShared
    {
        static readonly FieldInfo rendererIndex = typeof(UniversalAdditionalCameraData).GetField("m_RendererIndex", BindingFlags.Instance | BindingFlags.NonPublic);
        public static string Env(string k, string d) => Environment.GetEnvironmentVariable(k) ?? d;

        /// The extra camera draws like the gameplay camera: same clear, culling, renderer, post-processing, AA and shadows.
        public static void CopyLook(Camera main, Camera cam)
        {
            if (!main) return;
            float near = main.nearClipPlane, far = main.farClipPlane;
            cam.clearFlags = main.clearFlags; cam.backgroundColor = main.backgroundColor; cam.cullingMask = main.cullingMask;
            cam.nearClipPlane = Mathf.Min(near, .1f); cam.farClipPlane = Mathf.Max(far, 2000f);
            cam.allowHDR = main.allowHDR; cam.allowMSAA = main.allowMSAA; cam.useOcclusionCulling = false; cam.depth = main.depth - 10;
            var a = main.GetUniversalAdditionalCameraData(); var b = cam.GetUniversalAdditionalCameraData();
            if (a && b)
            {
                b.renderPostProcessing = a.renderPostProcessing; b.antialiasing = a.antialiasing; b.antialiasingQuality = a.antialiasingQuality;
                b.renderShadows = a.renderShadows; b.volumeLayerMask = a.volumeLayerMask; b.stopNaN = a.stopNaN; b.dithering = a.dithering;
                b.requiresDepthOption = a.requiresDepthOption; b.requiresColorOption = a.requiresColorOption;
                if (rendererIndex != null) b.SetRenderer((int)rendererIndex.GetValue(a));
            }
        }

        public static Animator Humanoid(Component root)
        {
            if (!root) return null;
            foreach (var an in root.GetComponentsInChildren<Animator>(true)) if (an.isHuman && an.avatar) return an;
            return null;
        }
        /// The hero's chest direction (from the shoulder line), the head and feet heights.
        public static bool Frame(Component root, out Vector3 basePos, out Vector3 fwd, out Vector3 head, out float scale)
        {
            basePos = root ? root.transform.position : Vector3.zero; fwd = root ? root.transform.forward : Vector3.forward; head = basePos + Vector3.up * 1.6f; scale = 1;
            var an = Humanoid(root); if (!an) return false;
            var l = an.GetBoneTransform(HumanBodyBones.LeftUpperArm); var r = an.GetBoneTransform(HumanBodyBones.RightUpperArm);
            var hd = an.GetBoneTransform(HumanBodyBones.Head); var hips = an.GetBoneTransform(HumanBodyBones.Hips);
            var lf = an.GetBoneTransform(HumanBodyBones.LeftFoot); var rf = an.GetBoneTransform(HumanBodyBones.RightFoot);
            if (!l || !r || !hd || !hips) return false;
            var right = r.position - l.position; right.y = 0;
            if (right.sqrMagnitude > 1e-4f) fwd = Vector3.Cross(right.normalized, Vector3.up).normalized;
            float floor = lf && rf ? Mathf.Min(lf.position.y, rf.position.y) - .08f : hips.position.y - .95f;
            basePos = new Vector3(hips.position.x, floor, hips.position.z);
            head = hd.position + Vector3.up * .07f;
            scale = Mathf.Clamp((head.y - floor + .1f) / 1.72f, .5f, 3f);
            return true;
        }

        /// Seven stills of one hero: front, 3/4 left, left side, 3/4 back, back, face close-up, low full body.
        public static List<string> Stills(Camera main, Component root, string dir, string prefix, int w = 1200, int h = 1500)
        {
            var written = new List<string>();
            Directory.CreateDirectory(dir);
            Frame(root, out var b, out var f, out var head, out float s);
            var ang = new ReviewAngle("still", null, w, h);
            void Shot(string name, Vector3 pos, Vector3 look, float fov)
            {
                ang.Aim(pos, look); ang.Fov = fov;
                var path = Path.Combine(dir, $"{prefix}_{name}.jpg");
                ang.Render(main, path); ang.Render(main, path); written.Add(path);
            }
            Vector3 Around(float yaw, float dist, float hgt) => b + Quaternion.AngleAxis(yaw, Vector3.up) * f * dist * s + Vector3.up * hgt * s;
            var mid = b + Vector3.up * .9f * s;
            Shot("1_front", Around(0, 4.4f, 1.15f), mid, 30);
            Shot("2_34left", Around(-45, 4.4f, 1.15f), mid, 30);
            Shot("3_side", Around(-90, 4.4f, 1.15f), mid, 30);
            Shot("4_34back", Around(-135, 4.4f, 1.15f), mid, 30);
            Shot("5_back", Around(180, 4.4f, 1.15f), mid, 30);
            // the face from where the face looks: the eye line when the rig maps eyes, else the head bone's axis nearest the chest
            // direction (the head may be turned off the chest), at eye height
            var ff = f; var an = Humanoid(root); var eye = head + Vector3.up * .05f * s;
            if (an)
            {
                var hb = an.GetBoneTransform(HumanBodyBones.Head);
                var le = an.GetBoneTransform(HumanBodyBones.LeftEye); var re = an.GetBoneTransform(HumanBodyBones.RightEye);
                if (le && re && (le.position - re.position).sqrMagnitude > 1e-5f)
                { var er = re.position - le.position; er.y = 0; var e = Vector3.Cross(er.normalized, Vector3.up).normalized; if (Vector3.Dot(e, f) > -.2f) ff = e; eye = (le.position + re.position) * .5f; }
                else if (hb)
                {
                    float best = -2; var bestAxis = f;
                    foreach (var ax in new[] { hb.forward, -hb.forward, hb.up, -hb.up, hb.right, -hb.right }) { var hz = ax; hz.y = 0; if (hz.sqrMagnitude < .05f) continue; hz.Normalize(); float d = Vector3.Dot(hz, f); if (d > best) { best = d; bestAxis = hz; } }
                    ff = bestAxis; eye = hb.position + Vector3.up * .11f * s;
                }
            }
            Shot("6_face", eye + ff * .8f * s - Vector3.up * .04f * s, eye - Vector3.up * .04f * s, 30);
            Shot("7_lowfull", Around(22, 3.3f, .22f), b + Vector3.up * 1.0f * s, 44);
            Object.DestroyImmediate(ang.Cam.gameObject);
            return written;
        }
    }
}
#endif
