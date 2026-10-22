import Foundation
let args=CommandLine.arguments
let input=try Data(contentsOf:URL(fileURLWithPath:args[2])) as NSData
let output = args[1] == "decode" ? try input.decompressed(using:.lzfse) : try input.compressed(using:.lzfse)
try output.write(to:URL(fileURLWithPath:args[3]),options:.atomic)
