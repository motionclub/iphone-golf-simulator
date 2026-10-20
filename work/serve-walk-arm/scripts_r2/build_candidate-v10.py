from pathlib import Path
P=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=P/'work/serve-walk-arm';C=W/'CandidateR2Clone/Assets/Scripts/Tennis';B=W/'rollback/r2/Unity/Assets/Scripts/Tennis'
s=(B/'HeroTennisDriver.cs').read_text()
s=s.replace('                pts[p] = transform.InverseTransformPoint(palm);', '                pts[p] = transform.InverseTransformPoint(palm);\n                if (p == 1) releasePalmOffsetLocal = transform.InverseTransformVector(palm - hand.position);')
s=s.replace('walkYaw = Mathf.MoveTowardsAngle(walkYaw, yawTo, dt * 420f);', 'walkYaw = Mathf.MoveTowardsAngle(walkYaw, yawTo, dt * (Match && actor.PrepareServe ? (Moving() > .2f ? 40f : 100f) : 420f));')
s=s.replace('            PostProcess(swinging);','            serveFinalPose = true;\n            ServeRootFrame = Time.frameCount;\n            PostProcess(swinging);\n            serveFinalPose = false;',1)
s=s.replace('            if (Match) return tossPoints != null ? Quaternion.Euler(0, serveYaw + walkYaw, 0) * tossPoints[Mathf.Clamp(k, 0, 2)] : (Vector3?)null;', '            if (Match) return k == 0 && matchHoldValid ? matchHoldLocal : tossPoints != null ? Quaternion.Euler(0, serveYaw + walkYaw, 0) * tossPoints[Mathf.Clamp(k, 0, 2)] : (Vector3?)null;')
needle='        static readonly Vector3 CarryPoint = new Vector3(-.3f, .66f, .08f);'
insert=r'''        // Final match reach runs after this frame's visual yaw, root and skin source pose.
        // Gameplay still owns the serve clock; this resolves its held-ball geometry for drawing.
        bool serveFinalPose, matchHoldValid, wristReady, wasServePre; Vector3 carryTravel;
        Vector3 matchHoldLocal, reachWrist, reachVelocity, reachActorPosition, previousWanted;
        float matchCarryT, lastPrepare; Vector3 windupWrist, releasePalmOffsetLocal;
        public int ServeRootFrame { get; private set; } = -1;
        public int ServeTargetFrame { get; private set; } = -1;
        public bool ServeBallInHand { get; private set; }
        public string ServeBallState { get; private set; } = "unbound";
        public Vector3 ServeWristTarget { get; private set; }
        void MatchServeArm(Transform up, Transform lo, Transform hand)
        {
            if (!serveFinalPose) return;
            float dt = Mathf.Max(.00001f, Time.deltaTime);
            bool pre = game && ((actor == game.Player && game.Flow == TennisGame.Phase.PlayerServeHold)
                || (actor == game.Opponent && game.Flow == TennisGame.Phase.OpponentServe && game.ServeReachClock(actor) < TennisRules.ServeTossDelay));
            bool justReleased = !pre && wasServePre;
            bool opponentServer = game && actor == game.Opponent;
            float prepare = opponentServer && pre ? .4f * Mathf.Clamp01((game.ServeReachClock(actor) - (TennisRules.ServeTossDelay - .5f)) / .5f) : actor.PrepareAmount;
            bool carry = pre && prepare <= .001f && Moving() > .2f;
            matchCarryT = Mathf.MoveTowards(matchCarryT, carry ? 1 : 0, dt / .35f);
            Vector3 side = Vector3.ProjectOnPlane(up.position - Bone(HumanBodyBones.RightUpperArm).position, Vector3.up).normalized;
            Vector3 forward = Vector3.Cross(Vector3.up, side);
            if (Moving() > .1f) carryTravel = Vector3.ProjectOnPlane(actor.transform.right * Mathf.Sign(actor.Speed), Vector3.up).normalized;
            if (carryTravel.sqrMagnitude < .5f) carryTravel = actor.transform.forward;
            Transform mid = Bone(HumanBodyBones.LeftMiddleProximal), index = Bone(HumanBodyBones.LeftIndexProximal);
            if (pre && prepare <= .001f && mid && index)
            {
                Vector3 view = game.GameplayCamera ? (game.GameplayCamera.transform.position - hand.position).normalized : forward;
                Vector3 fingers = carryTravel;
                hand.rotation = Quaternion.FromToRotation(mid.position - hand.position, fingers) * hand.rotation;
                Vector3 gripNormal = Vector3.Cross(mid.position - hand.position, index.position - hand.position).normalized;
                hand.rotation = Quaternion.AngleAxis(Vector3.SignedAngle(gripNormal, Vector3.ProjectOnPlane(view, fingers).normalized, fingers), fingers) * hand.rotation;
            }
            Vector3 palmOffset = mid ? Vector3.Lerp(hand.position, mid.position, .7f) - hand.position : Vector3.zero;
            Vector3 gripOffset = pre && prepare <= .001f ? carryTravel * .034f : Vector3.zero;
            Vector3 normal = mid && index ? Vector3.Cross(mid.position - hand.position, index.position - hand.position).normalized : -side;
            Quaternion rotation = hand.rotation;
            Vector3 hip = Bone(HumanBodyBones.Hips).position;
            float carryScale = Mathf.Clamp((Vector3.Distance(up.position, lo.position) + Vector3.Distance(lo.position, hand.position) - .4f) / .108f, .4f, 1);
            Vector3 lowWrist = up.position + (carryTravel + side * .15f).normalized * (.076f + .1f * carryScale);
            lowWrist.y = hip.y - Mathf.Lerp(.010f, .022f, carryScale * carryScale * carryScale);
            float gait = valid[(int)Clip.Walk] ? (float)time[(int)Clip.Walk] / length[(int)Clip.Walk] * Mathf.PI * 2 : 0;
            lowWrist += forward * (.018f * carryScale * Mathf.Sin(gait) * matchCarryT);
            if (gripOffset.sqrMagnitude < .00001f) gripOffset = normal * .03f;
            Vector3 holdBall = lowWrist + palmOffset + gripOffset;
            if (prepare <= .001f) { matchHoldLocal = actor.transform.InverseTransformPoint(holdBall); matchHoldValid = true; }
            Vector3 wantedPalm = actor.TossReachTarget, heldBall = game ? game.BallPosition : wantedPalm;
            bool inHand = false;
            if (pre && TennisServeRoutine.TryCurrentTime(actor, out float routine))
            {
                TennisServeRoutine.Pose(actor, carry ? 0 : routine, out heldBall, out wantedPalm);
                inHand = TennisServeRoutine.InHand(actor, carry ? 0 : routine);
                ServeBallState = inHand ? (carry ? "carry" : "held") : "bounce_flight";
            }
            else ServeBallState = "released";
            ServeBallInHand = inHand;
            Vector3 offset = pre && prepare <= .001f ? -normal * .03f : Vector3.up * (actor.PrepareAmount <= .001f ? .045f : -.045f);
            Vector3 wanted = wantedPalm + offset - palmOffset;
            if (pre && prepare <= .001f) wanted = lowWrist;
            if (pre && prepare > .001f)
            {
                if (lastPrepare <= .001f) windupWrist = reachWrist;
                float u = Mathf.Clamp01(prepare / .4f), ramp = .1f;
                float progress = u < ramp ? u * u / (2 * ramp * (1 - ramp))
                    : u > 1 - ramp ? 1 - (1 - u) * (1 - u) / (2 * ramp * (1 - ramp)) : (u - ramp * .5f) / (1 - ramp);
                Vector3 releaseWrist = TennisServeRoutine.Release(actor) - Vector3.up * .045f - transform.TransformVector(releasePalmOffsetLocal);
                if (opponentServer)
                {
                    Vector3 firstGoal = TennisServeRoutine.Release(actor) - Vector3.up * .045f - palmOffset;
                    float span = Vector3.Distance(up.position, lo.position) + Vector3.Distance(lo.position, hand.position) - .001f;
                    releaseWrist = up.position + Vector3.ClampMagnitude(firstGoal - up.position, span);
                }
                wanted = Vector3.Lerp(windupWrist, releaseWrist, progress);
            }
            lastPrepare = prepare;
            wanted = GuardServePoint(wanted, .04f);
            float upper = Vector3.Distance(up.position, lo.position), lower = Vector3.Distance(lo.position, hand.position);
            if (carry)
            {
                float min = Mathf.Sqrt(upper * upper + lower * lower + 2 * upper * lower * Mathf.Cos(58 * Mathf.Deg2Rad));
                float max = Mathf.Sqrt(upper * upper + lower * lower + 2 * upper * lower * Mathf.Cos(18 * Mathf.Deg2Rad));
                Vector3 direction = wanted - up.position;
                wanted = up.position + direction.normalized * Mathf.Clamp(direction.magnitude, min, max);
                wanted.y = Mathf.Min(wanted.y, hip.y - .002f);
            }
            bool teleported = ServeTargetFrame >= 0 && Vector3.Distance(actor.transform.position, reachActorPosition) > .3f;
            if (!wristReady || teleported)
            { reachWrist = teleported ? wanted : hand.position; reachVelocity = Vector3.zero; previousWanted = wanted; wristReady = true; }
            reachActorPosition = actor.transform.position;
            Vector3 desiredVelocity = Vector3.ClampMagnitude((wanted - previousWanted) / dt + (wanted - reachWrist) * 12f, 1.79f);
            if (pre && prepare > .001f) desiredVelocity = Vector3.ClampMagnitude((wanted - reachWrist) / dt, 1.79f);
            previousWanted = wanted;
            reachVelocity = Vector3.MoveTowards(reachVelocity, desiredVelocity, 30f * dt);
            Vector3 next = reachWrist + reachVelocity * dt;

            next = GuardServePoint(next, .04f);
            Vector3 previousWrist = reachWrist;
            reachWrist = next;
            if (justReleased && actor.PrepareServe)
            {
                float age = opponentServer ? Mathf.Max(0, TennisServeRoutine.CurrentTime(actor) - TennisRules.ServeTossDelay)
                    : Mathf.Max(0, (actor.PrepareAmount - .4f) / .6f * TennisRules.ServeApex);
                Vector3 start = TennisServeRoutine.TossPalm(actor, age) + Vector3.up * (actor.PrepareAmount <= .001f ? .045f : -.045f) - palmOffset;
                TwoBone(up, lo, hand, GuardServePoint(start, .04f));
                reachVelocity = (hand.position - previousWrist) / dt;
            }
            else SolveServeArm(up, lo, hand, reachWrist, side, forward, pre);
            hand.rotation = rotation;
            reachWrist = hand.position; ServeWristTarget = reachWrist;
            Vector3 finalPalm = mid ? Vector3.Lerp(hand.position, mid.position, .7f) : hand.position;
            if (pre)
            {
                if (inHand) heldBall = finalPalm + gripOffset;
                game.ResolveServeReachVisual(actor, heldBall);
                actor.ReachTossHand(finalPalm - offset, 1);
            }
            ServeTargetFrame = Time.frameCount; wasServePre = pre;
        }
        Vector3 GuardServePoint(Vector3 point, float pad)
        {
            for (int pass = 0; pass < 3; pass++)
            {
                point = OutsideServeCapsule(point, Bone(HumanBodyBones.Hips).position, Bone(HumanBodyBones.Spine).position, .16f + pad);
                point = OutsideServeCapsule(point, Bone(HumanBodyBones.Spine).position, Bone(HumanBodyBones.UpperChest).position, .16f + pad);
                point = OutsideServeCapsule(point, Bone(HumanBodyBones.LeftUpperLeg).position, Bone(HumanBodyBones.LeftLowerLeg).position, .095f + pad);
                point = OutsideServeCapsule(point, Bone(HumanBodyBones.RightUpperLeg).position, Bone(HumanBodyBones.RightLowerLeg).position, .095f + pad);
            }
            return point;
        }
        static Vector3 OutsideServeCapsule(Vector3 p, Vector3 a, Vector3 b, float radius)
        {
            Vector3 ab = b - a; float t = ab.sqrMagnitude > 1e-8f ? Mathf.Clamp01(Vector3.Dot(p - a, ab) / ab.sqrMagnitude) : 0;
            Vector3 c = a + ab * t, d = p - c;
            return d.sqrMagnitude >= radius * radius ? p : c + (d.sqrMagnitude > 1e-8f ? d.normalized : Vector3.forward) * radius;
        }
        void SolveServeArm(Transform up, Transform lo, Transform hand, Vector3 wanted, Vector3 side, Vector3 forward, bool guard)
        {
            float a = Vector3.Distance(up.position, lo.position), b = Vector3.Distance(lo.position, hand.position);
            Vector3 v = wanted - up.position; float d = Mathf.Clamp(v.magnitude, Mathf.Abs(a - b) + .001f, a + b - .001f); Vector3 dir = v.normalized;
            float along = (a * a - b * b + d * d) / (2 * d), h = Mathf.Sqrt(Mathf.Max(0, a * a - along * along));
            Vector3 outside = Vector3.ProjectOnPlane(side * .9f + forward * .4f - Vector3.up * .15f, dir).normalized;
            Vector3 authored = Vector3.ProjectOnPlane(lo.position - up.position, dir).normalized;
            float releaseBlend = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.24f, .39f, lastPrepare));
            Vector3 basePole = Vector3.Slerp(outside, authored, releaseBlend).normalized;
            Vector3 chosen = up.position + dir * along + basePole * h;
            if (false)
            {
                float best = float.PositiveInfinity;
                for (int k = 0; k < 36; k++)
                {
                    Vector3 elbow = up.position + dir * along + Quaternion.AngleAxis(k * 10, dir) * basePole * h; float cost = 0;
                    for (int n = 1; n <= 7; n++)
                    {
                        Vector3 p = Vector3.Lerp(up.position, elbow, n / 7f); cost += (GuardServePoint(p, .045f) - p).sqrMagnitude;
                        p = Vector3.Lerp(elbow, up.position + dir * d, n / 7f); cost += (GuardServePoint(p, .035f) - p).sqrMagnitude;
                    }
                    cost = cost * 10000 + (elbow - chosen).sqrMagnitude * .001f;
                    if (cost < best) { best = cost; chosen = elbow; }
                }
            }
            up.rotation = Quaternion.FromToRotation(lo.position - up.position, chosen - up.position) * up.rotation;
            lo.rotation = Quaternion.FromToRotation(hand.position - lo.position, up.position + dir * d - lo.position) * lo.rotation;
        }
'''
s=s.replace(needle,insert+'\n'+needle)
s=s.replace('            tossWeight = Mathf.MoveTowards(tossWeight, want, Time.deltaTime / .12f);', '            if (Match && game && ((actor == game.Player && game.Flow == TennisGame.Phase.PlayerServeHold) || (actor == game.Opponent && game.Flow == TennisGame.Phase.OpponentServe && game.ServeReachClock(actor) < TennisRules.ServeTossDelay))) want = 1;\n            tossWeight = Mathf.MoveTowards(tossWeight, want, Time.deltaTime / .12f);')
s=s.replace('            if (tossWeight <= .001f) return;','            if (tossWeight <= .001f) { wristReady = false; return; }',1)
s=s.replace('            var a = Anim;\n            Transform up = Bone(HumanBodyBones.LeftUpperArm), lo = Bone(HumanBodyBones.LeftLowerArm), hand = Bone(HumanBodyBones.LeftHand);','            var a = Anim;\n            Transform up = Bone(HumanBodyBones.LeftUpperArm), lo = Bone(HumanBodyBones.LeftLowerArm), hand = Bone(HumanBodyBones.LeftHand);\n            if (Match && Application.isPlaying) { MatchServeArm(up, lo, hand); return; }',1)
(C/'HeroTennisDriver.cs').write_text(s)
s=(B/'TennisServeRoutine.cs').read_text().replace('using UnityEngine;','using UnityEngine;\nusing System.Collections.Generic;')
s=s.replace('        const float Gravity = 9.81f;',r'''        const float Gravity = 9.81f;
        static readonly Dictionary<TennisActor, (int frame, float time)> sampled = new Dictionary<TennisActor, (int, float)>();
        public static void RecordServeTime(TennisActor actor, float time) => sampled[actor] = (Time.frameCount, time);
        public static float CurrentTime(TennisActor actor) => sampled.TryGetValue(actor, out var p) ? p.time : -1;
        public static bool TryCurrentTime(TennisActor actor, out float time)
        { bool valid = sampled.TryGetValue(actor, out var p) && p.frame == Time.frameCount; time = p.time; return valid; }
        public static bool InHand(TennisActor actor, float t)
        {
            Vector3 hold = Hold(actor);
            Timing(hold.y - PushDepth - actor.transform.position.y, out float fall, out float rebound, out float rise, out float cycle);
            float windStart = TennisRules.ServeTossDelay - WindUp;
            if (t >= windStart) return t < TennisRules.ServeTossDelay;
            float b = t - Mathf.Max(0, windStart - Gather - Bounces * cycle);
            int n = Mathf.FloorToInt(b / cycle);
            if (b < 0 || n >= Bounces) return true;
            float u = b - n * cycle;
            return u < Push || u >= Push + fall + rise;
        }''')
