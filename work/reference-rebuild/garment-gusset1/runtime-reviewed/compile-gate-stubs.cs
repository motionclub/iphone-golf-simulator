using UnityEngine;
namespace GolfArcade.Tennis {
 public sealed class MatchHeroLook : MonoBehaviour { public bool golfKit, female; public SkinnedMeshRenderer body; public SkinnedMeshRenderer[] kit; }
 public static class HeroGarmentHemWeights { public static Mesh Prepare(MatchHeroLook look,SkinnedMeshRenderer renderer,Mesh source,Transform[] bones) => source; }
 public sealed class HeroGarmentPoseCorrectives : MonoBehaviour { public void Apply() {} }
 public sealed class TennisGame : MonoBehaviour { public bool Initialized, ManualSimulation; public Camera GameplayCamera; }
 public sealed class TennisActor : MonoBehaviour { public void Build(bool female, Color color, bool left) {} }
 public sealed class HeroTennisDriver : MonoBehaviour { public enum Clip { Forehand, EmoteSpike } public MatchHeroLook matchLook; public float ContactOf(Clip c) => 0; public float LengthOf(Clip c) => 1; public void Sample(Clip c, float t) {} }
 public static class TennisHeroSetup { public static HeroTennisDriver Attach(TennisGame game, TennisActor actor, bool player) => null; }
}
