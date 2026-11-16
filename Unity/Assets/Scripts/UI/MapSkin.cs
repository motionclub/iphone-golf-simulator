using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.UI
{
    /// UI OVERHAUL (Adnan 2026-11-15, "UI overhaul.zip" → 01 Current UI): every map dresses its HUD in the material of its sculpted
    /// title (Tropical Resort's wood and waves, Sky Tower's lavender tower, Magma Crater's basalt and lava …). Map names stand alone,
    /// players are their usernames only (no YOU, no sport labels). The sculpted pieces (titles, name plates, event banners, cards) are
    /// cut from the boards (Resources/MapSkins/skin-*.png, sample text painted out so the game writes live names on them). The phone
    /// has the same skins (GolfArcade/Unity/MapSkin.swift).
    public sealed class MapSkin
    {
        /// "tennis-resort", "golf-cliffside", "bowling-neon" (the asset names' key).
        public readonly string Id;
        /// The map's name as it stands on its own ("SKY TOWER").
        public readonly string Title;
        /// Panels (scoreboard, cards) top → bottom, the rim of the map's material and its shade.
        public readonly Color Top, Bottom, Frame, FrameDeep;
        /// Cream plates and their ink, the map's light (meters, rings), and the type on the plate.
        public readonly Color Cream, Ink, Glow, PlateText, PlateStroke, CardText, CardStroke;
        /// Where text goes on the plate / event / card art (fractions of the image, top-left origin).
        public readonly Rect PlateBox, EventBox, CardBox;

        MapSkin(string id, string title, string top, string bottom, string frame, string frameDeep, string cream, string ink, string glow,
                string plateText, string plateStroke, string cardText, string cardStroke, Rect plate, Rect evt, Rect card)
        {
            Id = id; Title = title; Top = UiKit.Hex(top); Bottom = UiKit.Hex(bottom); Frame = UiKit.Hex(frame); FrameDeep = UiKit.Hex(frameDeep);
            Cream = UiKit.Hex(cream); Ink = UiKit.Hex(ink); Glow = UiKit.Hex(glow); PlateText = UiKit.Hex(plateText); PlateStroke = UiKit.Hex(plateStroke);
            CardText = UiKit.Hex(cardText); CardStroke = UiKit.Hex(cardStroke); PlateBox = plate; EventBox = evt; CardBox = card;
        }
        static Rect B(float x0, float y0, float x1, float y1) => new Rect(x0, y0, x1 - x0, y1 - y0);
        static readonly Rect None = new Rect(0, 0, 0, 0);

        public static readonly MapSkin[] All =
        {
            new MapSkin("tennis-resort", "TROPICAL RESORT", "1E3C73", "142A55", "D49553", "8A5426", "FFF1D8", "16264A", "35DCCB", "FFF1D8", "0F2147", "16264A", "FFF6E6",
                        B(.286f, .473f, .703f, .665f), B(.221f, .448f, .782f, .714f), None),
            new MapSkin("tennis-skyscraper", "SKY TOWER", "2A2F72", "1C2056", "A592E0", "6A55B8", "FFF3DF", "1D2157", "B9A6FF", "FFF3DF", "151946", "1D2157", "FFF6E6",
                        B(.275f, .514f, .749f, .751f), B(.182f, .485f, .812f, .875f), None),
            new MapSkin("tennis-volcano", "MAGMA CRATER", "2E2629", "1D1719", "463A3D", "1E1719", "FFEBD2", "2A1B16", "FF8B2B", "FFEBD2", "1E1416", "FFEBD2", "1E1416",
                        B(.283f, .293f, .816f, .591f), B(.242f, .429f, .805f, .742f), None),
            new MapSkin("golf-cliffside", "CLIFFSIDE", "1A4F7A", "103757", "EFE3C8", "B8A57F", "FFF4DF", "123A5C", "33E0E4", "143A5C", "FFF6E4", "143A5C", "FFF6E4",
                        B(.258f, .408f, .812f, .741f), None, B(.303f, .129f, .795f, .524f)),
            new MapSkin("golf-wildisles", "WILD ISLES", "2D7032", "1C4B22", "E9D9B5", "A88A5A", "FFF3DB", "1F4A1F", "B7F05A", "FFF3DB", "1C4519", "FFF3DB", "1C4519",
                        B(.247f, .366f, .794f, .671f), None, B(.328f, .236f, .734f, .546f)),
            new MapSkin("golf-magma", "MAGMA OPEN", "3D7A2A", "275219", "3B3230", "1C1514", "FFF0D6", "2A1E14", "FF8B22", "FFF0D6", "1F3A12", "FFF0D6", "1F3A12",
                        B(.248f, .381f, .774f, .642f), None, B(.247f, .24f, .758f, .589f)),
            new MapSkin("bowling-club", "CLUB LANES", "1E2756", "131A3E", "8A5A30", "4E2F16", "FFF1D8", "1B2148", "E9B949", "FFF1D8", "121838", "1B2148", "FFF6E6",
                        B(.232f, .472f, .803f, .75f), None, B(.175f, .373f, .834f, .794f)),
            new MapSkin("bowling-neon", "NEON NIGHTS", "3A1266", "1E0A3C", "8A4DFF", "4A1E9A", "FFF1F8", "2A0B4D", "2DE2F0", "FFF1F8", "D61F86", "FFFFFF", "2A0B4D",
                        B(.208f, .107f, .87f, .644f), None, B(.146f, .189f, .873f, .784f)),
            new MapSkin("bowling-tiki", "TIKI SHORES", "11535A", "0A3A40", "E2AE4C", "9A6A22", "FFF1D6", "123B40", "3FD8C8", "FFF1D6", "0C3A40", "123B40", "FFF6E6",
                        B(.255f, .238f, .769f, .69f), None, B(.195f, .259f, .848f, .741f)),
            new MapSkin("bowling-magma", "MAGMA LANES", "40231D", "241210", "5A3A2E", "2A1712", "FFEBD2", "3A1F18", "FF8B2B", "FFEBD2", "241210", "FFEBD2", "241210",
                        B(.282f, .402f, .87f, .687f), None, B(.112f, .179f, .779f, .632f)),
        };

        public static MapSkin Get(string id) { foreach (var s in All) if (s.Id == id) return s; return All[0]; }

        /// The tennis court being played (TennisVenue.Current).
        public static MapSkin Tennis => Get(GolfArcade.Tennis.TennisVenue.Current switch
        {
            GolfArcade.Tennis.TennisVenueKind.Skyscraper => "tennis-skyscraper",
            GolfArcade.Tennis.TennisVenueKind.Volcano => "tennis-volcano",
            _ => "tennis-resort",
        });
        /// The bowling centre being played (BowlingVenue.Current).
        public static MapSkin Bowling => Get(GolfArcade.Bowling.BowlingVenue.Current switch
        {
            GolfArcade.Bowling.BowlingVenueKind.NeonNights => "bowling-neon",
            GolfArcade.Bowling.BowlingVenueKind.TikiShores => "bowling-tiki",
            GolfArcade.Bowling.BowlingVenueKind.MagmaLanes => "bowling-magma",
            _ => "bowling-club",
        });
        /// A golf course by its key ("cliffside", "wildisles", "magma"; round keys like "cliffside+9" too).
        public static MapSkin Golf(string courseKey)
        {
            var k = (courseKey ?? "").ToLowerInvariant();
            return Get(k.Contains("magma") ? "golf-magma" : k.Contains("wild") ? "golf-wildisles" : "golf-cliffside");
        }

        /// The local player's username from the launch message (the HUDs never say YOU).
        public static string LocalName = "";

        // ---------------------------------------------------------------- assets

        static readonly Dictionary<string, Sprite> sprites = new();
        static Sprite Load(string name)
        {
            if (sprites.TryGetValue(name, out var hit)) return hit;
            var tex = Resources.Load<Texture2D>("MapSkins/" + name);
            Sprite s = null;
            if (tex)
            {
                tex.wrapMode = TextureWrapMode.Clamp;
                s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(.5f, .5f), 100, 0, SpriteMeshType.FullRect);
                s.name = name;
            }
            sprites[name] = s;
            return s;
        }
        public Sprite TitleSprite => Load("skin-title-" + Id);
        public Sprite PlateSprite => Load("skin-plate-" + Id);
        public Sprite EventSprite => Load("skin-event-" + Id);
        public Sprite CardSprite => Load("skin-card-" + Id);
        /// ACE / OUT / FAULT / DEUCE (tennis, board 12).
        public static Sprite Call(string word) => Load("skin-call-" + (word ?? "").ToLowerInvariant());
        /// The map's painted loading pictures (golf: Resources/MapSkins/load-golf-*.jpg).
        public Texture2D LoadingArt(int pick)
        {
            string[] names = Id switch
            {
                "golf-cliffside" => new[] { "load-golf-cliffside-male", "load-golf-cliffside-female" },
                "golf-magma" => new[] { "load-golf-magma-male", "load-golf-magma-female" },
                "golf-wildisles" => new[] { "load-golf-wildisles-male" },
                _ => new string[0],
            };
            return names.Length == 0 ? null : Resources.Load<Texture2D>("MapSkins/" + names[Mathf.Abs(pick) % names.Length]);
        }

        static Font bold, semi;
        /// Fredoka (OFL): the sculpted lettering's live twin. Rubik ExtraBold if missing.
        public static Font Bold => bold ??= Resources.Load<Font>("Fonts/Fredoka/Fredoka-Bold") ?? UiKit.Display;
        public static Font Semi => semi ??= Resources.Load<Font>("Fonts/Fredoka/Fredoka-SemiBold") ?? UiKit.Strong;

        // ---------------------------------------------------------------- builders

        /// An image of `sprite` at `height` canvas units, its width from the art's aspect.
        public static Image Art(string name, RectTransform parent, Sprite sprite, float height, Vector2 anchor, Vector2 pos)
        {
            var img = new GameObject(name).AddComponent<Image>();
            img.transform.SetParent(parent, false);
            img.sprite = sprite; img.preserveAspect = true; img.raycastTarget = false;
            var rt = img.rectTransform; rt.anchorMin = rt.anchorMax = anchor; rt.pivot = new Vector2(.5f, .5f); rt.anchoredPosition = pos;
            float aspect = sprite ? sprite.rect.width / Mathf.Max(1, sprite.rect.height) : 3;
            rt.sizeDelta = new Vector2(height * aspect, height);
            return img;
        }

        /// Raised lettering: a fill, an outline all round and a soft drop (as the boards' sculpted type).
        public static Text Letters(string name, RectTransform parent, string text, Font font, int size, Color fill, Color stroke, float strokeWidth)
        {
            var t = new GameObject(name).AddComponent<Text>();
            t.transform.SetParent(parent, false);
            t.font = font; t.fontSize = size; t.color = fill; t.text = text; t.alignment = TextAnchor.MiddleCenter; t.raycastTarget = false;
            t.horizontalOverflow = HorizontalWrapMode.Wrap; t.verticalOverflow = VerticalWrapMode.Truncate;
            t.resizeTextForBestFit = true; t.resizeTextMinSize = Mathf.Max(8, size / 3); t.resizeTextMaxSize = size;
            if (strokeWidth > 0)
            {
                var a = t.gameObject.AddComponent<Outline>(); a.effectColor = stroke; a.effectDistance = new Vector2(strokeWidth, -strokeWidth);
                var b = t.gameObject.AddComponent<Outline>(); b.effectColor = stroke; b.effectDistance = new Vector2(-strokeWidth, strokeWidth);
                var s = t.gameObject.AddComponent<Shadow>(); s.effectColor = new Color(0, 0, 0, .35f); s.effectDistance = new Vector2(0, -strokeWidth * 1.6f);
            }
            return t;
        }

        public enum Piece { Plate, Event, Card }
        /// A sculpted piece with live type in its window: a username on the plate, POINT + name on the event, a number on the card.
        /// Returns the text; its parent is the art (move and scale that). Null art (asset missing) still gives a cream pill.
        public Text Plate(string name, RectTransform parent, Piece piece, string text, float height, Vector2 anchor, Vector2 pos)
        {
            var sprite = piece == Piece.Plate ? PlateSprite : piece == Piece.Event ? EventSprite : CardSprite;
            var box = piece == Piece.Plate ? PlateBox : piece == Piece.Event ? (EventBox.width > 0 ? EventBox : PlateBox) : (CardBox.width > 0 ? CardBox : PlateBox);
            var art = Art(name, parent, sprite, height, anchor, pos);
            if (!sprite) { art.sprite = GlassKit.RoundRect; art.type = Image.Type.Sliced; art.color = Frame; art.preserveAspect = false; box = B(.1f, .15f, .9f, .85f); }
            var size = art.rectTransform.sizeDelta;
            var fill = piece == Piece.Card ? CardText : PlateText; var stroke = piece == Piece.Card ? CardStroke : PlateStroke;
            int font = Mathf.RoundToInt(box.height * size.y * 0.92f);
            var t = Letters("Text", art.rectTransform, text, Bold, font, fill, stroke, Mathf.Max(1.2f, height * .02f));
            var rt = t.rectTransform; rt.anchorMin = rt.anchorMax = new Vector2(0, 1); rt.pivot = new Vector2(0, 1);
            rt.sizeDelta = new Vector2(box.width * size.x, box.height * size.y);
            rt.anchoredPosition = new Vector2(box.x * size.x, -box.y * size.y);
            return t;
        }

        /// A panel of the map's material: a rim of its frame, the face in its colours, a soft drop. Returns the face.
        public Image Panel(string name, RectTransform parent, Vector2 anchor, Vector2 size, Vector2 pos, float rim = 5, float alpha = .94f)
        {
            var drop = new GameObject(name).AddComponent<Image>();
            drop.transform.SetParent(parent, false);
            drop.sprite = GlassKit.RoundRect; drop.type = Image.Type.Sliced; drop.pixelsPerUnitMultiplier = 2.4f; drop.raycastTarget = false;
            drop.color = FrameDeep;
            var rt = drop.rectTransform; rt.anchorMin = rt.anchorMax = anchor; rt.pivot = new Vector2(.5f, .5f);
            rt.sizeDelta = size + Vector2.one * rim * 2; rt.anchoredPosition = pos + new Vector2(0, -4);
            var edge = Child("Rim", rt, size + Vector2.one * rim * 2, new Vector2(0, 4), Frame);
            var face = Child("Face", edge.rectTransform, size, Vector2.zero, Color.white);
            GolfArcade.Tennis.UiGradient.On(face, new Color(Top.r, Top.g, Top.b, alpha), new Color(Bottom.r, Bottom.g, Bottom.b, alpha));
            return face;
        }
        static Image Child(string name, RectTransform parent, Vector2 size, Vector2 pos, Color color)
        {
            var img = new GameObject(name).AddComponent<Image>();
            img.transform.SetParent(parent, false);
            img.sprite = GlassKit.RoundRect; img.type = Image.Type.Sliced; img.pixelsPerUnitMultiplier = 2.4f; img.color = color; img.raycastTarget = false;
            var rt = img.rectTransform; rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(.5f, .5f); rt.sizeDelta = size; rt.anchoredPosition = pos;
            return img;
        }
    }
}
