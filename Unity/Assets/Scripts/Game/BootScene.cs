using UnityEngine;
using UnityEngine.SceneManagement;

namespace GolfArcade.Game
{
    /// Boot.unity is the build's first scene and holds nothing: in the iPhone app the phone's first message picks the scene (the
    /// Plaza, a match), so a cold start no longer builds the golf course just to throw it away (it held the TV's loading bar at
    /// 12 % for ~9 s, Adnan 10-26). Stand-alone builds have no phone, so they go on to Golf, which used to be the first scene.
    public static class BootScene
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Continue()
        {
            if (NativeSportsSession.Embedded || SceneManager.GetActiveScene().name != "Boot") return;
            SceneManager.LoadScene("Golf");
        }
    }
}
