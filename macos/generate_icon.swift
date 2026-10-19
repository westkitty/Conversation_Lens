import AppKit
import CoreGraphics
import Foundation

let args = CommandLine.arguments
let sourcePath = args.count > 1 ? args[1] : "/Volumes/wc2tb/stationary/assets/brand/source/west-cat-logo-original.png"
let outputPngPath = args.count > 2 ? args[2] : "macos/ConversationLensIcon.png"

let size = 1024
let colorSpace = CGColorSpaceCreateDeviceRGB()
guard let ctx = CGContext(
    data: nil,
    width: size,
    height: size,
    bitsPerComponent: 8,
    bytesPerRow: size * 4,
    space: colorSpace,
    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
) else {
    fputs("Failed to create CGContext\n", stderr)
    exit(1)
}

NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(cgContext: ctx, flipped: false)

let rect = NSRect(x: 52, y: 52, width: 920, height: 920)
let squircle = NSBezierPath(roundedRect: rect, xRadius: 208, yRadius: 208)

// Drop shadow behind squircle
ctx.saveGState()
ctx.setShadow(offset: CGSize(width: 0, height: -18), blur: 36, color: NSColor(calibratedWhite: 0, alpha: 0.65).cgColor)
NSColor(calibratedRed: 0.04, green: 0.05, blue: 0.08, alpha: 1.0).setFill()
squircle.fill()
ctx.restoreGState()

ctx.saveGState()
squircle.addClip()

// Deep obsidian -> midnight -> crimson-burgundy gradient
let bgColors = [
    NSColor(calibratedRed: 0.04, green: 0.05, blue: 0.08, alpha: 1.0).cgColor,
    NSColor(calibratedRed: 0.09, green: 0.12, blue: 0.17, alpha: 1.0).cgColor,
    NSColor(calibratedRed: 0.28, green: 0.13, blue: 0.17, alpha: 1.0).cgColor
] as CFArray
if let grad = CGGradient(colorsSpace: colorSpace, colors: bgColors, locations: [0.0, 0.58, 1.0]) {
    ctx.drawLinearGradient(
        grad,
        start: CGPoint(x: 120, y: 80),
        end: CGPoint(x: 900, y: 940),
        options: []
    )
}

// Radial cyan observatory glow behind central lens
let glowColors = [
    NSColor(calibratedRed: 0.58, green: 0.81, blue: 0.87, alpha: 0.28).cgColor,
    NSColor(calibratedRed: 1.0, green: 0.42, blue: 0.40, alpha: 0.12).cgColor,
    NSColor(calibratedRed: 0.04, green: 0.05, blue: 0.08, alpha: 0.0).cgColor
] as CFArray
if let radial = CGGradient(colorsSpace: colorSpace, colors: glowColors, locations: [0.0, 0.55, 1.0]) {
    ctx.drawRadialGradient(
        radial,
        startCenter: CGPoint(x: 512, y: 520),
        startRadius: 20,
        endCenter: CGPoint(x: 512, y: 520),
        endRadius: 430,
        options: []
    )
}

// Horizontal stratigraphy horizon rails across lower third
let strataY: [(CGFloat, NSColor)] = [
    (210, NSColor(calibratedRed: 1.00, green: 0.42, blue: 0.40, alpha: 0.26)),
    (265, NSColor(calibratedRed: 0.66, green: 0.86, blue: 0.75, alpha: 0.30)),
    (320, NSColor(calibratedRed: 0.58, green: 0.81, blue: 0.87, alpha: 0.34))
]
for (y, col) in strataY {
    let line = NSBezierPath()
    line.move(to: NSPoint(x: 96, y: y))
    line.line(to: NSPoint(x: 928, y: y))
    line.lineWidth = 3
    let dash: [CGFloat] = [10, 8]
    line.setLineDash(dash, count: 2, phase: 0)
    col.setStroke()
    line.stroke()
}

// Acoustic waveform curve
let wave = NSBezierPath()
wave.move(to: NSPoint(x: 96, y: 265))
for i in 1...80 {
    let t = CGFloat(i) / 80.0
    let x = 96.0 + t * 832.0
    let env = sin(t * .pi)
    let y = 265.0 + sin(t * .pi * 8.0) * 48.0 * env
    wave.line(to: NSPoint(x: x, y: y))
}
wave.lineWidth = 5.5
NSColor(calibratedRed: 0.58, green: 0.81, blue: 0.87, alpha: 0.55).setStroke()
wave.stroke()

