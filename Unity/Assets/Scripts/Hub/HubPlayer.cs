using GolfArcade.Tennis;
using UnityEngine;

namespace GolfArcade.Hub
{
    /// The player's hero in the menu: the match hero under a root that MenuStage stands on the line-up's first slot, facing the
    /// camera; HubHeroAnimator holds its stance and plays its emotes. (It walked the Plaza on the phone's stick until 2026-11-15.)
    public sealed class HubPlayer : MonoBehaviour
    {
        public HubHeroAnimator hero;
        public MatchHeroLook look;
        public bool female;
        /// Held on its slot (MenuStage sets it; nothing moves the hero any more).
        public bool locked;

        float yaw;
        public float Yaw => yaw;

        public static HubPlayer Spawn(Transform parent, bool female, Vector3 at, float facingYaw)
        {
            var root = new GameObject("Hub player");
            root.transform.SetParent(parent, false);
            root.transform.position = at;
            var p = root.AddComponent<HubPlayer>(); p.yaw = facingYaw;
            p.SetHero(female);
            return p;
        }

        /// Puts the male or female match hero under this root (again, when the locker changes the body).
        public void SetHero(bool female)
        {
            if (hero && this.female == female) return;
            if (hero) Destroy(hero.gameObject);
            this.female = female;
            var prefab = TennisCustomization.HeroBase(female);
            if (!prefab) { Debug.LogError("[Hub] match hero prefab missing: " + TennisCustomization.HeroPath(female)); return; }
            var go = Instantiate(prefab, transform, false);
            go.name = female ? "Plaza hero Female" : "Plaza hero Male";
            go.transform.localPosition = Vector3.zero; go.transform.localRotation = Quaternion.Euler(0, yaw, 0);
            HubWorld.SetLayer(go.transform);
            look = go.GetComponent<MatchHeroLook>();
            if (look) HeroAccessories.For(look).SetCarry(true, backItem);   // ACCESSORIES: in the menu the golf bag (or the racket, MENU HERO) is on the back
            // the menu hero stands empty-handed: the racket stays in the bag until a match
            if (look && look.racketGrip) foreach (var r in look.racketGrip.GetComponentsInChildren<Renderer>(true)) r.enabled = false;
            hero = HubHeroAnimator.Attach(go);
        }

        /// MENU HERO: what the menu hero carries on the back, HeroAccessories golf_bag | racket_back (null / "" = the bag).
        string backItem = "golf_bag";
        public void SetBackCarry(string item)
        {
            backItem = System.Array.IndexOf(HeroAccessories.BackCarryItems, item) >= 0 ? item : "golf_bag";
            if (look) HeroAccessories.For(look).SetCarry(true, backItem);
        }

        public void Teleport(Vector3 position, float facingYaw)
        {
            transform.position = position; yaw = facingYaw;
            if (hero) { hero.transform.localRotation = Quaternion.Euler(0, yaw, 0); hero.ResetFootTracking(); }
        }

        void Update()
        {
            float dt = Time.unscaledDeltaTime; if (dt <= 0) return;   // unscaled: a match loading behind the menu pauses Time.timeScale
            if (hero) { hero.transform.localRotation = Quaternion.Euler(0, yaw, 0); hero.Tick(0, dt); }
        }

        public bool PlayEmote(string clip) => hero && hero.Play(clip);
    }
}
