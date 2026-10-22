import Foundation
let args=CommandLine.arguments
let d=try Data(contentsOf:URL(fileURLWithPath:args[1]))
let raw=try (d as NSData).decompressed(using:.lzfse)
try (raw as Data).write(to:URL(fileURLWithPath:args[2]))
