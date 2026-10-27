using System;
using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Records the last few seconds of every rendered frame -- both players' full skeletons,
    /// their rackets and the ball -- and plays a winner back in slow motion from a low
    /// camera from the umpire's chair. Storage is fixed at build time; recording never allocates.
    ///
    /// Capture and playback both run in LateUpdate, after the hero animation (HeroTennisDriver, order 1000) and the
    /// arm and clearance passes (order 10000) have posed the visible characters. Recording from TennisGame's Update
    /// caught the skeletons before the heroes were posed, and in playback the driver re-posed them over the replay:
    /// that was why replays were switched off (2026-10-26).
    [DefaultExecutionOrder(31000)]
    public sealed class TennisReplay : MonoBehaviour
    {
        public const int Frames = 200;          // ~3.3s at 60fps
        public const float Slowdown = .45f;     // playback speed
        Transform[] tracked;
        Vector3[] positions;
        Quaternion[] rotations;
        float[] stamps;
        int head, recorded;
        int transformsPerFrame;
        public bool Playing { get; private set; }
        float playTime, startStamp, endStamp;
        Transform ball;
        Action<bool> onPose;
        Camera cam;
        Vector3 cameraRestPosition; Quaternion cameraRestRotation;
        /// The live frame at the moment playback started, restored afterwards so play resumes
        /// exactly where it was rather than from the replay's last frame.
        Vector3[] livePositions; Quaternion[] liveRotations;

        /// `roots` are recorded in full (every child transform), in world space.
        public void Build(IList<Transform> roots, Transform ballTransform, Camera camera, Action<bool> refresh)
        {
            var list = new List<Transform>();
            foreach (var r in roots) list.AddRange(r.GetComponentsInChildren<Transform>(true));
            list.Add(ballTransform);
            tracked = list.ToArray();
            transformsPerFrame = tracked.Length;
            positions = new Vector3[Frames * transformsPerFrame];
            rotations = new Quaternion[Frames * transformsPerFrame];
            stamps = new float[Frames];
            livePositions = new Vector3[transformsPerFrame]; liveRotations = new Quaternion[transformsPerFrame];
            head = 0; recorded = 0;
            ball = ballTransform; cam = camera; onPose = refresh;
        }

        /// Ask for this frame to be captured once it is fully posed (in LateUpdate).
        public void Record(float time) { recordAt = time; recordPending = true; }
        bool recordPending; float recordAt;
        /// Playback: the two recorded frames either side of the playback time and the blend between them,
        /// applied in LateUpdate over whatever posed the characters this frame; and where the camera wants to be.
        int poseA = -1, poseC; float poseT; Vector3 camGoal; Quaternion camLook; bool camSet;

        void LateUpdate()
        {
            if (Playing) { ApplyPose(); return; }
            if (recordPending) { recordPending = false; Capture(recordAt); }
        }

        void Capture(float time)
        {
            if (Playing || tracked == null) return;
            int offset = head * transformsPerFrame;
            for (int i = 0; i < transformsPerFrame; i++)
            {
                var t = tracked[i];
                if (!t) continue;
                positions[offset + i] = t.position; rotations[offset + i] = t.rotation;
            }
            stamps[head] = time;
            head = (head + 1) % Frames; recorded = Mathf.Min(Frames, recorded + 1);
        }

        /// Play back the last `seconds` of recorded play, ending `trim` seconds before now.
        public bool Play(float seconds, float trim = 0)
        {
            if (recorded < 20 || tracked == null) return false;
            int newest = (head - 1 + Frames) % Frames;
            endStamp = stamps[newest] - trim;
            startStamp = Mathf.Max(stamps[(head - recorded + Frames) % Frames], endStamp - seconds);
            playTime = startStamp;
            Playing = true; poseA = -1; camSet = false;
            cameraRestPosition = cam.transform.position; cameraRestRotation = cam.transform.rotation;
            for (int i = 0; i < transformsPerFrame; i++)
                if (tracked[i]) { livePositions[i] = tracked[i].position; liveRotations[i] = tracked[i].rotation; }
            var trail = ball ? ball.GetComponent<TrailRenderer>() : null; if (trail) trail.Clear();
            onPose?.Invoke(true);
            return true;
        }

        public void Stop()
        {
            if (!Playing) return;
            Playing = false;
            cam.transform.SetPositionAndRotation(cameraRestPosition, cameraRestRotation);
            for (int i = 0; i < transformsPerFrame; i++)
                if (tracked[i]) tracked[i].SetPositionAndRotation(livePositions[i], liveRotations[i]);
            var trail = ball ? ball.GetComponent<TrailRenderer>() : null; if (trail) trail.Clear();
            onPose?.Invoke(false);
        }

        /// Advance playback. Returns false once finished.
        public bool Tick(float dt)
        {
            if (!Playing) return false;
            playTime += dt * Slowdown;
            if (playTime >= endStamp) { Stop(); return false; }
            // Find the two recorded frames either side of the playback time.
            int newest = (head - 1 + Frames) % Frames;
            int b = newest;
            for (int n = 0; n < recorded; n++)
            {
                int i = (newest - n + Frames) % Frames;
                if (stamps[i] <= playTime) { b = i; break; }
            }
            int a = b, c = (b + 1) % Frames;
            if (c == head) c = b;
            float span = stamps[c] - stamps[a];
            float t = span > 1e-5f ? Mathf.Clamp01((playTime - stamps[a]) / span) : 0;
            poseA = a; poseC = c; poseT = t;
            // The umpire's view: high in the chair at the net, looking down the court and
            // turning to follow the ball, so the whole point reads from above.
            int ballIndex = transformsPerFrame - 1;
            Vector3 focus = Vector3.Lerp(positions[a * transformsPerFrame + ballIndex], positions[c * transformsPerFrame + ballIndex], t);
            Vector3 eye = TennisUmpire.Seat + new Vector3(.7f, 2.1f, Mathf.Clamp(focus.z * .12f, -1.5f, 1.5f));
            Vector3 from = camSet ? camGoal : cam.transform.position; Quaternion fromLook = camSet ? camLook : cam.transform.rotation;
            camGoal = Vector3.Lerp(from, eye, 1 - Mathf.Exp(-dt * 4));
            camLook = Quaternion.Slerp(fromLook, Quaternion.LookRotation(new Vector3(focus.x * .6f, Mathf.Max(.4f, focus.y * .5f), focus.z) - camGoal), 1 - Mathf.Exp(-dt * 6));
            camSet = true;
            return true;
        }

        /// The recorded pose for this frame, laid over the live animation (and the replay camera over any rig).
        void ApplyPose()
        {
            if (poseA < 0) return;
            int oa = poseA * transformsPerFrame, oc = poseC * transformsPerFrame;
            for (int i = 0; i < transformsPerFrame; i++)
            {
                var tr = tracked[i]; if (!tr) continue;
                tr.SetPositionAndRotation(Vector3.Lerp(positions[oa + i], positions[oc + i], poseT),
                                          Quaternion.Slerp(rotations[oa + i], rotations[oc + i], poseT));
            }
            onPose?.Invoke(true);   // the arms follow the replayed body (without it a hand stayed ~2.6 m off, at its live spot)
            if (camSet) cam.transform.SetPositionAndRotation(camGoal, camLook);
        }
    }
}
