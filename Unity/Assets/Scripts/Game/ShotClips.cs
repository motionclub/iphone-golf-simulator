using System;
using System.Runtime.InteropServices;
using Unity.Collections;
using Unity.Collections.LowLevel.Unsafe;
using UnityEngine;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.RenderGraphModule.Util;
using UnityEngine.Rendering.Universal;

namespace GolfArcade.Game
{
    /// DAILY SHARE (Adnan 2026-11-21: "one click share their hole in one challenge, it takes a recording … can you beat my score",
    /// mockups in ArtDir/ui/daily-challenge-ui-mockups): films each of the Daily Hole in One's three shots so the phone can share
    /// a clip of them the moment the round ends.
    ///
    /// The course camera's own picture (after post-processing, before any HUD canvas) is copied into a 1280×720 texture 30 times a
    /// second while a shot is on, read back without stalling the GPU (AsyncGPUReadback) and handed to the app
    /// (SportsShotClips.mm → DailyShareClips.swift), which encodes it and later cuts the shots together with the score cards.
    /// One small blit a frame, no second render of the course, and it works the same on a TV and in handheld play (the camera is
    /// filmed, not a display). Nothing runs outside the daily challenge.
    ///
    /// Per shot: Arm at address → Contact at the strike → Rest when it is scored → Close `TailSeconds` later. The app trims each
    /// shot to a little before the strike and a little after the rest, so a long wait at address costs nothing in the clip.
    public sealed class ShotClips : MonoBehaviour
    {
        public const int Width = 1280, Height = 720, Fps = 30;
        /// Filming goes on this long after the ball stops (the app keeps ~2 s of it).
        public const float TailSeconds = 2.4f;
        /// A shot not struck this long after address starts its file over (the app only keeps the last seconds before the strike).
        public const float MaxAddressSeconds = 75f;
        /// A ball that never comes to rest still ends its clip.
        public const float MaxFlightSeconds = 30f;

        public enum Kind { Arm = 1, Contact = 2, Rest = 3, Close = 4, Cancel = 5 }

        /// For the editor and tests (there is no app there): every event and frame as the app would get it. Frames are BGRA, bottom row first.
        public static Action<Kind, int, double, double, int, bool> EditorEvent;
        public static Action<byte[], int, int, double> EditorFrame;

        static ShotClips instance;
        public static bool Supported => SystemInfo.supportsAsyncGPUReadback;
        /// Which shot is being filmed (-1: none) and what it is waiting for, for the tests.
        public static int Shot => instance ? instance.shot : -1;
        public static bool Filming => instance && instance.target;
        public static int FramesSent => instance ? instance.sent : 0;

        Camera target;
        int shot = -1, sent;
        double armedAt, contactAt, restAt, lastFrame = -1;
        RenderTexture texture, encodedTexture; RTHandle handle, encodedHandle; CapturePass pass;
        /// The camera picture's format, as the last frame found it (for the logs and tests).
        public static GraphicsFormat SourceFormat { get; private set; }
        byte[] editorBuffer;

        static ShotClips Get()
        {
            if (instance) return instance;
            var go = new GameObject("Shot clips (daily share)") { hideFlags = HideFlags.HideAndDontSave };
            if (Application.isPlaying) DontDestroyOnLoad(go);
            instance = go.AddComponent<ShotClips>();
            return instance;
        }

        // ----- what GolfGame.HoleInOne.cs calls

        /// The shot is at address: start filming `camera` (the course camera) for shot `index` (0-based).
        public static void Arm(Camera camera, int index)
        {
            if (!Supported || !camera) return;
#if UNITY_IOS && !UNITY_EDITOR
            if (!SportsShotClips_Wanted()) return;   // the app shares no clip (the Friend Challenge shares a card): film nothing
#endif
            var c = Get();
            if (c.target) c.Send(Kind.Cancel, c.shot);
            c.target = camera; c.shot = index; c.sent = 0; c.lastFrame = -1;
            c.armedAt = Now; c.contactAt = c.restAt = -1;
            c.Send(Kind.Arm, index);
        }

        /// The club met the ball.
        public static void Contact()
        {
            if (!instance || !instance.target || instance.contactAt >= 0) return;
            instance.contactAt = Now; instance.Send(Kind.Contact, instance.shot);
        }

