import CoreVideo
import XCTest
@testable import GolfArcade

/// The court-direction scan finds the TV by its blink (SportsScreenFinder, 2026-11-10): the part of the camera's picture that turns
/// bright when the game turns the TV white. Synthetic camera images in the camera's format: a grey wall, a bright window, a TV.
final class SportsScreenFinderTests: XCTestCase {
    /// 640×480 full-range 4:2:0 YCbCr, like the camera's frames. The TV's picture fills x 172–468, y 162–318, moved by `dx`, `dy`, at
    /// luma `tv`; a window (always bright) sits top left; the whole picture is moved by `sway` pixels (a hand that is not still).
    private func camera(tv: UInt8, dx: Int = 0, dy: Int = 0, sway: Int = 0, noTV: Bool = false) throws -> CVPixelBuffer {
        var made: CVPixelBuffer?
        CVPixelBufferCreate(nil, 640, 480, kCVPixelFormatType_420YpCbCr8BiPlanarFullRange, nil, &made)
        let buffer = try XCTUnwrap(made)
        CVPixelBufferLockBaseAddress(buffer, []); defer { CVPixelBufferUnlockBaseAddress(buffer, []) }
        let luma = try XCTUnwrap(CVPixelBufferGetBaseAddressOfPlane(buffer, 0)).assumingMemoryBound(to: UInt8.self)
        let row = CVPixelBufferGetBytesPerRowOfPlane(buffer, 0)
        for y in 0..<480 {
            for x in 0..<640 {
                let sx = x - sway, sy = y - sway
                var l: UInt8 = 110
                if sx >= 20 && sx < 140 && sy >= 20 && sy < 160 { l = 240 }   // the window
                if !noTV && sx >= 172 + dx && sx < 468 + dx && sy >= 162 + dy && sy < 318 + dy { l = tv }
                luma[y * row + x] = l
            }
        }
        return buffer
    }
    private func cells(_ buffer: CVPixelBuffer) throws -> [UInt8] {
        let grid = try XCTUnwrap(SportsScreenFinder.grid(buffer))
        XCTAssertEqual(grid.rows, 60); XCTAssertEqual(grid.cells.count, 80 * 60)
        return grid.cells
    }
    /// Camera frames at 60 a second around a blink drawn at t = 10: the TV black, then white `delay` later for 0.45 s.
    private func blink(delay: Double, dx: Int = 0, dy: Int = 0, swayPerSecond: Double = 0, noTV: Bool = false, blinks: Bool = true) throws -> [SportsScreenFinder.Frame] {
        try stride(from: 9.7, through: 10.8, by: 1.0 / 60).map { t in
            let white = blinks && t >= 10 + delay && t < 10 + delay + 0.45
            return .init(time: t, cells: try cells(try camera(tv: white ? 235 : 12, dx: dx, dy: dy, sway: Int(swayPerSecond * (t - 10)), noTV: noTV)), attitude: nil)
        }
    }

    func testTheBlinkFindsTheTVAndItsDelay() throws {
        let seen = try XCTUnwrap(SportsScreenFinder.sighting(try blink(delay: 0.12), rows: 60, rendered: 10))
        XCTAssertEqual(seen.at.x, 0.5, accuracy: 0.02); XCTAssertEqual(seen.at.y, 0.5, accuracy: 0.02)
        XCTAssertEqual(seen.delay, 0.12, accuracy: 0.02)
    }
    func testTheTVCanBeAnywhereInThePicture() throws {
        let seen = try XCTUnwrap(SportsScreenFinder.sighting(try blink(delay: 0.2, dx: 150, dy: 130), rows: 60, rendered: 10))
        XCTAssertEqual(seen.at.x, 470.0 / 640, accuracy: 0.02); XCTAssertEqual(seen.at.y, 370.0 / 480, accuracy: 0.02)
        XCTAssertEqual(seen.delay, 0.2, accuracy: 0.02)
    }
    func testAHandThatIsNotStillStillFindsIt() throws {
        let frames = try blink(delay: 0.1, swayPerSecond: 60)
        let seen = try XCTUnwrap(SportsScreenFinder.sighting(frames, rows: 60, rendered: 10))
        // where the TV was in the frame it was found in
        let moved = 60 * (frames[seen.frame].time - 10)
        XCTAssertEqual(seen.at.x, 0.5 + moved / 640, accuracy: 0.03); XCTAssertEqual(seen.at.y, 0.5 + moved / 480, accuracy: 0.03)
    }
    func testNothingThatDoesNotBlinkCounts() throws {
        XCTAssertNil(SportsScreenFinder.sighting(try blink(delay: 0.1, noTV: true), rows: 60, rendered: 10), "a bright window, no TV")
        XCTAssertNil(SportsScreenFinder.sighting(try blink(delay: 0.1, swayPerSecond: 60, noTV: true), rows: 60, rendered: 10), "the window's edge moving with the hand")
        XCTAssertNil(SportsScreenFinder.sighting(try blink(delay: 0.1, blinks: false), rows: 60, rendered: 10), "a TV that stays dark")
        XCTAssertNil(SportsScreenFinder.sighting([], rows: 60, rendered: 10))
    }
    func testOnlyAScreenLikePatchCounts() throws {
        let dark = try cells(try camera(tv: 12)), bright = try cells(try camera(tv: 235))
        let lit = try XCTUnwrap(SportsScreenFinder.brightened(dark: dark, bright: bright, rows: 60))
        XCTAssertEqual(lit.cells.count, 37 * 20, accuracy: 60, "the TV's picture, in cells")
        XCTAssertNil(SportsScreenFinder.brightened(dark: dark, bright: dark, rows: 60))
        XCTAssertNil(SportsScreenFinder.brightened(dark: bright, bright: dark, rows: 60), "turning dark is not the blink")
        XCTAssertNil(SportsScreenFinder.brightened(dark: dark, bright: bright, rows: 59), "mismatched grids")
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
}
