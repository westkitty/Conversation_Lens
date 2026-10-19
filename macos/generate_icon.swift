import AppKit
import CoreGraphics
import Foundation

let args = CommandLine.arguments
let sourcePath = args.count > 1 ? args[1] : "assets/brand/DEX_Quorum_04_Approved_Compact_Logo.png"
let outputPngPath = args.count > 2 ? args[2] : "macos/ConversationLensIcon.png"
let size = 1024
let colorSpace = CGColorSpaceCreateDeviceRGB()
guard let context = CGContext(
    data: nil,
    width: size,
    height: size,
    bitsPerComponent: 8,
    bytesPerRow: size * 4,
    space: colorSpace,
    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
) else {
    fputs("Could not create icon canvas\n", stderr)
    exit(1)
}
guard let image = NSImage(contentsOfFile: sourcePath)?.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    fputs("Could not read approved Quorum logo at \(sourcePath)\n", stderr)
    exit(1)
}

let tile = CGRect(x: 26, y: 26, width: 972, height: 972)
let path = CGPath(roundedRect: tile, cornerWidth: 208, cornerHeight: 208, transform: nil)
context.addPath(path)
context.clip()
context.setFillColor(NSColor(calibratedRed: 0.035, green: 0.045, blue: 0.065, alpha: 1).cgColor)
context.fill(tile)

// Keep the full approved mark inside the squircle, including the wordmark.
let mark = CGRect(x: 58, y: 58, width: 908, height: 908)
context.draw(image, in: mark)
guard let result = context.makeImage() else {
    fputs("Could not render application icon\n", stderr)
    exit(1)
}
let bitmap = NSBitmapImageRep(cgImage: result)
guard let png = bitmap.representation(using: .png, properties: [:]) else {
    fputs("Could not encode application icon\n", stderr)
    exit(1)
}
let output = URL(fileURLWithPath: outputPngPath)
try FileManager.default.createDirectory(at: output.deletingLastPathComponent(), withIntermediateDirectories: true)
try png.write(to: output)
print("Generated Dex Quorum icon from the approved compact logo at \(outputPngPath)")
