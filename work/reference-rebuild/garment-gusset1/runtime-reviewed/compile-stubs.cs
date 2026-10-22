using UnityEngine;
namespace GolfArcade.Tennis {
 public sealed class MatchHeroLook : MonoBehaviour { public bool golfKit, female; public SkinnedMeshRenderer body; public SkinnedMeshRenderer[] kit; }
 public static class HeroGarmentHemWeights { public static Mesh Prepare(MatchHeroLook look,SkinnedMeshRenderer renderer,Mesh source,Transform[] bones) => source; }
}
