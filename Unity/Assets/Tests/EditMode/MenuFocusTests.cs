using GolfArcade.UI;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// MENU FOCUS: the phone's stick picks the nearest TV button the way it is pushed.
    public sealed class MenuFocusTests
    {
        // the round card: NEXT HOLE across the top, PLAY AGAIN and MAIN MENU under it (y up)
        static readonly Vector2[] Card = { new(0, 100), new(-120, 0), new(120, 0) };

        [Test]
        public void DownGoesToTheButtonsUnderTheWayOn()
        {
            Assert.AreEqual(1, MenuFocus.Pick(Card, 0, new Vector2(-.3f, -1)), "down and a little left: play again");
            Assert.AreEqual(2, MenuFocus.Pick(Card, 0, new Vector2(.3f, -1)), "down and a little right: main menu");
        }

        [Test]
        public void SidewaysAndUpMoveOnlyWhereThereIsAButton()
        {
            Assert.AreEqual(2, MenuFocus.Pick(Card, 1, Vector2.right));
            Assert.AreEqual(1, MenuFocus.Pick(Card, 1, Vector2.left), "nothing further left: stays put");
            Assert.AreEqual(0, MenuFocus.Pick(Card, 2, Vector2.up));
            Assert.AreEqual(0, MenuFocus.Pick(Card, 0, Vector2.up), "nothing above: stays put");
        }

        [Test]
        public void NoButtonsOrNoPushLeavesTheRingAlone()
        {
            Assert.AreEqual(-1, MenuFocus.Pick(new Vector2[0], 0, Vector2.up));
            Assert.AreEqual(1, MenuFocus.Pick(Card, 1, Vector2.zero));
        }
    }
}
