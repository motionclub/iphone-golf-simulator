using UnityEngine;

namespace GolfArcade.Tennis
{
    // Wire IDs are shared with TennisUltimate in SportsSession.swift. No paid tiers or perks.
    public enum TennisUltimate { Skybreaker = 0, RescueLob = 1, Curveball = 2 }

    public static class TennisAbilities
    {
        // Retain archived ability data/recording APIs, but no player or AI ultimates in gameplay.
        public static bool UltimatesEnabled => false;
        public static string Name(TennisUltimate ability) => ability switch {
            TennisUltimate.RescueLob => "Rescue Lob", TennisUltimate.Curveball => "Curveball", _ => "Skybreaker"
        };
        public static Vector3 LobVelocity(Vector3 start, Vector3 target, float apex)
        {
            apex = Mathf.Max(apex, start.y + .5f);
            float up = Mathf.Sqrt(2 * 9.81f * (apex - start.y));
            float duration = up / 9.81f + Mathf.Sqrt(2 * (apex - target.y) / 9.81f);
            Vector3 v = (target - start) / duration; v.y = up; return v;
        }
        // Spin is zero here: constant lateral acceleration makes the landing exactly solvable.
        public static Vector3 CurveVelocity(Vector3 start, Vector3 target, float curve)
        {
            float duration = Mathf.Max(1.1f, Mathf.Abs(target.z - start.z) / 17f);
            return (target - start) / duration + new Vector3(-.5f * curve * duration, .5f * 9.81f * duration, 0);
        }
    }

    public sealed partial class TennisGame
    {
        public TennisUltimate SelectedUltimate { get; private set; }
        public string UltimateName => TennisAbilities.Name(SelectedUltimate);
        public bool UltimateArmed { get; private set; }
        public bool LoadoutLocked { get; private set; }
        float ballCurve;
        // STRETCH REACH 2026-11-13 (the dive is gone: its code-bent pose warped the hero at full stretch). A swing at a
        // ball passing just out of reach lunges the player toward it, upright, on the ordinary wide-reach clip.
        /// The player is lunging toward a wide ball (TennisRules.StretchFrom..StretchMax), started by the swing itself.
        public bool StretchActive => stretchLeft > 0;
        /// The current swing stretched: its contact is weak, as the dive's was (TennisRules.StretchQualityCap).
        public bool StretchedSwing { get; private set; }
        float stretchLeft, stretchSpeed, stretchTime;
        bool LiveAbilityInput => !ControllerSetup && Player && Flow == Phase.Rally && resetTimer <= 0 && faultDelay <= 0
            && !CheckingTiming && !IntroPlaying && !ReplayPlaying && !(juice && juice.UltimateActive)
            && (ManualSimulation || Time.timeScale > 0);
        public bool CanArmUltimate => TennisAbilities.UltimatesEnabled && LiveAbilityInput && PlayerUltimate >= 1;
        /// Armed ultimates fire on the player's very next real contact, whatever the stroke (Skybreaker included).
        bool EligibleUltimateContact => !StretchedSwing;

        public bool SelectUltimate(int value)
        {
            if (!TennisAbilities.UltimatesEnabled || LoadoutLocked || value < 0 || value > 2) return false;
            SelectedUltimate = (TennisUltimate)value; UltimateArmed = false; return true;
        }
        public void LockLoadout() => LoadoutLocked = true;
        public bool ToggleUltimate()
        {
            if (!TennisAbilities.UltimatesEnabled || !LiveAbilityInput) return false;
            if (UltimateArmed) { UltimateArmed = false; playerUltCharged = false; return true; }
            if (!CanArmUltimate) return false;
            UltimateArmed = true;
            Feedback = UltimateName + " armed — your next hit fires it";
            return true;
        }
        /// Called as a rally swing starts, with where the ball will pass (`offset`, metres to the player's side, negative =
        /// left) and the seconds until it gets there. Lunges only for a ball between StretchFrom and StretchMax to the side.
        bool BeginStretch(float offset, float toArrive)
        {
            StretchedSwing = false;
            float side = Mathf.Abs(offset);
            if (StretchActive || side <= TennisRules.StretchFrom || side > TennisRules.StretchMax) return false;
            // Already running there fast enough (the auto-run's dash): no lunge, it would only slow the player down.
            if (moveVelocity.x * Mathf.Sign(offset) * toArrive >= side - TennisRules.StretchTo) return false;
            float distance = Mathf.Min(side - TennisRules.StretchTo, TennisRules.StretchDistance);
            stretchTime = Mathf.Clamp(toArrive * .8f, .12f, TennisRules.StretchTime);
            stretchSpeed = Mathf.Sign(offset) * distance / stretchTime;
            stretchLeft = stretchTime; StretchedSwing = true; Stretches++;
            return true;
        }
        /// The lunge itself: sideways at a constant pace (eased off over its last fifth), feet on the court.
        void MoveStretch(float dt)
        {
            float step = Mathf.Min(dt, stretchLeft);
            float ease = Mathf.Clamp01(stretchLeft / (stretchTime * .2f));
            stretchLeft = Mathf.Max(0, stretchLeft - dt);
            Vector3 p = Player.transform.position;
            p.x = Mathf.Clamp(p.x + stretchSpeed * Mathf.Lerp(.5f, 1, ease) * step, -TennisRules.CourtHalfWidth - 2.4f, TennisRules.CourtHalfWidth + 2.4f);
            LateralSpeed = (p.x - Player.transform.position.x) / Mathf.Max(dt, 1e-4f);
            Player.transform.position = p; moveVelocity = new Vector2(LateralSpeed, 0);
        }
        void TickAbilities(float dt)
        {
            if (Flow == Phase.Rally) LoadoutLocked = true;
        }
        void ResetPointAbilities()
        {
            UltimateArmed = false; playerUltCharged = rivalUltCharged = false;
            stretchLeft = 0; StretchedSwing = false; ballCurve = 0; TrackingOverhead = false; overheadAttempted = false; queuedOverheadPower = -1;
        }
        void ResetMatchAbilities()
        {
            ResetPointAbilities(); PlayerUltimate = RivalUltimate = 0;
            LoadoutLocked = false;
        }
        void ApplySelectedUltimate(Vector3 target, float speed)
        {
            switch (SelectedUltimate)
            {
                case TennisUltimate.RescueLob:
                    BallSpin = 0; target.z = 10; target.y = TennisRules.BallRadius;
                    BallVelocity = TennisAbilities.LobVelocity(BallPosition, target, 6f);
                    break;
                case TennisUltimate.Curveball:
                    BallSpin = 0; ballCurve = AimInput < 0 ? -4f : 4f;
                    target.x = Mathf.Clamp(target.x, -3.4f, 3.4f); target.y = TennisRules.BallRadius;
                    BallVelocity = TennisAbilities.CurveVelocity(BallPosition, target, ballCurve);
                    break;
                default:
                    BallVelocity = TennisRules.RallyVelocity(BallPosition, target, Mathf.Min(34, speed * UltimateSpeed), BallSpin, 1);
                    break;
            }
            Feedback = UltimateName.ToUpperInvariant() + "!";
        }
    }
}
