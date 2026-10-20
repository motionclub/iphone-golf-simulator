import Foundation
// CPU packaging only. root invokes after fresh Unity goldens, no GPU.
@main struct PackGolden {
    static func main() throws {
        let args=CommandLine.arguments
        precondition(args.count==3,"PackGolden INPUT_JSON OUTPUT_LZFSE")
        let input=URL(fileURLWithPath:args[1]),output=URL(fileURLWithPath:args[2])
        let raw=try Data(contentsOf:input)
        let packed=try (raw as NSData).compressed(using:.lzfse) as Data
        let decoded=try (packed as NSData).decompressed(using:.lzfse) as Data
        precondition(decoded==raw,"Exact LZFSE golden roundtrip")
        try packed.write(to:output,options:.atomic)
    }
}
