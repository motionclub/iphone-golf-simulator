namespace GolfArcade.Game
{
    /// The Daily Hole in One (GolfGame.HoleInOne.cs): the phone starts it with `holeInOne` set to the day (yyyymmdd, UTC), hears
    /// the three shots as a "holeInOne" event, and sends the world's standing back as `holeInOneBoard` (its JSON in `mode`).
    public sealed partial class NativeSportsSession
    {
        public partial class Message { public int holeInOne; }

        bool HoleInOneReceive(Message m)
        {
            if (m.action != "holeInOneBoard") return false;
            if (golf) golf.SetHoleInOneBoard(m.mode);
            return true;
        }
    }
}
