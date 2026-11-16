using System;
using System.Collections.Generic;
using System.Linq;
using GolfArcade.Tennis;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Hub
{
    /// One friend's state in your menu, relayed by the phones (their hubPose -> hubPresence -> your hubRemote) with their lobby look
    /// merged in. The wire format of the walk-around Plaza is kept: the menu reads the identity, the look and the emote, and ignores
    /// where the friend says they are (`place` is always "plaza" from a current build, `bay` empty, x/y/z/yaw/speed their own line-up).
    [Serializable] public sealed class RemoteState
    {
        public string id, name, place, bay, emote, skinHex, shirt, shorts, accent;
        public bool female; public int colour;
        public float x, y, z, yaw, speed;
    }

    /// Friends in your menu's squad: each is the match hero in their own look, stood on the line-up by MenuStage (Override), emotes
    /// mirrored; and the party's chat bubbles over the heroes.
    public sealed class HubRemotes : MonoBehaviour
    {
        /// The one place there is (the `place` field of RemoteState and of hubPose: the wire format keeps it).
        public const string Plaza = "plaza";
        public static readonly Color[] PartyColours = { new Color(.36f, .55f, 1f), new Color(.48f, .85f, .29f), new Color(1f, .39f, .72f), new Color(.66f, .44f, 1f) };

        sealed class Remote
        {
            public string id; public GameObject root; public HubHeroAnimator hero; public MatchHeroLook look;
            /// The newest state they sent (null until the first).
            public RemoteState last; public string lookKey, emote; public bool female;
            public Vector3 shown; public float yaw;
        }
        readonly Dictionary<string, Remote> remotes = new Dictionary<string, Remote>();
        sealed class Speech { public Transform root; public float until; }
        readonly Dictionary<string, Speech> speech = new Dictionary<string, Speech>();
        public bool HasSpeech(string id) => speech.TryGetValue(id ?? "", out var s) && s.until > Time.unscaledTime;

        /// Message text is literal user text: never interpret Unity rich text tags.
        public void Chat(string id, string text)
        {
            id = id ?? "";
            if (string.IsNullOrWhiteSpace(text)) return;
            if (id.Length > 0 && !remotes.ContainsKey(id)) return;
            if (speech.TryGetValue(id, out var previous) && previous.root) Destroy(previous.root.gameObject);
            var root = MenuLight.NameTag(world.transform, text.Length > 280 ? text.Substring(0, 280) : text, new Color(.96f, .98f, 1f));
            root.name = "Party speech " + id;
            var rt = (RectTransform)root; rt.sizeDelta = new Vector2(350, 105);
            var label = root.GetComponentInChildren<Text>(); label.supportRichText = false;
            label.color = new Color(.06f, .12f, .22f); label.fontSize = 23;
            label.resizeTextForBestFit = true; label.resizeTextMinSize = 18; label.resizeTextMaxSize = 23;
            label.horizontalOverflow = HorizontalWrapMode.Wrap; label.verticalOverflow = VerticalWrapMode.Truncate;
            label.rectTransform.offsetMin = new Vector2(12, 8); label.rectTransform.offsetMax = new Vector2(-12, -8);
            HubWorld.SetLayer(root);
            speech[id] = new Speech { root = root, until = Time.unscaledTime + 8f };
            UpdateSpeech();
        }

        void UpdateSpeech()
        {
            foreach (var id in speech.Keys.ToArray()) {
                var s = speech[id];
                if (!s.root || Time.unscaledTime >= s.until || (id.Length > 0 && !remotes.ContainsKey(id))) {
                    if (s.root) Destroy(s.root.gameObject); speech.Remove(id); continue;
                }
                bool local = id.Length == 0;
                var r = local ? null : remotes[id];
                var anchor = local ? world.Player.transform : r.root.transform;
                s.root.position = anchor.position + Vector3.up * (2.75f + (local ? 0 : .45f));
                s.root.rotation = world.Camera.transform.rotation;
                // The menu camera is close: limit the projected width so bubbles never cover the whole picture.
                var camera = world.Camera;
                float distance = Mathf.Max(.1f, Vector3.Dot(s.root.position - camera.transform.position, camera.transform.forward));
                float viewHeight = camera.orthographic ? camera.orthographicSize * 2 : 2 * distance * Mathf.Tan(camera.fieldOfView * .5f * Mathf.Deg2Rad);
                float scale = viewHeight * camera.aspect * (HubWorld.PhoneOnly ? .38f : .22f) / 350f;
                s.root.localScale = Vector3.one * Mathf.Min(.0062f, scale);
                s.root.gameObject.SetActive(local || (r.last != null && r.last.place == Plaza));
                var canvas = s.root.GetComponent<Canvas>(); canvas.targetDisplay = world.Camera.targetDisplay;
            }
        }
        HubWorld world;
        public int Count => remotes.Count;
        /// The menu stands friends on its line-up itself (MenuStage). Asked every frame per friend id: where they stand, which way
        /// they face, and whether they are shown (no answer: hidden).
        public Func<string, (Vector3 pos, float yaw, bool show)?> Override;
        readonly List<string> ids = new List<string>();
        /// A friend's hero animator (null until their hero has spawned): the menu line-up holds a pose on it.
        public HubHeroAnimator HeroOf(string id) => remotes.TryGetValue(id, out var r) ? r.hero : null;
        /// Friends here now, ordered by id (a stable line-up order on every TV).
        public List<string> Ids { get { ids.Clear(); ids.AddRange(remotes.Keys); ids.Sort(System.StringComparer.Ordinal); return ids; } }
        /// A friend's name and party colour (for the menu's name plates).
        public bool TryGetIdentity(string id, out string name, out Color colour)
        {
            name = null; colour = PartyColours[0];
            if (!remotes.TryGetValue(id ?? "", out var r) || r.last == null) return false;
            var s = r.last; name = string.IsNullOrEmpty(s.name) ? "Friend" : s.name;
            colour = PartyColours[Mathf.Abs(s.colour) % PartyColours.Length]; return true;
        }
        /// Diagnostics: where a friend is drawn now.
        public bool TryGetShown(string id, out Vector3 at) { at = default; if (!remotes.TryGetValue(id, out var r)) return false; at = r.shown; return true; }

        public static HubRemotes For(HubWorld w) { var r = w.GetComponent<HubRemotes>(); if (!r) { r = w.gameObject.AddComponent<HubRemotes>(); r.world = w; } return r; }

        public void Receive(RemoteState s)
        {
            if (s == null || string.IsNullOrEmpty(s.id) || float.IsNaN(s.x) || float.IsNaN(s.z)) return;
            if (!remotes.TryGetValue(s.id, out var r)) remotes[s.id] = r = new Remote { id = s.id };
            string key = $"{s.female}|{s.skinHex}|{s.shirt}|{s.shorts}|{s.accent}|{s.name}|{s.colour}";
            if (!r.root || r.female != s.female) Spawn(r, s);
            if (r.lookKey != key) { Dress(r, s); r.lookKey = key; }
            r.last = s;
            if (!string.IsNullOrEmpty(s.emote) && s.emote != r.emote && r.hero) r.hero.Play(s.emote);
            r.emote = s.emote;
        }

        /// The party's member list: anyone not in it is removed.
        public void Roster(IEnumerable<string> ids)
        {
            var keep = new HashSet<string>(ids);
            foreach (var id in remotes.Keys.Where(k => !keep.Contains(k)).ToList()) { if (remotes[id].root) Destroy(remotes[id].root); remotes.Remove(id); }
        }

        void Spawn(Remote r, RemoteState s)
        {
            if (r.root) Destroy(r.root);
            r.female = s.female;
            r.root = new GameObject("Friend " + s.name); r.root.transform.SetParent(world.transform, false);
            var prefab = TennisCustomization.HeroBase(s.female); if (!prefab) return;
            var go = Instantiate(prefab, r.root.transform, false); go.name = "Friend hero";
            r.look = go.GetComponent<MatchHeroLook>();
            if (r.look) HeroAccessories.For(r.look).SetCarry(true);   // ACCESSORIES: friends in the menu carry the golf bag too
            if (r.look && r.look.racketGrip) foreach (var rend in r.look.racketGrip.GetComponentsInChildren<Renderer>(true)) rend.enabled = false;
            r.hero = HubHeroAnimator.Attach(go);
            r.root.transform.position = new Vector3(s.x, s.y, s.z); r.shown = r.root.transform.position;
            HubWorld.SetLayer(r.root.transform);
        }

        /// Their lobby look. (Their name plate is the menu's own: MenuHud, from TryGetIdentity.)
        void Dress(Remote r, RemoteState s)
        {
            if (!r.look) return;
            r.look.SetSkin(!string.IsNullOrEmpty(s.skinHex) ? HeroKit.Hex(s.skinHex) : HeroKit.Hex(HeroKit.SkinHex[2]));
            r.look.SetKit(s.shirt, s.shorts, s.accent);
        }

        void LateUpdate()
        {
            if (!world || !world.Camera) return;
            float dt = Time.unscaledDeltaTime;
            foreach (var r in remotes.Values)
            {
                if (!r.root || r.last == null) continue;
                // on the line-up, idle, facing the camera
                var placed = Override?.Invoke(r.id);
                r.root.SetActive(placed.HasValue && placed.Value.show);
                if (!r.root.activeSelf) continue;
                var o = placed.Value;
                r.shown = o.pos; r.root.transform.position = o.pos;
                r.yaw = Mathf.MoveTowardsAngle(r.yaw, o.yaw, 900 * dt);
                if (r.hero) { r.hero.Seated = false; r.hero.transform.localRotation = Quaternion.Euler(0, r.yaw, 0); r.hero.Tick(0, dt); }
            }
            UpdateSpeech();
        }
    }
}
