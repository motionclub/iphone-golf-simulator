using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// The three accessory slots. Each holds at most one item; slots never touch each other or the body, head, clothes, rig or clips.
    public enum AccessorySlot { Headwear, Glove, BackCarry }

    /// ACCESSORIES (work/accessories): basic hero accessories as separate swappable items. An item is its own skinned piece (renderer `Acc_*`), bound BY NAME to
    /// the hero's own bones or to a socket this component creates under a bone (`Headwear` under Head, `Back_Bag` under UpperChest; `HairRoot` is reserved
    /// empty under Head for the hair that comes later), drawn with the kit V2 cloth look (TennisCloth + the piece's own N / M maps). Nothing in a prefab changes: the
    /// component is added by MatchHeroLook.OwnMaterials (the one place the game and every tool build a hero's look) and loads the per-sex mesh and data from
    /// Resources/Accessories/<Sex>/<item>/ (installed by Editor/AccessoriesInstall.cs from work/accessories/out).
    ///
    /// Slots and items:  Headwear = tennis_cap | golf_cap,  Glove = golf_glove (left hand; the mirrored right one for left-handed golfers),  BackCarry = golf_bag | racket_back.
    /// Defaults (by kit): tennis kit -> tennis_cap; golf kit -> golf_cap + golf_glove. The bag is carried only where the game asks: SetCarry(true) in the plaza and
    /// between golf shots. ACC_DEFAULTS=0 (environment) turns the default items off for A/B captures; ACC_ITEMS=a,b,... replaces the default list.
    [DefaultExecutionOrder(100)]
    public sealed class HeroAccessories : MonoBehaviour
    {
        public const string SocketHeadwear = "Headwear", SocketHair = "HairRoot", SocketBack = "Back_Bag", SocketBackRacket = "Back_Racket";
        public const string BackRacketRenderer = "Acc_Racket_Back";

        public sealed class ItemDef
        {
            public readonly string id, name; public readonly AccessorySlot slot; public readonly string baseHex, trimHex;
            public ItemDef(string id, AccessorySlot slot, string name, string baseHex, string trimHex) { this.id = id; this.slot = slot; this.name = name; this.baseHex = baseHex; this.trimHex = trimHex; }
        }
        public static readonly ItemDef[] Catalog =
        {
            new ItemDef("tennis_cap", AccessorySlot.Headwear, "Tennis cap", "F3F2EE", "1F2B57"),
            new ItemDef("golf_cap", AccessorySlot.Headwear, "Golf cap", "1F2B57", "F3F2EE"),
            new ItemDef("golf_glove", AccessorySlot.Glove, "Golf glove", "F1F0EC", "1F2B57"),
            new ItemDef("golf_bag", AccessorySlot.BackCarry, "Golf carry bag", "F1F0EC", "1F2B57"),
            // MENU HERO (work/menu-hero): the hero's own classic racket slung across the back (built from the racket in the hand, no item data)
            new ItemDef("racket_back", AccessorySlot.BackCarry, "Racket on back", "FFFFFF", "FFFFFF"),
        };
        /// The back items the locker switches between (the player's pick is saved on the phone and sent with the plaza look).
        public static readonly string[] BackCarryItems = { "golf_bag", "racket_back" };
        public static ItemDef Def(string id) => Catalog.FirstOrDefault(d => d.id == id);

        [Serializable] sealed class PieceData { public string name, renderer, mesh, maps; public float metresPerUv; public string[] bones, roles; }
        [Serializable] sealed class ItemData { public string item, sex, slot, parentBone, socket; public float[] socketPosition, socketRotation; public PieceData[] pieces; }

        sealed class Equipped
        {
            public ItemDef def; public ItemData data; public List<SkinnedMeshRenderer> renderers = new List<SkinnedMeshRenderer>();
            public bool visible = true; public Color? baseColour, trimColour; public List<(Material m, bool metal)> materials = new List<(Material, bool)>();
            /// racket_back: the cloned racket (plain mesh renderers under the Back_Racket socket, the racket's own materials).
            public GameObject rigidRoot; public List<Renderer> rigid = new List<Renderer>();
        }

        public MatchHeroLook look;
        readonly Dictionary<AccessorySlot, Equipped> worn = new Dictionary<AccessorySlot, Equipped>();
        Dictionary<string, Transform> byName;
        bool leftHandedGolfer, carry;
        /// What SetCarry(true) puts on the back: golf_bag (default) or racket_back.
        public string CarryItem { get; private set; } = "golf_bag";

        /// The component of a hero (added when missing).
        public static HeroAccessories For(MatchHeroLook look)
        {
            if (!look) return null;
            var a = look.GetComponent<HeroAccessories>();
            if (!a) a = look.gameObject.AddComponent<HeroAccessories>();
            a.look = look;
            return a;
        }

        /// Called by MatchHeroLook.OwnMaterials: the hero's default accessories for its kit.
        public static void Setup(MatchHeroLook look)
        {
            if (!look || !look.body) return;
            var a = For(look);
            if (Environment.GetEnvironmentVariable("ACC_DEFAULTS") == "0") return;
            string list = Environment.GetEnvironmentVariable("ACC_ITEMS");
            var items = !string.IsNullOrEmpty(list) ? list.Split(',').Select(s => s.Trim()).Where(s => s.Length > 0).ToArray()
                : look.golfKit ? new[] { "golf_cap", "golf_glove" } : new[] { "tennis_cap" };
            foreach (var id in items) a.Equip(id);
        }

        // ---------------------------------------------------------------- queries
        public string Item(AccessorySlot slot) => worn.TryGetValue(slot, out var e) ? e.def.id : null;
        public bool IsVisible(AccessorySlot slot) => worn.TryGetValue(slot, out var e) && e.visible;
        public bool Carrying => carry;
        public IEnumerable<SkinnedMeshRenderer> Renderers(AccessorySlot slot) => worn.TryGetValue(slot, out var e) ? e.renderers.Where(r => r) : Enumerable.Empty<SkinnedMeshRenderer>();
        public IEnumerable<SkinnedMeshRenderer> AllRenderers() => worn.Values.SelectMany(e => e.renderers).Where(r => r);

        // ---------------------------------------------------------------- slot operations
        public bool Equip(string itemId) { var d = Def(itemId); return d != null && Equip(d.slot, itemId); }

        /// Puts `itemId` in `slot` (replacing what is there). False when the item has no data for this hero's body.
        public bool Equip(AccessorySlot slot, string itemId)
        {
            var def = Def(itemId);
            if (def == null || def.slot != slot || !look || !look.body) return false;
            if (worn.TryGetValue(slot, out var cur) && cur.def.id == itemId && cur.renderers.Count > 0 && cur.renderers.All(r => r)) return true;
            if (worn.TryGetValue(slot, out cur) && cur.def.id == itemId && cur.rigidRoot) return true;
            Unequip(slot);
            if (itemId == "racket_back")
            {
                var racket = BuildBackRacket(def); if (racket == null) return false;
                worn[slot] = racket; Apply(racket); return true;
            }
            string sex = look.female ? "Female" : "Male";
            var json = Resources.Load<TextAsset>($"Accessories/{sex}/{itemId}/item");
            if (!json) return false;
            var data = JsonUtility.FromJson<ItemData>(json.text);
            var e = new Equipped { def = def, data = data };
            if (!string.IsNullOrEmpty(data.socket)) PlaceSocket(data);
            foreach (var p in data.pieces)
            {
                var r = BuildPiece(e, p, sex);
                if (r) e.renderers.Add(r);
            }
            if (e.renderers.Count != data.pieces.Length) { foreach (var r in e.renderers) if (r) Kill(r.gameObject); return false; }
            worn[slot] = e;
            if (slot == AccessorySlot.Glove) RefreshGlove();
            Apply(e);
            return true;
        }

        public void Unequip(AccessorySlot slot)
        {
            if (!worn.TryGetValue(slot, out var e)) return;
            foreach (var r in e.renderers) if (r) { r.enabled = false; Kill(r.gameObject); }
            if (e.rigidRoot) { foreach (var r in e.rigid) if (r) r.enabled = false; Kill(e.rigidRoot); }
            foreach (var (m, _) in e.materials) Kill(m);
            worn.Remove(slot);
            if (slot == AccessorySlot.Glove) RefreshGlove();
            ApplyCover();
        }

        public void SetVisible(AccessorySlot slot, bool on)
        {
            if (!worn.TryGetValue(slot, out var e)) return;
            e.visible = on; Apply(e);
        }

        /// Base and trim colour of the item in `slot` (sRGB picks, like the kit colours; null keeps the item's own).
        public void SetColours(AccessorySlot slot, Color? baseColour, Color? trimColour)
        {
            if (!worn.TryGetValue(slot, out var e)) return;
            e.baseColour = baseColour; e.trimColour = trimColour; Apply(e);
        }

        /// The back item on the back: true in the plaza and between golf shots, false while swinging / in matches. `item` (golf_bag | racket_back,
        /// null = keep the current pick) is the player's locker choice; golf always carries the bag (GolferView passes none and the pick stays the bag there).
        public void SetCarry(bool carried, string item = null)
        {
            if (item != null && Array.IndexOf(BackCarryItems, item) >= 0) CarryItem = item;
            carry = carried;
            if (carried && Item(AccessorySlot.BackCarry) != CarryItem && !Equip(AccessorySlot.BackCarry, CarryItem)) Equip(AccessorySlot.BackCarry, "golf_bag");
            SetVisible(AccessorySlot.BackCarry, carried);
        }

        // ---------------------------------------------------------------- the racket on the back
        /// Where the racket sits, in the Back_Bag socket's frame of the golf bag data (the socket is authored on the hero's back surface, axes along the
        /// hero: +x the hero's right, +y up, +z forward): the string bed's centre a little above the bag socket and behind it, the face flat on the back,
        /// the handle up over the right shoulder, `BackRacketTilt` degrees off vertical.
        public static readonly Vector3 BackRacketCentre = new Vector3(0f, .03f, -.035f);
        public const float BackRacketTilt = 30f;
        /// The racket on the back is drawn at its own (prefab) size: the court's TennisRules.HeroRacketScale is for the string bed in play only.
        public const float BackRacketScale = 1f;

        /// The Racket_Classic (racketGrip) placement on the back relative to `parent` (UpperChest), for this hero. False when the hero has no racket or
        /// no bag socket data. MatchHeroLockerExport uses the same numbers for the phone menu's racket-on-back.
        public static bool BackRacketPose(MatchHeroLook look, out Transform parent, out Vector3 position, out Quaternion rotation, out float scale)
        {
            parent = null; position = Vector3.zero; rotation = Quaternion.identity; scale = 1;
            if (!look || !look.racketGrip) return false;
            string sex = look.female ? "Female" : "Male";
            var json = Resources.Load<TextAsset>($"Accessories/{sex}/golf_bag/item");
            if (!json) return false;
            var d = JsonUtility.FromJson<ItemData>(json.text);
            parent = look.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == d.parentBone);
            if (!parent) return false;
            var socketPos = new Vector3(d.socketPosition[0], d.socketPosition[1], d.socketPosition[2]);
            var socketRot = new Quaternion(d.socketRotation[0], d.socketRotation[1], d.socketRotation[2], d.socketRotation[3]);
            // racket axes (racketGrip-local): stringUpLocal = grip -> head, stringNormalLocal = the face normal, stringCentreLocal = the string bed's centre
            float a = BackRacketTilt * Mathf.Deg2Rad;
            var headDir = new Vector3(-Mathf.Sin(a), -Mathf.Cos(a), 0);   // head down and to the hero's left, so the handle rises over the right shoulder
            var inSocket = Quaternion.LookRotation(Vector3.back, headDir) * Quaternion.Inverse(Quaternion.LookRotation(look.stringNormalLocal, look.stringUpLocal));
            // parent-local metres: the socket data are in UpperChest units; the racket's own size follows the hero root
            float unit = Mathf.Abs(parent.lossyScale.x) > 1e-6f ? Mathf.Abs(look.transform.lossyScale.x) / Mathf.Abs(parent.lossyScale.x) : 1;
            scale = BackRacketScale * unit;
            rotation = socketRot * inSocket;
            position = socketPos + socketRot * BackRacketCentre * unit - rotation * (look.stringCentreLocal * scale);
            return true;
        }

        Equipped BuildBackRacket(ItemDef def)
        {
            if (!BackRacketPose(look, out var parent, out var pos, out var rot, out float scale)) return null;
            var s = Bone(SocketBackRacket);
            if (!s || s.parent != parent) { var go = new GameObject(SocketBackRacket); s = go.transform; s.SetParent(parent, false); byName[SocketBackRacket] = s; }
            s.localPosition = pos; s.localRotation = rot; s.localScale = Vector3.one * scale;
            var e = new Equipped { def = def };
            var root = new GameObject(BackRacketRenderer); root.layer = look.racketGrip.gameObject.layer;
            root.transform.SetParent(s, false);
            // the racket's visible meshes (frame, strings, grip, butt cap) at their place inside Racket_Classic, sharing its materials (the racket colour pick follows)
            var src = look.racketGrip;
            foreach (var mr in src.GetComponentsInChildren<MeshRenderer>(true))
            {
                var mf = mr.GetComponent<MeshFilter>(); if (!mf || !mf.sharedMesh || mr.name.StartsWith("Collider")) continue;
                var piece = new GameObject(mr.name); piece.layer = mr.gameObject.layer;
                piece.transform.SetParent(root.transform, false);
                var m = src.worldToLocalMatrix * mr.transform.localToWorldMatrix;
                piece.transform.localPosition = m.GetColumn(3); piece.transform.localRotation = m.rotation; piece.transform.localScale = m.lossyScale;
                piece.AddComponent<MeshFilter>().sharedMesh = mf.sharedMesh;
                var r = piece.AddComponent<MeshRenderer>(); r.sharedMaterials = mr.sharedMaterials;
                r.shadowCastingMode = mr.shadowCastingMode; r.receiveShadows = mr.receiveShadows; r.renderingLayerMask = mr.renderingLayerMask;
                e.rigid.Add(r);
            }
            if (e.rigid.Count == 0) { Kill(root); return null; }
            e.rigidRoot = root;
            return e;
        }

        /// Golfers: the glove goes on the lead hand (left hand for a right-hander, so the mirrored piece for a left-hander).
        public void SetGolfHand(bool leftHanded)
        {
            leftHandedGolfer = leftHanded;
            if (worn.TryGetValue(AccessorySlot.Glove, out var e)) Apply(e);
            RefreshGlove();
        }

        /// The old kit gloves (Kit_Glove_L/R) stay off while an accessory glove is worn.
        public void RefreshGlove()
        {
            if (!look || look.kit == null) return;
            bool mine = worn.ContainsKey(AccessorySlot.Glove);
            foreach (var r in look.kit)
                if (r && (r.name == "Kit_Glove_L" || r.name == "Kit_Glove_R"))
                    r.enabled = !mine && r.name == (leftHandedGolfer ? "Kit_Glove_R" : "Kit_Glove_L");
        }

        // ---------------------------------------------------------------- building
        Transform Bone(string name)
        {
            if (byName == null || !byName.TryGetValue(name, out var t) || !t)
            {
                byName = new Dictionary<string, Transform>();
                foreach (var tr in look.GetComponentsInChildren<Transform>(true)) if (!byName.ContainsKey(tr.name)) byName[tr.name] = tr;
                byName.TryGetValue(name, out t);
            }
            return t;
        }

        void PlaceSocket(ItemData d)
        {
            var parent = Bone(d.parentBone);
            if (!parent) throw new InvalidOperationException($"accessory {d.item}: parent bone {d.parentBone} missing on {look.name}");
            var s = Bone(d.socket);
            if (!s || s.parent != parent)
            {
                var go = new GameObject(d.socket); s = go.transform; s.SetParent(parent, false);
                byName[d.socket] = s;
            }
            s.localPosition = new Vector3(d.socketPosition[0], d.socketPosition[1], d.socketPosition[2]);
            s.localRotation = new Quaternion(d.socketRotation[0], d.socketRotation[1], d.socketRotation[2], d.socketRotation[3]);
            s.localScale = Vector3.one;
            // the empty hair socket: hair that comes later is parented here and the cap squashes / hides it, never the other way round
            if (d.parentBone == "Head" && !Bone(SocketHair)) { var h = new GameObject(SocketHair); h.transform.SetParent(parent, false); byName[SocketHair] = h.transform; }
        }

        SkinnedMeshRenderer BuildPiece(Equipped e, PieceData p, string sex)
        {
            var mesh = Resources.Load<Mesh>($"Accessories/{sex}/{e.def.id}/{p.mesh}");
            if (!mesh) { Debug.LogWarning($"[Accessories] mesh Accessories/{sex}/{e.def.id}/{p.mesh} missing"); return null; }
            var body = look.body;
            var go = new GameObject(p.renderer);
            go.transform.SetParent(body.transform.parent, false);
            go.transform.localPosition = body.transform.localPosition; go.transform.localRotation = body.transform.localRotation; go.transform.localScale = body.transform.localScale;
            go.layer = body.gameObject.layer;
            var smr = go.AddComponent<SkinnedMeshRenderer>();
            smr.sharedMesh = mesh;
            var bones = new Transform[p.bones.Length];
            for (int i = 0; i < bones.Length; i++)
            {
                bones[i] = Bone(p.bones[i]);
                if (!bones[i]) { Debug.LogWarning($"[Accessories] {e.def.id}: bone {p.bones[i]} missing on {look.name}"); Kill(go); return null; }
            }
            smr.bones = bones; smr.rootBone = body.rootBone;
            smr.localBounds = body.localBounds; smr.updateWhenOffscreen = body.updateWhenOffscreen; smr.quality = SkinQuality.Bone4;
            smr.shadowCastingMode = body.shadowCastingMode; smr.receiveShadows = body.receiveShadows;
            smr.lightProbeUsage = body.lightProbeUsage; smr.reflectionProbeUsage = body.reflectionProbeUsage;
            smr.motionVectorGenerationMode = body.motionVectorGenerationMode; smr.skinnedMotionVectors = body.skinnedMotionVectors; smr.allowOcclusionWhenDynamic = body.allowOcclusionWhenDynamic;
            smr.renderingLayerMask = body.renderingLayerMask | HeroRimLight.Layer;
            var mats = new Material[p.roles.Length];
            string maps = $"Accessories/{sex}/{e.def.id}/Acc_{sex}_{e.def.id}_{p.maps}";
            for (int i = 0; i < mats.Length; i++)
            {
                bool metal = p.roles[i].EndsWith("Metal");
                mats[i] = metal ? look.AccessoryMetal(p.roles[i] + " (hero)", Color.white) : look.AccessoryCloth(p.roles[i] + " (hero)", maps, p.metresPerUv, Color.white, Color.white);
                e.materials.Add((mats[i], metal));
            }
            smr.sharedMaterials = mats;
            // The female body preserves wrist volume with a dual-quaternion
            // palette. Its glove needs the same interpolation at that seam.
            if(look.female && look.golfKit && e.def.slot==AccessorySlot.Glove)HeroArmSkinning.Build(smr);
            return smr;
        }

        void Apply(Equipped e)
        {
            Color b = e.baseColour ?? HeroKit.Hex(e.def.baseHex), t = e.trimColour ?? HeroKit.Hex(e.def.trimHex);
            foreach (var (m, metal) in e.materials)
            {
                if (!m) continue;
                if (metal) { if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", new Color(.78f, .79f, .81f, 1)); continue; }
                m.SetColor("_BaseColor", MatchHeroLook.KitTint(b)); m.SetColor("_TrimColor", MatchHeroLook.KitTint(t));
            }
            foreach (var r in e.rigid) if (r) r.enabled = e.visible;
            // hidden pieces are disabled, not deactivated: the lobby export keeps its part list stable and only draws enabled renderers
            foreach (var r in e.renderers)
            {
                if (!r) continue;
                bool on = e.visible;
                if (e.def.slot == AccessorySlot.Glove) on &= r.name.EndsWith("R") == leftHandedGolfer;
                r.enabled = on;
            }
            ApplyCover();
        }

        // ---------------------------------------------------------------- skin cover
        /// Skin an accessory covers (the golf glove: the whole hand, work/accessories/py/glove_cover.py) is not drawn, so it can never show through the wall in a swing.
        /// Same idea as the clothing V2 cover: the body ASSET is untouched; a derived copy of the mesh the body shows right now drops the listed triangles
        /// (int32 body-vertex triplets in Resources/Accessories/<Sex>/<item>/Acc_<Sex>_<item>_<Tag>_hide.bytes). Re-applied by MatchHeroLook after its own cover.
        Mesh coverSource;
        static readonly Dictionary<(Mesh, string), Mesh> covered = new Dictionary<(Mesh, string), Mesh>();
        static readonly HashSet<Mesh> coverVariants = new HashSet<Mesh>();
        static long CoverKey(int a, int b, int c)
        {
            if (a > b) (a, b) = (b, a); if (b > c) (b, c) = (c, b); if (a > b) (a, b) = (b, a);
            return ((long)a << 42) | ((long)b << 21) | (long)c;
        }

        public void ReapplyCover() => ApplyCover();

        void ApplyCover()
        {
            if (!look || !look.body) return;
            var cur = look.body.sharedMesh; if (!cur) return;
            var src = coverVariants.Contains(cur) && coverSource ? coverSource : cur;
            if (!src.isReadable) return;
            string sex = look.female ? "Female" : "Male";
            var lists = new List<(string key, TextAsset data)>();
            foreach (var e in worn.Values)
                foreach (var r in e.renderers)
                {
                    if (!r || !r.enabled || e.data == null) continue;
                    var p = e.data.pieces.FirstOrDefault(q => q.renderer == r.name);
                    if (p == null) continue;
                    var ta = Resources.Load<TextAsset>($"Accessories/{sex}/{e.def.id}/Acc_{sex}_{e.def.id}_{p.maps}_hide");
                    if (ta) lists.Add(($"{e.def.id}:{p.maps}", ta));
                }
            if (lists.Count == 0)
            {
                if (coverVariants.Contains(cur) && coverSource) look.body.sharedMesh = coverSource;
                return;
            }
            coverSource = src;
            string key = string.Join("|", lists.Select(l => l.key).OrderBy(k => k, StringComparer.Ordinal));
            if (!covered.TryGetValue((src, key), out var mesh) || !mesh)
            {
                var hide = new HashSet<long>();
                foreach (var (_, ta) in lists)
                {
                    var b = ta.bytes;
                    for (int i = 0; i + 12 <= b.Length; i += 12) hide.Add(CoverKey(BitConverter.ToInt32(b, i), BitConverter.ToInt32(b, i + 4), BitConverter.ToInt32(b, i + 8)));
                }
                // 10-19: the stored lists are body-vertex index triplets from the day the glove was built; where the runtime body has split or moved
                // vertices since, slivers of knuckle skin stayed drawn and poked through the glove wall (female golf, orange shards on the knuckles).
                // Any triangle touching the gloved hand, its fingers or the hand half of the wrist blend is under the glove, so those are hidden too.
                // Female only: the male's glove stays exactly as it was accepted.
                if (look.female)
                    foreach (var (lk, _) in lists)
                        if (lk.StartsWith("golf_glove")) HideGlovedHand(src, lk.EndsWith(":GloveR") ? "Right" : "Left", hide);
                mesh = UnityEngine.Object.Instantiate(src); mesh.name = src.name + " (accessory cover)"; mesh.hideFlags = HideFlags.DontSave;
                for (int sub = 0; sub < src.subMeshCount; sub++)
                {
                    var t = src.GetTriangles(sub); var keep = new List<int>(t.Length);
                    for (int i = 0; i < t.Length; i += 3)
                        if (!hide.Contains(CoverKey(t[i], t[i + 1], t[i + 2]))) { keep.Add(t[i]); keep.Add(t[i + 1]); keep.Add(t[i + 2]); }
                    mesh.SetTriangles(keep, sub, false);
                }
                covered[(src, key)] = mesh; coverVariants.Add(mesh);
            }
            look.body.sharedMesh = mesh;
        }

        void HideGlovedHand(Mesh src, string side, HashSet<long> hide)
        {
            var palette = look.body.bones; var w = src.boneWeights; if (w.Length != src.vertexCount || palette == null) return;
            var hand = new bool[palette.Length];
            for (int i = 0; i < palette.Length; i++)
            {
                var n = palette[i] ? palette[i].name : "";
                // the wrist joint's blend palette (HeroArmSkinning: ArmBlend_<forearm>_<hand>_<step 1..7>): the steps nearer the hand are glove territory
                if (n.StartsWith("ArmBlend_"))
                {
                    var parts = n.Split('_');
                    if (parts.Length >= 4 && int.TryParse(parts[1], out int pa) && int.TryParse(parts[2], out int pb) && int.TryParse(parts[3], out int step)
                        && pa >= 0 && pb >= 0 && pa < palette.Length && pb < palette.Length && palette[pa] && palette[pb]
                        && palette[pa].name == side + "LowerArm" && palette[pb].name == side + "Hand" && step >= 4) hand[i] = true;
                    continue;
                }
                if (!n.StartsWith(side)) continue;
                hand[i] = n == side + "Hand" || n.Contains("Thumb") || n.Contains("Index") || n.Contains("Middle") || n.Contains("Ring") || n.Contains("Little");
            }
            var inside = new bool[w.Length]; int count = 0;
            for (int v = 0; v < w.Length; v++)
            {
                float sum = 0; var b = w[v];
                if (b.boneIndex0 >= 0 && b.boneIndex0 < hand.Length && hand[b.boneIndex0]) sum += b.weight0;
                if (b.boneIndex1 >= 0 && b.boneIndex1 < hand.Length && hand[b.boneIndex1]) sum += b.weight1;
                if (b.boneIndex2 >= 0 && b.boneIndex2 < hand.Length && hand[b.boneIndex2]) sum += b.weight2;
                if (b.boneIndex3 >= 0 && b.boneIndex3 < hand.Length && hand[b.boneIndex3]) sum += b.weight3;
                inside[v] = sum >= .55f;
            }
            for (int sub = 0; sub < src.subMeshCount; sub++)
            {
                var t = src.GetTriangles(sub);
                for (int i = 0; i < t.Length; i += 3)
                    {
                    if ((inside[t[i]] || inside[t[i + 1]] || inside[t[i + 2]]) && hide.Add(CoverKey(t[i], t[i + 1], t[i + 2]))) count++;
                }
            }
            Debug.Log("[HeroAccessories] golf glove cover: " + count + " more " + side + " hand triangles hidden under the glove");
        }

        static void Kill(UnityEngine.Object o) { if (!o) return; if (Application.isPlaying) Destroy(o); else DestroyImmediate(o); }
        void OnDestroy() { foreach (var e in worn.Values) foreach (var (m, _) in e.materials) Kill(m); }
    }
}