        /// The shot is scored: where it stopped (feet; 0 holed, -1 in a hazard), its points. Filming ends TailSeconds later.
        public static void Rest(int index, double feet, int points, bool holed)
        {
            if (!instance || !instance.target || instance.shot != index || instance.restAt >= 0) return;
            instance.restAt = Now; instance.Send(Kind.Rest, index, feet, points, holed);
        }

        /// Stop without keeping the shot (the round was left).
        public static void Cancel()
        {
            if (!instance || !instance.target) return;
            instance.Send(Kind.Cancel, instance.shot); instance.Stop();
        }

        /// The clock frames and events are stamped with: the real one in play; a proof run films game time instead (captureFramerate).
        public static Func<double> ClockOverride;
        static double Now => ClockOverride?.Invoke() ?? Time.realtimeSinceStartupAsDouble;

        void Stop() { target = null; shot = -1; contactAt = restAt = -1; }

        void OnEnable() { RenderPipelineManager.beginCameraRendering += BeginCamera; }
        void OnDisable() { RenderPipelineManager.beginCameraRendering -= BeginCamera; }
        void OnDestroy()
        {
            handle?.Release(); handle = null; encodedHandle?.Release(); encodedHandle = null;
            if (texture) { texture.Release(); Destroy(texture); }
            if (encodedTexture) { encodedTexture.Release(); Destroy(encodedTexture); }
            if (instance == this) instance = null;
        }

        void Update()
        {
            if (!target) { if (shot >= 0) Stop(); return; }
            double now = Now;
            if (restAt >= 0 && now - restAt >= TailSeconds) { Send(Kind.Close, shot); Stop(); return; }
            if (contactAt >= 0 && restAt < 0 && now - contactAt > MaxFlightSeconds) { Send(Kind.Close, shot); Stop(); return; }
            // a long wait at address: the app starts the shot's file over (it keeps only the run-up to the strike)
            if (contactAt < 0 && now - armedAt > MaxAddressSeconds) { int s = shot; var cam = target; Arm(cam, s); }
        }

        /// A course camera frame is about to render: when one is due (30 a second), add the copy to it.
        void BeginCamera(ScriptableRenderContext context, Camera camera)
        {
            if (camera != target || shot < 0) return;
            double now = Now;
            if (lastFrame >= 0 && now - lastFrame < 1.0 / Fps - .004) return;
            var data = camera.GetUniversalAdditionalCameraData();
            if (data == null || data.scriptableRenderer == null) return;
            lastFrame = now;
            Prepare();
            var px = camera.pixelRect;
            pass.Setup(handle, encodedHandle, px.width, px.height, now, shot, this);
            data.scriptableRenderer.EnqueuePass(pass);
        }

        void Prepare()
        {
            if (texture && texture.IsCreated() && encodedTexture && encodedTexture.IsCreated()) return;
            // a linear picture (sRGB or float target) is written through an sRGB frame, which encodes it for display; an 8-bit
            // non-sRGB target already holds display values (URP converts on its last post pass), so it is copied as it is
            // (11-21: encoding that one again washed the clip out, lime grass and a white sky)
            texture = new RenderTexture(new RenderTextureDescriptor(Width, Height, GraphicsFormat.R8G8B8A8_SRGB, 0)) { name = "Shot clip frame" };
            encodedTexture = new RenderTexture(new RenderTextureDescriptor(Width, Height, GraphicsFormat.R8G8B8A8_UNorm, 0)) { name = "Shot clip frame (display values)" };
            texture.Create(); encodedTexture.Create();
            handle?.Release(); encodedHandle?.Release();
            handle = RTHandles.Alloc(texture); encodedHandle = RTHandles.Alloc(encodedTexture);
            pass ??= new CapturePass();
        }

        /// Fills the 16:9 frame from the middle of the camera's picture (a wider or taller view is cropped, never squashed).
        public static void Fit(float width, float height, out Vector2 scale, out Vector2 offset)
        {
            float aspect = height > 0 ? width / height : 16f / 9f, want = (float)Width / Height;
            scale = Vector2.one;
            if (aspect > want) scale.x = want / aspect; else if (aspect < want) scale.y = aspect / want;
            offset = new Vector2((1 - scale.x) * .5f, (1 - scale.y) * .5f);
        }

