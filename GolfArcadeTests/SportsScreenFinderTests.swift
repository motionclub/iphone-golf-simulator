import CoreVideo
import XCTest
@testable import GolfArcade

/// The court-direction scan only counts while the camera sees the TV with the game on it (SportsScreenFinder), anywhere in the picture
/// (2026-11-08), on synthetic camera images in the camera's format: a grey wall, and a TV with a black bezel showing a striped,
/// coloured picture (or nothing).
final class SportsScreenFinderTests: XCTestCase {
    private enum Picture { case game, off, none, glow }
    /// 640×480 full-range 4:2:0 YCbCr, like the camera's frames. The TV fills x 160–480, y 150–330 (16:9), bezel 12 px, moved by
    /// `dx`, `dy`. `glow`: the picture with no bezel (no edges to find), straight on the wall.
    private func camera(_ picture: Picture, wall: UInt8 = 120, dx: Int = 0, dy: Int = 0) throws -> CVPixelBuffer {
        var made: CVPixelBuffer?
        CVPixelBufferCreate(nil, 640, 480, kCVPixelFormatType_420YpCbCr8BiPlanarFullRange, nil, &made)
        let buffer = try XCTUnwrap(made)
        CVPixelBufferLockBaseAddress(buffer, []); defer { CVPixelBufferUnlockBaseAddress(buffer, []) }
        let luma = try XCTUnwrap(CVPixelBufferGetBaseAddressOfPlane(buffer, 0)).assumingMemoryBound(to: UInt8.self)
        let chroma = try XCTUnwrap(CVPixelBufferGetBaseAddressOfPlane(buffer, 1)).assumingMemoryBound(to: UInt8.self)
        let row = CVPixelBufferGetBytesPerRowOfPlane(buffer, 0), chromaRow = CVPixelBufferGetBytesPerRowOfPlane(buffer, 1)
        func tv(_ x: Int, _ y: Int) -> Bool { picture != .none && x >= 160 + dx && x < 480 + dx && y >= 150 + dy && y < 330 + dy }
        func screen(_ x: Int, _ y: Int) -> Bool { x >= 172 + dx && x < 468 + dx && y >= 162 + dy && y < 318 + dy }
        for y in 0..<480 {
            for x in 0..<640 {
                var l = wall
                if tv(x, y) && (picture != .glow || screen(x, y)) { l = !screen(x, y) || picture == .off ? 12 : ((x / 20 + y / 20) % 2 == 0 ? 220 : 150) }
                luma[y * row + x] = l
            }
        }
        for y in 0..<240 {
            for x in 0..<320 {
                let game = (picture == .game || picture == .glow) && screen(x * 2, y * 2)
                chroma[y * chromaRow + x * 2] = game ? 170 : 128       // Cb: a blue court
                chroma[y * chromaRow + x * 2 + 1] = game ? 110 : 128   // Cr
            }
        }
        return buffer
    }

    func testTheTVWithTheGameOnItIsFound() throws {
        guard case .screen(let at) = SportsScreenFinder.find(try camera(.game)) else { return XCTFail("the TV in the middle was missed") }
        XCTAssertEqual(at.x, 0.5, accuracy: 0.03); XCTAssertEqual(at.y, 0.5, accuracy: 0.03)
    }
    func testATVOffInACornerOfThePictureCountsToo() throws {
        guard case .screen(let at) = SportsScreenFinder.find(try camera(.game, dx: 140, dy: 130)) else { return XCTFail("a TV in the window but off centre was missed") }
        XCTAssertEqual(at.x, 460.0 / 640, accuracy: 0.03, "where it is, for the court direction"); XCTAssertEqual(at.y, 370.0 / 480, accuracy: 0.03)
    }
    func testAGlowingPictureWithNoEdgesCountsInTheMiddle() throws {
        XCTAssertTrue(SportsScreenFinder.glowing(try camera(.glow)))
        XCTAssertFalse(SportsScreenFinder.glowing(try camera(.none)), "a plain wall")
        XCTAssertFalse(SportsScreenFinder.glowing(try camera(.glow, wall: 200)), "no brighter than the room: not a lit screen")
    }
    func testABlankWallIsNotATV() throws {
        XCTAssertEqual(SportsScreenFinder.find(try camera(.none)), .missing(SportsScreenFinder.lookingMessage))
    }
    func testATVThatIsOffDoesNotCount() throws {
        guard case .missing(let why) = SportsScreenFinder.find(try camera(.off)) else { return XCTFail("a dark TV counted as the game") }
        XCTAssertTrue([SportsScreenFinder.darkMessage, SportsScreenFinder.lookingMessage].contains(why), why)
    }

