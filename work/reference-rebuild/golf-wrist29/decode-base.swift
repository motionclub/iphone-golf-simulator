import Foundation
let repo=URL(fileURLWithPath:CommandLine.arguments[1])
for sex in ["Male","Female"] {
 let input=repo.appendingPathComponent("work/reference-rebuild/original-native-adoption1/export/GolfKitHero_"+sex+".lzfse")
 let d=try (Data(contentsOf:input) as NSData).decompressed(using:.lzfse) as Data
 try d.write(to:repo.appendingPathComponent("work/reference-rebuild/golf-wrist29/"+sex+".base.raw"))
 print(sex,d.count)
}
