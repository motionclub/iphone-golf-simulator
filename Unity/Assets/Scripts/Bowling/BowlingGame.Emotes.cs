using System;
using System.Collections.Generic;
using System.Linq;
using GolfArcade.Multiplayer;
using GolfArcade.Tennis;
using UnityEngine;

namespace GolfArcade.Bowling
{
    /// Adnan 11-22: "allow players to emote whenever they want when it's not their turn". A player who is not up plays one of their three
    /// equipped emotes (the locker's, as in tennis and golf) from their phone; their hero does it where they stand beside the lane. In a
    /// game across phones every phone plays it on its own lane (a peer "emote"), so the screen and the other phones all see it.
    public sealed partial class BowlingGame
    {
        /// Each player's three equipped emote ids (TennisEmotes), player order; missing = the defaults.
        readonly List<string[]> playerEmotes = new List<string[]>();
        readonly Dictionary<int, float> lastEmote = new Dictionary<int, float>();
        const float EmoteCooldown = 1.5f;

        /// This phone's own player's equipped emotes (the start message's `emotes`).
        public void EquipEmotes(string[] ids)
        {
            int p = Mathf.Max(0, LocalPlayer);
            while (playerEmotes.Count <= p) playerEmotes.Add(null);
            playerEmotes[p] = TennisEmotes.Normalize(ids);
        }
        string[] EmotesOf(int player) => player >= 0 && player < playerEmotes.Count && playerEmotes[player] != null ? playerEmotes[player] : TennisEmotes.Normalize(null);
        void EquipNetworkEmotes(IEnumerable<string[]> seated)
        {
            playerEmotes.Clear(); playerEmotes.AddRange(seated.Select(TennisEmotes.Normalize)); lastEmote.Clear();
        }

        /// This phone's player may emote now: they are in the game and someone else is up (not after the game).
        public bool CanEmote => CanEmoteAs(LocalPlayer);
        bool CanEmoteAs(int player) =>
            Initialized && player >= 0 && player < heroes.Count && heroes[player] && player != Current && !IsCpu(player) && Flow != Phase.GameOver
            && (!lastEmote.TryGetValue(player, out float at) || Time.time - at >= EmoteCooldown);

        /// The phone's emote button (slot 0..2 of the equipped three). False when it is this player's turn (or too soon after the last one).
        public bool PlayerEmote(int slot)
        {
            int p = LocalPlayer;
            if (slot < 0 || slot > 2 || !CanEmoteAs(p)) return false;
            string id = EmotesOf(p)[slot];
            if (!PlayEmoteOn(p, id)) return false;
            if (Networked && p < seatOfPlayer.Length)
                SportsMultiplayer.Instance?.SendPeer(JsonUtility.ToJson(new NetBall { kind = "emote", ball = ballsBowled, seat = seatOfPlayer[p], emote = id }), true);
            return true;
        }

        /// Proof films: `player` (not up) plays emote `id`, as their phone's button would.
        public bool EmoteAs(int player, string id) => CanEmoteAs(player) && PlayEmoteOn(player, id);

        /// Another phone's player emoted: the same move on their hero here.
        void ReceiveEmote(NetBall m)
        {
            int p = Array.IndexOf(seatOfPlayer, m.seat);
            if (p < 0 || p == LocalPlayer || p >= heroes.Count || Array.IndexOf(TennisEmotes.IDs, m.emote) < 0) return;
            PlayEmoteOn(p, m.emote);
        }

        bool PlayEmoteOn(int player, string id)
        {
            var h = player >= 0 && player < heroes.Count ? heroes[player] : null;
            if (!h || !TennisEmotes.TryClip(id, out var clip)) return false;
            if (!h.Arrived) h.Snap();   // (a walk to their spot ends where it was going: moving would cancel the emote)
            if (!h.React(clip.ToString())) return false;
            lastEmote[player] = Time.time;
            return true;
        }
    }
}
