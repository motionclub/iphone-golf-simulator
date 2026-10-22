        static float GolfRollPower8(float value)
        {
            float squared = value * value; squared *= squared; return squared * squared;
        }
        // Pose-local Gauss-Newton step, smoothly bounded before solving the arm.
        // No angle search, previous-frame state, or final feasibility rejection.
        static void ApplyGolfWristRoll(MatchHeroLook hero, GolfGripData data, bool left, Vector3 axis, float scale)
        {
            if (System.Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_ROLL") != "1") return;
            var upper = hero.Bone(left ? HumanBodyBones.LeftUpperArm : HumanBodyBones.RightUpperArm);
            var lower = hero.Bone(left ? HumanBodyBones.LeftLowerArm : HumanBodyBones.RightLowerArm);
            var hand = hero.Bone(left ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand);
            var middle = Bone(hero, left, "Middle", "Proximal");
            if (!upper || !lower || !hand || !middle || scale < .0001f) return;
            var shoulder = upper.position; var handRotation = hand.rotation;
            var clubPosition = data.grip.position; var clubRotation = data.grip.rotation;
            // Model metres keep the bound independent of the locker/game scale.
            var e = (lower.position - shoulder) / scale;
            var h = (hand.position - shoulder) / scale;
            var c = (clubPosition - shoulder) / scale;
            var palm = (middle.position - hand.position).normalized;
            axis.Normalize();
            float a = e.magnitude, b = (h - e).magnitude, d = h.magnitude;
            if (a <= 0 || b <= 0 || d <= 0) return;
            var forward = h / d; float along = Vector3.Dot(e, forward);
            var pole = e - forward * along; float radius = pole.magnitude;
            float margin = Mathf.Min(a + b - d, d - Mathf.Abs(a - b));
            // At a degenerate arm the continuous safe roll tends to zero.
            if (margin <= 0 || radius <= 0) return;
            var normal = pole / radius; var forearm = (h - e) / b;
            float originalAngle = Vector3.Angle(forearm, palm);
            float activation = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(35, 50, originalAngle));
            var handDerivative = Vector3.Cross(axis, h - c);
            float distanceDerivative = Vector3.Dot(forward, handDerivative);
            var forwardDerivative = (handDerivative - forward * distanceDerivative) / d;
            float alongDerivative = .5f * (1 - (a * a - b * b) / (d * d)) * distanceDerivative;
            float radiusDerivative = -along * alongDerivative / Mathf.Max(radius, 1e-12f);
            var elbowDerivative = forward * alongDerivative + forwardDerivative * along + normal * radiusDerivative
                - forward * (radius * Vector3.Dot(normal, forwardDerivative));
            var forearmDerivative = (handDerivative - elbowDerivative) / b;
            var palmDerivative = Vector3.Cross(axis, palm);
            float gradient = Vector3.Dot(forearmDerivative, palm) + Vector3.Dot(forearm, palmDerivative);
            float rawRoll = gradient / ((forearmDerivative - palmDerivative).sqrMagnitude + .12f + 15.23f * elbowDerivative.sqrMagnitude);

            // Every wrist on this orbit stays within q0 of its source. Over that
            // ball, sensitivity bounds elbow displacement / wrist displacement.
            // See continuous-review/CONTINUITY.md for the geometric derivation.
            float q0 = .5f * margin, dMin = d - q0, dMax = d + q0;
            float lMin = (a * a - b * b + dMin * dMin) / (2 * dMin);
            float lMax = (a * a - b * b + dMax * dMax) / (2 * dMax);
            float rMin = Mathf.Sqrt(Mathf.Max(1e-24f, Mathf.Min(a * a - lMin * lMin, a * a - lMax * lMax)));
            float lPrime = Mathf.Max(Mathf.Abs(.5f * (1 - (a * a - b * b) / (dMin * dMin))),
                Mathf.Abs(.5f * (1 - (a * a - b * b) / (dMax * dMax))));
            float sensitivity = a * (1 / Mathf.Sqrt(d * d - q0 * q0) + lPrime / rMin);
            float radial = Vector3.Cross(axis, h - c).magnitude;
            const float limit = .04f;
            float rate0 = 4 / Mathf.PI, rate1 = radial / limit, rate2 = radial / q0, rate3 = radial * sensitivity / limit;
            float rate = Mathf.Max(Mathf.Max(rate0, rate1), Mathf.Max(rate2, rate3));
            float rollCap = 1 / (rate * Mathf.Pow(GolfRollPower8(rate0 / rate) + GolfRollPower8(rate1 / rate)
                + GolfRollPower8(rate2 / rate) + GolfRollPower8(rate3 / rate), .125f));
            float roll = rollCap * (float)System.Math.Tanh(rawRoll / rollCap) * activation;
            var turn = Quaternion.AngleAxis(roll * Mathf.Rad2Deg, axis);
            var targetHand = c + turn * (h - c);
            float targetDistance = targetHand.magnitude;
            var targetForward = targetHand / targetDistance;
            float targetAlong = (a * a - b * b + targetDistance * targetDistance) / (2 * targetDistance);
            // Transport the source elbow plane: projecting the old elbow into
            // each trial plane created a second discontinuity near straight arms.
            var cross = Vector3.Cross(forward, targetForward);
            var targetNormal = normal + Vector3.Cross(cross, normal)
                + Vector3.Cross(cross, Vector3.Cross(cross, normal)) / (1 + Vector3.Dot(forward, targetForward));
            var targetElbow = targetForward * targetAlong
                + targetNormal * Mathf.Sqrt(Mathf.Max(0, a * a - targetAlong * targetAlong));
            var bestElbow = shoulder + targetElbow * scale;
            var bestWrist = shoulder + targetHand * scale;
            if (System.Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_AUDIT") == "1")
                Debug.Log($"[GolfWristRoll] {(hero.female ? "Female" : "Male")} {(left ? "Left" : "Right")} angle={originalAngle:F3} roll={roll * Mathf.Rad2Deg:F3} scale={scale:F6} wristDelta={(targetHand-h).magnitude * scale:F6} elbowDelta={(targetElbow-e).magnitude * scale:F6} axis={axis:F6}");
            upper.rotation = Quaternion.FromToRotation(lower.position - shoulder, bestElbow - shoulder) * upper.rotation;
            lower.rotation = Quaternion.FromToRotation(hand.position - lower.position, bestWrist - lower.position) * lower.rotation;
            hand.SetPositionAndRotation(bestWrist, turn * handRotation);
            // The sampled digit local transforms are untouched. Preserve the
            // club explicitly, including rigs that parent it beneath a hand.
            data.grip.SetPositionAndRotation(clubPosition, clubRotation);
        }
