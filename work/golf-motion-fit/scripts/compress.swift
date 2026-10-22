import Foundation
for path in CommandLine.arguments.dropFirst() {
 let url=URL(fileURLWithPath:path)
 let data=try Data(contentsOf:url)
 let packed=try (data as NSData).compressed(using:.lzfse)
 try (packed as Data).write(to:url.deletingPathExtension().appendingPathExtension("lzfse"))
}
