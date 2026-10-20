import Foundation
import Metal

let dir = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let output = URL(fileURLWithPath: CommandLine.arguments[2])
let device = MTLCreateSystemDefaultDevice()!
let queue = device.makeCommandQueue()!
let manager = MTLCaptureManager.shared()
let capture = MTLCaptureDescriptor()
capture.captureObject = device
capture.destination = .gpuTraceDocument
capture.outputURL = output
try? FileManager.default.removeItem(at: output)
try manager.startCapture(with: capture)
let producer = """
struct ProofVaryings {
 float4 position [[position]];
 float2 uv [[user(TEXCOORD0)]];
 float3 world [[user(TEXCOORD1)]];
 float3 normal [[user(TEXCOORD2)]];
 float4 tangent [[user(TEXCOORD3)]];
};
vertex ProofVaryings clothProofVertex(uint id [[vertex_id]]) {
 float2 p=float2((id<<1)&2,id&2);
 ProofVaryings o;
 o.position=float4(p*2-1,0,1); o.uv=p;
 o.world=float3(p,0); o.normal=float3(0,0,1); o.tangent=float4(1,0,0,1);
 return o;
}
"""
let targetDesc = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba16Float, width: 128, height: 128, mipmapped: false)
targetDesc.usage = [.renderTarget,.shaderRead]
let target = device.makeTexture(descriptor: targetDesc)!
let texDesc = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm, width: 16, height: 16, mipmapped: false)
texDesc.usage = .shaderRead
let tex = device.makeTexture(descriptor: texDesc)!
var pixels = [UInt8](repeating: 128, count: 16*16*4)
pixels.withUnsafeBytes { tex.replace(region: MTLRegionMake2D(0,0,16,16), mipmapLevel: 0, withBytes: $0.baseAddress!, bytesPerRow: 64) }
let depthDesc = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .depth32Float, width: 16, height: 16, mipmapped: false)
depthDesc.usage = [.shaderRead,.renderTarget]
let depth = device.makeTexture(descriptor: depthDesc)!
let buffer = device.makeBuffer(length: 16384, options: .storageModeShared)!
let numbers = buffer.contents().bindMemory(to: Float.self, capacity: 4096)
for i in 0..<4096 { numbers[i] = 1 }
let samplerDesc = MTLSamplerDescriptor(); samplerDesc.minFilter = .linear; samplerDesc.magFilter = .linear
let sampler = device.makeSamplerState(descriptor: samplerDesc)!
for variant in ["before_plain","after_plain","before_court","after_court"] {
 let file = try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil).first { $0.lastPathComponent.hasPrefix(variant+"_") && $0.pathExtension == "msl" }!
 let source = try String(contentsOf: file, encoding: .utf8)
 let options = MTLCompileOptions(); options.fastMathEnabled = true
 let library = try device.makeLibrary(source: source+"\n"+producer, options: options)
 library.label = "Unity CompileVariant: " + variant
 let constants = MTLFunctionConstantValues(); var remap: UInt32 = 0
 constants.setConstantValue(&remap, type: .uint, index: 1)
 let fragment = try library.makeFunction(name: "xlatMtlMain", constantValues: constants)
 let desc = MTLRenderPipelineDescriptor(); desc.label = "TennisCloth / " + variant
 desc.vertexFunction = library.makeFunction(name: "clothProofVertex")
 desc.fragmentFunction = fragment; desc.colorAttachments[0].pixelFormat = .rgba16Float
 let pipeline = try device.makeRenderPipelineState(descriptor: desc)
 let cb = queue.makeCommandBuffer()!; cb.label = variant
 let pass = MTLRenderPassDescriptor(); pass.colorAttachments[0].texture = target
 pass.colorAttachments[0].loadAction = .clear; pass.colorAttachments[0].storeAction = .store
 let encoder = cb.makeRenderCommandEncoder(descriptor: pass)!
 encoder.label = "Unity compiled fragment / " + variant
 encoder.setRenderPipelineState(pipeline)
 for i in 0..<8 { encoder.setFragmentBuffer(buffer, offset: 0, index: i); encoder.setFragmentTexture(tex,index:i); encoder.setFragmentSamplerState(sampler,index:i) }
 if variant.hasSuffix("court") { encoder.setFragmentTexture(depth,index:4) }
 encoder.drawPrimitives(type:.triangle,vertexStart:0,vertexCount:3)
 encoder.endEncoding(); cb.commit(); cb.waitUntilCompleted()
 if let e = cb.error { print("COMMAND_ERROR \(variant) \(e)") }
 print("COMPILED \(variant) device=\(device.name)")
}
manager.stopCapture()
print("TRACE_COMPLETE \(output.path)")