        void Readback(AsyncGPUReadbackRequest request, double stamp, int forShot)
        {
            if (request.hasError || forShot != shot || !target) return;
            var data = request.GetData<byte>();
            if (data.Length < Width * Height * 4) return;
            sent++;
#if UNITY_IOS && !UNITY_EDITOR
            unsafe { SportsShotClips_Frame((IntPtr)NativeArrayUnsafeUtility.GetUnsafeReadOnlyPtr(data), Width, Height, Width * 4, stamp); }
#else
            if (EditorFrame == null) return;
            editorBuffer ??= new byte[Width * Height * 4];
            data.CopyTo(editorBuffer);
            EditorFrame(editorBuffer, Width, Height, stamp);
#endif
        }

        void Send(Kind kind, int index, double feet = 0, int points = 0, bool holed = false)
        {
            double now = Now;
#if UNITY_IOS && !UNITY_EDITOR
            SportsShotClips_Event((int)kind, index, now, feet, points, holed ? 1 : 0);
#endif
            EditorEvent?.Invoke(kind, index, now, feet, points, holed);
        }

#if UNITY_IOS && !UNITY_EDITOR
        [DllImport("__Internal")] static extern void SportsShotClips_Event(int kind, int shot, double time, double feet, int points, int holed);
        [DllImport("__Internal")] static extern void SportsShotClips_Frame(IntPtr bgra, int width, int height, int stride, double time);
        [DllImport("__Internal")] [return: MarshalAs(UnmanagedType.I1)] static extern bool SportsShotClips_Wanted();
#endif

        /// The copy: the camera's finished picture (after post-processing, before the HUD) into the clip frame, then read back.
        sealed class CapturePass : ScriptableRenderPass
        {
            RTHandle linearInto, displayInto; Vector2 scale, offset; double stamp; int forShot; ShotClips owner;

            public CapturePass()
            {
                renderPassEvent = RenderPassEvent.AfterRenderingPostProcessing;
                requiresIntermediateTexture = true;   // the picture must be a texture to copy from, not the screen
                profilingSampler = new ProfilingSampler("Shot clip capture");
            }

            public void Setup(RTHandle linear, RTHandle display, float width, float height, double at, int index, ShotClips by)
            {
                linearInto = linear; displayInto = display; stamp = at; forShot = index; owner = by;
                Fit(width, height, out scale, out offset);
            }

            sealed class Data { public RenderTexture texture; public double stamp; public int shot; public ShotClips owner; }

            public override void RecordRenderGraph(RenderGraph graph, ContextContainer frameData)
            {
                var resources = frameData.Get<UniversalResourceData>();
                if (resources.isActiveTargetBackBuffer || linearInto == null || !resources.activeColorTexture.IsValid()) return;
                var format = graph.GetTextureDesc(resources.activeColorTexture).format;
                if (format != SourceFormat) { SourceFormat = format; Debug.Log($"[ShotClips] camera picture format {format}"); }
                bool displayValues = QualitySettings.activeColorSpace == ColorSpace.Linear
                    && GraphicsFormatUtility.IsUNormFormat(format) && !GraphicsFormatUtility.IsSRGBFormat(format);
                var destination = displayValues ? displayInto : linearInto;
                var into = graph.ImportTexture(destination);
                graph.AddBlitPass(resources.activeColorTexture, into, scale, offset, passName: "Shot clip blit");
                using var builder = graph.AddUnsafePass<Data>("Shot clip readback", out var data, profilingSampler);
                data.texture = destination.rt; data.stamp = stamp; data.shot = forShot; data.owner = owner;
                builder.UseTexture(into, AccessFlags.Read);
                builder.AllowPassCulling(false);
                builder.SetRenderFunc((Data d, UnsafeGraphContext context) =>
                {
                    var cmd = CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);
                    double at = d.stamp; int s = d.shot; var by = d.owner;
                    cmd.RequestAsyncReadback(d.texture, 0, TextureFormat.BGRA32, r => { if (by) by.Readback(r, at, s); });
                });
            }
        }
    }
}
