using UnityEngine;

/// GOLF SWING SPEED film helper (clone only): runs the film's phone-sample feed inside the frame's Update, as
/// NativeSportsSession drains the phone's samples on the device (an Editor update callback runs outside the frame).
[DefaultExecutionOrder(-1000)]
public sealed class GSSPhoneFeed : MonoBehaviour
{
    public static System.Action Hook;
    void Update() => Hook?.Invoke();
}
