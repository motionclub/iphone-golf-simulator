using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace GolfArcade.Bowling
{
    /// The lanes' planar mirror (the lacquer look of every real centre and of the Wii/Switch bowling alleys):
    /// a camera under the floor (y = 0) renders the scene at half resolution into _BowlingLaneReflection after
    /// the main camera has moved; GolfArcade/BowlingLane samples it in screen space. The camera is a proper
    /// one (no flipped winding): its picture is the mirror flipped left-right, which the shader undoes.
    [DefaultExecutionOrder(10000)]
    public sealed class BowlingLaneMirror : MonoBehaviour
    {
        public static bool Enabled = true;
        static readonly int ReflectionId = Shader.PropertyToID("_BowlingLaneReflection");
        static BowlingLaneMirror active;
        Camera mirror;
        RenderTexture rt;

        void OnEnable() => active = this;
        void OnDisable() { if (active == this) active = null; Shader.SetGlobalTexture(ReflectionId, Texture2D.blackTexture); }
        void OnDestroy() { if (rt) { rt.Release(); Destroy(rt); } }

        /// Re-render the mirror for the main camera's current pose (offscreen captures move the camera and
        /// render it straight away, before this component's LateUpdate).
        public static void RenderNow() { if (active) active.Render(); }

        void LateUpdate() => Render();

        void Render()
        {
            var main = Camera.main;
            if (!Enabled || !main) { Shader.SetGlobalTexture(ReflectionId, Texture2D.blackTexture); return; }
            if (!mirror)
            {
                var go = new GameObject("LaneMirrorCamera"); go.transform.SetParent(transform, false);
                mirror = go.AddComponent<Camera>(); mirror.enabled = false;
                var data = mirror.GetUniversalAdditionalCameraData();
                data.renderShadows = false; data.renderPostProcessing = false;
                data.requiresColorOption = CameraOverrideOption.Off; data.requiresDepthOption = CameraOverrideOption.Off;
                data.antialiasing = AntialiasingMode.None;
            }
            int w = Mathf.Max(64, main.pixelWidth / 2), h = Mathf.Max(64, main.pixelHeight / 2);
            if (!rt || rt.width != w || rt.height != h)
            {
                if (rt) { rt.Release(); Destroy(rt); }
                rt = new RenderTexture(w, h, 16, RenderTextureFormat.DefaultHDR) { name = "LaneMirror", useMipMap = false };
            }
            mirror.CopyFrom(main);
            mirror.enabled = false; mirror.targetTexture = rt; mirror.depth = main.depth - 1;
            mirror.farClipPlane = Mathf.Min(main.farClipPlane, 45);
            // the pose: reflected position, reflected forward and up (a proper camera, upside down under the floor)
            var p = main.transform.position; var f = main.transform.forward; var u = main.transform.up;
            mirror.transform.SetPositionAndRotation(new Vector3(p.x, -p.y, p.z), Quaternion.LookRotation(new Vector3(f.x, -f.y, f.z), new Vector3(u.x, -u.y, u.z)));
            // clip everything below the lane surface (the pit, the gutters' undersides) with an oblique near plane
            mirror.ResetProjectionMatrix();
            var m = mirror.worldToCameraMatrix;
            var cn = m.MultiplyVector(Vector3.up).normalized;
            var cp = m.MultiplyPoint(new Vector3(0, .002f, 0));
            mirror.projectionMatrix = mirror.CalculateObliqueMatrix(new Vector4(cn.x, cn.y, cn.z, -Vector3.Dot(cp, cn)));
            mirror.Render();
            Shader.SetGlobalTexture(ReflectionId, rt);
        }
    }
}