    func testThePictureMustBeLitDetailedAndColourful() {
        XCTAssertEqual(SportsScreenFinder.problem(.init(mean: 20, spread: 40, colour: 20)), SportsScreenFinder.darkMessage)
        XCTAssertEqual(SportsScreenFinder.problem(.init(mean: 160, spread: 4, colour: 20)), SportsScreenFinder.blankMessage, "a blank, lit surface")
        XCTAssertEqual(SportsScreenFinder.problem(.init(mean: 160, spread: 40, colour: 1)), SportsScreenFinder.blankMessage, "grey only: a door, a frame")
        XCTAssertNil(SportsScreenFinder.problem(.init(mean: 120, spread: 40, colour: 20)))
    }
    func testTheTVCanBeAnywhereInThePicture() {
        XCTAssertTrue(SportsScreenFinder.inView(CGRect(x: 0.3, y: 0.3, width: 0.4, height: 0.3)))
        XCTAssertTrue(SportsScreenFinder.inView(CGRect(x: 0.6, y: 0.6, width: 0.3, height: 0.2)), "off in a corner")
        XCTAssertFalse(SportsScreenFinder.inView(CGRect(x: 0, y: 0, width: 1, height: 1)), "the whole picture is not a TV")
    }
    /// The court direction goes through the TV: the image's top row is the upright phone's right edge, its left column the top.
    func testTheDirectionGoesThroughTheTV() {
        let image = SIMD2<Double>(640, 480), tan35 = tan(35 * Double.pi / 180)
        let middle = SportsScreenFinder.ray(at: SIMD2(0.5, 0.5), image: image, tanHalfWidth: tan35)
        XCTAssertEqual(middle.x, 0, accuracy: 1e-9); XCTAssertEqual(middle.y, 0, accuracy: 1e-9); XCTAssertEqual(middle.z, -1, accuracy: 1e-9)
        let right = SportsScreenFinder.ray(at: SIMD2(0.5, 0), image: image, tanHalfWidth: tan35)
        XCTAssertEqual(atan2(right.x, -right.z), atan(tan35 * 0.75), accuracy: 1e-9, "the top row: half the narrow field of view to the right")
        XCTAssertEqual(right.y, 0, accuracy: 1e-9)
        let up = SportsScreenFinder.ray(at: SIMD2(0, 0.5), image: image, tanHalfWidth: tan35)
        XCTAssertEqual(atan2(up.y, -up.z), 35 * Double.pi / 180, accuracy: 1e-9, "the left column: up the phone")
        XCTAssertEqual(up.x, 0, accuracy: 1e-9)
    }
    func testThePatchReadsTheCameraImage() throws {
        let buffer = try camera(.game)
        let inside = try XCTUnwrap(SportsScreenFinder.patch(buffer, in: CGRect(x: 0.3, y: 0.36, width: 0.4, height: 0.28)))
        XCTAssertEqual(inside.mean, 185, accuracy: 15); XCTAssertGreaterThan(inside.spread, 30); XCTAssertEqual(inside.colour, 30, accuracy: 3)
        let wall = try XCTUnwrap(SportsScreenFinder.patch(buffer, in: CGRect(x: 0, y: 0, width: 0.2, height: 0.2)))
        XCTAssertEqual(wall.mean, 120, accuracy: 0.5); XCTAssertEqual(wall.spread, 0, accuracy: 0.5); XCTAssertEqual(wall.colour, 0, accuracy: 0.5)
    }
}
