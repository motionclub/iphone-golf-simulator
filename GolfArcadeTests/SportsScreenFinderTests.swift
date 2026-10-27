import CoreVideo
import XCTest
@testable import GolfArcade

/// The court-direction scan only counts while the camera sees the TV with the game on it (SportsScreenFinder), on synthetic camera
/// images in ARKit's format: a grey wall, and a TV with a black bezel showing a striped, coloured picture (or nothing).
final class SportsScreenFinderTests: XCTestCase {
    private enum Picture { case game, off, none }
    /// 640×480 full-range 4:2:0 YCbCr, like ARKit's capturedImage. The TV fills x 160–480, y 150–330 (16:9), bezel 12 px.
    private func camera(_ picture: Picture, wall: UInt8 = 120) throws -> CVPixelBuffer {
        var made: CVPixelBuffer?
        CVPixelBufferCreate(nil, 640, 480, kCVPixelFormatType_420YpCbCr8BiPlanarFullRange, nil, &made)
        let buffer = try XCTUnwrap(made)
        CVPixelBufferLockBaseAddress(buffer, []); defer { CVPixelBufferUnlockBaseAddress(buffer, []) }
        let luma = try XCTUnwrap(CVPixelBufferGetBaseAddressOfPlane(buffer, 0)).assumingMemoryBound(to: UInt8.self)
        let chroma = try XCTUnwrap(CVPixelBufferGetBaseAddressOfPlane(buffer, 1)).assumingMemoryBound(to: UInt8.self)
        let row = CVPixelBufferGetBytesPerRowOfPlane(buffer, 0), chromaRow = CVPixelBufferGetBytesPerRowOfPlane(buffer, 1)
        func tv(_ x: Int, _ y: Int) -> Bool { picture != .none && x >= 160 && x < 480 && y >= 150 && y < 330 }
        func screen(_ x: Int, _ y: Int) -> Bool { x >= 172 && x < 468 && y >= 162 && y < 318 }
        for y in 0..<480 {
            for x in 0..<640 {
                var l = wall
                if tv(x, y) { l = !screen(x, y) || picture == .off ? 12 : ((x / 20 + y / 20) % 2 == 0 ? 170 : 90) }
                luma[y * row + x] = l
            }
        }
        for y in 0..<240 {
            for x in 0..<320 {
                let game = picture == .game && screen(x * 2, y * 2)
                chroma[y * chromaRow + x * 2] = game ? 170 : 128       // Cb: a blue court
                chroma[y * chromaRow + x * 2 + 1] = game ? 110 : 128   // Cr
            }
        }
        return buffer
    }

    func testTheTVWithTheGameOnItIsFound() throws {
        XCTAssertEqual(SportsScreenFinder.find(try camera(.game)), .screen)
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
    func testThePhoneMustBeAimedAtIt() {
        XCTAssertTrue(SportsScreenFinder.aimed(at: CGRect(x: 0.3, y: 0.3, width: 0.4, height: 0.3)))
        XCTAssertTrue(SportsScreenFinder.aimed(at: CGRect(x: 0.52, y: 0.3, width: 0.4, height: 0.3)), "a little off centre is fine")
        XCTAssertFalse(SportsScreenFinder.aimed(at: CGRect(x: 0.6, y: 0.6, width: 0.3, height: 0.2)), "off in a corner")
        XCTAssertFalse(SportsScreenFinder.aimed(at: CGRect(x: 0, y: 0, width: 1, height: 1)), "the whole picture is not a TV")
    }
    func testThePatchReadsTheCameraImage() throws {
        let buffer = try camera(.game)
        let inside = try XCTUnwrap(SportsScreenFinder.patch(buffer, in: CGRect(x: 0.3, y: 0.36, width: 0.4, height: 0.28)))
        XCTAssertEqual(inside.mean, 130, accuracy: 15); XCTAssertGreaterThan(inside.spread, 30); XCTAssertEqual(inside.colour, 30, accuracy: 3)
        let wall = try XCTUnwrap(SportsScreenFinder.patch(buffer, in: CGRect(x: 0, y: 0, width: 0.2, height: 0.2)))
        XCTAssertEqual(wall.mean, 120, accuracy: 0.5); XCTAssertEqual(wall.spread, 0, accuracy: 0.5); XCTAssertEqual(wall.colour, 0, accuracy: 0.5)
    }
}
