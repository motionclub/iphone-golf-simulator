import Foundation
let a = CommandLine.arguments
let d = try! Data(contentsOf: URL(fileURLWithPath: a[1]))
let r = try! (d as NSData).decompressed(using: .lzfse)
try! (r as Data).write(to: URL(fileURLWithPath: a[2]))
