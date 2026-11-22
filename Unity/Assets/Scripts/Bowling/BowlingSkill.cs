namespace GolfArcade.Bowling
{
    /// The 11-21 skill pass (Adnan: "ball speed, spin, pretty much no mechanics really matter"). The lane and pin physics already
    /// answered to speed and spin; the swing reading flattened them first. With the pass on:
    ///   * speed: the swing → mph curve spans ~14 (lazy) to ~22.5 mph (hard) instead of 16.5-21, and an easy swing floors at
    ///     11 mph, not 15.4 (BowlingSwingDetector.BallSpeed, BowlingGame.SelfTimedMin). About ±1.5 boards at the pins per mph;
    ///   * spin: the wrist's dead zone is 4°, not 8°, revs reach 500 rpm, and the side roll eases into a 34 rad/s ceiling instead of
    ///     stopping hard at 22.5, so a bigger flick keeps hooking more (entry ~6-6.5° at the top, was stuck at ~5°)
    ///     (BowlingSwingDetector.Spin, BowlingRelease.SideRoll);
    ///   * release timing: Perfect / Good / Early / Late are further apart (BowlingRelease.For);
    ///   * lane: the house pattern's dry outside boards ("the wall") pull a wide ball back to the pocket far less (OilPattern.House).
    /// Both phones of a networked game must agree (the throw is replayed from its inputs), so these are build-wide defaults:
    /// flip them here, not per player. `On = false` is the 10-27 feel pass exactly; `EasyLanes` keeps the new swing reading on
    /// the old forgiving lane (kids / party play).
    public static class BowlingSkill
    {
        public static bool On = true;
        public static bool EasyLanes = false;
    }
}