s=s.replace('            Vector3 hold = Hold(a);','            RecordServeTime(a, t);\n            Vector3 hold = Hold(a);',1)
(C/'TennisServeRoutine.cs').write_text(s)
s=(B/'TennisGame.cs').read_text()
# Only the opponent serve approach/reach branch and a shared visual reach adapter.
s=s.replace('                    TennisRules.ServerStanceX(false, Match.DeuceCourt), dt * Profile.Speed);','                    TennisRules.ServerStanceX(false, Match.DeuceCourt), dt * Mathf.Min(Profile.Speed, 1.65f));',1)
s=s.replace('                float tossAge = serveTimer - TennisRules.ServeTossDelay;', '                float tossAge = serveTimer - TennisRules.ServeTossDelay;\n                TennisServeRoutine.RecordServeTime(Opponent, serveTimer);')
s=s.replace('                    TennisServeRoutine.Pose(Opponent, serveTimer, out Vector3 held, out Vector3 palm);','                    TennisServeRoutine.Pose(Opponent, Mathf.Abs(Opponent.Speed) > .2f ? 0 : serveTimer, out Vector3 held, out Vector3 palm);',1)
needle='        void UpdateOpponent(float dt)'
insert=r'''        /// Final visual serve reach, after the match driver's current yaw/root pose.
        /// Changes held/bouncing geometry only; phase clocks and flight/contact stay owned by Step.
        public float ServeReachClock(TennisActor server) => server == Opponent ? serveTimer : TennisServeRoutine.CurrentTime(server);
        public void ResolveServeReachVisual(TennisActor server, Vector3 position)
        {
            bool active = server == Player ? Flow == Phase.PlayerServeHold
                : server == Opponent && Flow == Phase.OpponentServe && serveTimer < TennisRules.ServeTossDelay;
            if (!active) return;
            BallPosition = previousBall = position;
            renderedBall = position;
            if (ball) ball.position = position;
        }

'''
s=s.replace(needle,insert+needle)
(C/'TennisGame.cs').write_text(s)
print('Candidate R2 written; production runtime unchanged')