// Concentric calibrated optical/acoustic lens rings
let center = NSPoint(x: 512, y: 525)
let rings: [(CGFloat, CGFloat, NSColor, Bool)] = [
    (370, 5.0, NSColor(calibratedRed: 0.58, green: 0.81, blue: 0.87, alpha: 0.38), true),
    (326, 8.0, NSColor(calibratedRed: 0.93, green: 0.80, blue: 0.57, alpha: 0.55), false),
    (294, 4.0, NSColor(calibratedRed: 1.00, green: 0.42, blue: 0.40, alpha: 0.65), false)
]
for (r, lw, col, dashed) in rings {
    let ringRect = NSRect(x: center.x - r, y: center.y - r, width: r * 2, height: r * 2)
    let path = NSBezierPath(ovalIn: ringRect)
    path.lineWidth = lw
    if dashed {
        let pattern: [CGFloat] = [18, 12]
        path.setLineDash(pattern, count: 2, phase: 0)
    }
    col.setStroke()
    path.stroke()
}

// Dark glass inner aperture disc
let innerR: CGFloat = 282
let innerDisc = NSBezierPath(ovalIn: NSRect(x: center.x - innerR, y: center.y - innerR, width: innerR * 2, height: innerR * 2))
NSColor(calibratedRed: 0.05, green: 0.08, blue: 0.12, alpha: 0.82).setFill()
innerDisc.fill()

// Composite the WestCat brand asset from the drive inside the lens aperture
if let img = NSImage(contentsOfFile: sourcePath) {
    ctx.saveGState()
    innerDisc.addClip()
    let drawRect = NSRect(x: center.x - 255, y: center.y - 265, width: 510, height: 510)
    img.draw(in: drawRect, from: .zero, operation: .sourceOver, fraction: 1.0)
    ctx.restoreGState()
} else {
    fputs("Warning: Could not load source image at \(sourcePath)\n", stderr)
}

// Lens aperture rim highlight
innerDisc.lineWidth = 7.0
NSColor(calibratedRed: 0.58, green: 0.81, blue: 0.87, alpha: 0.88).setStroke()
innerDisc.stroke()

// Live acoustic beacon badge (top-right of lens)
let beaconCenter = NSPoint(x: 760, y: 775)
let outerBeacon = NSBezierPath(ovalIn: NSRect(x: beaconCenter.x - 36, y: beaconCenter.y - 36, width: 72, height: 72))
NSColor(calibratedRed: 0.16, green: 0.09, blue: 0.12, alpha: 0.95).setFill()
outerBeacon.fill()
outerBeacon.lineWidth = 4.5
NSColor(calibratedRed: 1.00, green: 0.42, blue: 0.40, alpha: 0.95).setStroke()
outerBeacon.stroke()

let innerBeacon = NSBezierPath(ovalIn: NSRect(x: beaconCenter.x - 16, y: beaconCenter.y - 16, width: 32, height: 32))
NSColor(calibratedRed: 1.00, green: 0.42, blue: 0.40, alpha: 1.0).setFill()
innerBeacon.fill()

// Bottom "LENS v6" pill badge
let pillRect = NSRect(x: 352, y: 108, width: 320, height: 64)
let pill = NSBezierPath(roundedRect: pillRect, xRadius: 32, yRadius: 32)
NSColor(calibratedRed: 0.07, green: 0.11, blue: 0.16, alpha: 0.94).setFill()
pill.fill()
pill.lineWidth = 3.5
NSColor(calibratedRed: 0.58, green: 0.81, blue: 0.87, alpha: 0.78).setStroke()
pill.stroke()

let paragraph = NSMutableParagraphStyle()
paragraph.alignment = .center
let attrs: [NSAttributedString.Key: Any] = [
    .font: NSFont.monospacedSystemFont(ofSize: 28, weight: .bold),
    .foregroundColor: NSColor(calibratedRed: 0.93, green: 0.95, blue: 0.98, alpha: 1.0),
    .kern: 3.2,
    .paragraphStyle: paragraph
]
let label = NSAttributedString(string: "LENS · v6", attributes: attrs)
label.draw(in: NSRect(x: pillRect.minX, y: pillRect.minY + 14, width: pillRect.width, height: 40))

ctx.restoreGState()

// Outer squircle metallic rim
squircle.lineWidth = 8.0
NSColor(calibratedRed: 0.74, green: 0.47, blue: 0.45, alpha: 0.72).setStroke()
squircle.stroke()

NSGraphicsContext.restoreGraphicsState()

guard let cgImage = ctx.makeImage() else {
    fputs("Failed to make CGImage\n", stderr)
    exit(1)
}
let rep = NSBitmapImageRep(cgImage: cgImage)
guard let pngData = rep.representation(using: .png, properties: [:]) else {
    fputs("Failed to encode PNG\n", stderr)
    exit(1)
}
let outURL = URL(fileURLWithPath: outputPngPath)
try FileManager.default.createDirectory(at: outURL.deletingLastPathComponent(), withIntermediateDirectories: true)
try pngData.write(to: outURL)
print("Generated icon PNG at \(outputPngPath)")
