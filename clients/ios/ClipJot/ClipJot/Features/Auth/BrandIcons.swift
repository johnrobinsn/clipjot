import SwiftUI

/// Official Google "G" logo with brand colors
struct GoogleIcon: View {
    var size: CGFloat = 24

    var body: some View {
        Canvas { context, canvasSize in
            let scale = canvasSize.width / 24

            // Blue path
            let bluePath = Path { path in
                path.move(to: CGPoint(x: 22.56, y: 12.25))
                path.addCurve(
                    to: CGPoint(x: 22.36, y: 10),
                    control1: CGPoint(x: 22.56, y: 11.47),
                    control2: CGPoint(x: 22.49, y: 10.72)
                )
                path.addLine(to: CGPoint(x: 12, y: 10))
                path.addLine(to: CGPoint(x: 12, y: 14.26))
                path.addLine(to: CGPoint(x: 17.92, y: 14.26))
                path.addCurve(
                    to: CGPoint(x: 15.71, y: 17.57),
                    control1: CGPoint(x: 17.66, y: 15.63),
                    control2: CGPoint(x: 16.88, y: 16.79)
                )
                path.addLine(to: CGPoint(x: 15.71, y: 20.34))
                path.addLine(to: CGPoint(x: 19.28, y: 20.34))
                path.addCurve(
                    to: CGPoint(x: 22.56, y: 12.25),
                    control1: CGPoint(x: 21.36, y: 18.42),
                    control2: CGPoint(x: 22.56, y: 15.6)
                )
                path.closeSubpath()
            }.applying(CGAffineTransform(scaleX: scale, y: scale))
            context.fill(bluePath, with: .color(Color(hex: 0x4285F4)))

            // Green path
            let greenPath = Path { path in
                path.move(to: CGPoint(x: 12, y: 23))
                path.addCurve(
                    to: CGPoint(x: 19.28, y: 20.34),
                    control1: CGPoint(x: 14.97, y: 23),
                    control2: CGPoint(x: 17.46, y: 22.02)
                )
                path.addLine(to: CGPoint(x: 15.71, y: 17.57))
                path.addCurve(
                    to: CGPoint(x: 12, y: 18.63),
                    control1: CGPoint(x: 14.73, y: 18.23),
                    control2: CGPoint(x: 13.48, y: 18.63)
                )
                path.addCurve(
                    to: CGPoint(x: 5.84, y: 14.1),
                    control1: CGPoint(x: 9.14, y: 18.63),
                    control2: CGPoint(x: 6.71, y: 16.7)
                )
                path.addLine(to: CGPoint(x: 2.18, y: 16.94))
                path.addCurve(
                    to: CGPoint(x: 12, y: 23),
                    control1: CGPoint(x: 3.99, y: 20.53),
                    control2: CGPoint(x: 7.7, y: 23)
                )
                path.closeSubpath()
            }.applying(CGAffineTransform(scaleX: scale, y: scale))
            context.fill(greenPath, with: .color(Color(hex: 0x34A853)))

            // Yellow path
            let yellowPath = Path { path in
                path.move(to: CGPoint(x: 5.84, y: 14.09))
                path.addCurve(
                    to: CGPoint(x: 5.49, y: 12),
                    control1: CGPoint(x: 5.62, y: 13.43),
                    control2: CGPoint(x: 5.49, y: 12.73)
                )
                path.addCurve(
                    to: CGPoint(x: 5.84, y: 9.91),
                    control1: CGPoint(x: 5.49, y: 11.27),
                    control2: CGPoint(x: 5.62, y: 10.57)
                )
                path.addLine(to: CGPoint(x: 5.84, y: 7.07))
                path.addLine(to: CGPoint(x: 2.18, y: 7.07))
                path.addCurve(
                    to: CGPoint(x: 1, y: 12),
                    control1: CGPoint(x: 1.43, y: 8.55),
                    control2: CGPoint(x: 1, y: 10.22)
                )
                path.addCurve(
                    to: CGPoint(x: 2.18, y: 16.93),
                    control1: CGPoint(x: 1, y: 13.78),
                    control2: CGPoint(x: 1.43, y: 15.45)
                )
                path.addLine(to: CGPoint(x: 5.84, y: 14.09))
                path.closeSubpath()
            }.applying(CGAffineTransform(scaleX: scale, y: scale))
            context.fill(yellowPath, with: .color(Color(hex: 0xFBBC05)))

            // Red path
            let redPath = Path { path in
                path.move(to: CGPoint(x: 12, y: 5.38))
                path.addCurve(
                    to: CGPoint(x: 16.21, y: 7.02),
                    control1: CGPoint(x: 13.62, y: 5.38),
                    control2: CGPoint(x: 15.06, y: 5.94)
                )
                path.addLine(to: CGPoint(x: 19.36, y: 3.87))
                path.addCurve(
                    to: CGPoint(x: 12, y: 1),
                    control1: CGPoint(x: 17.45, y: 2.09),
                    control2: CGPoint(x: 14.97, y: 1)
                )
                path.addCurve(
                    to: CGPoint(x: 2.18, y: 7.07),
                    control1: CGPoint(x: 7.7, y: 1),
                    control2: CGPoint(x: 3.99, y: 3.47)
                )
                path.addLine(to: CGPoint(x: 5.84, y: 9.91))
                path.addCurve(
                    to: CGPoint(x: 12, y: 5.38),
                    control1: CGPoint(x: 6.71, y: 7.31),
                    control2: CGPoint(x: 9.14, y: 5.38)
                )
                path.closeSubpath()
            }.applying(CGAffineTransform(scaleX: scale, y: scale))
            context.fill(redPath, with: .color(Color(hex: 0xEA4335)))
        }
        .frame(width: size, height: size)
    }
}

/// Official GitHub mark logo
struct GitHubIcon: View {
    var size: CGFloat = 24
    var color: Color = Color(hex: 0x181717)

    var body: some View {
        Canvas { context, canvasSize in
            let scale = canvasSize.width / 24

            let path = Path { path in
                path.move(to: CGPoint(x: 12, y: 0.297))
                path.addCurve(
                    to: CGPoint(x: 0, y: 12.297),
                    control1: CGPoint(x: 5.37, y: 0.297),
                    control2: CGPoint(x: 0, y: 5.67)
                )
                path.addCurve(
                    to: CGPoint(x: 8.205, y: 23.682),
                    control1: CGPoint(x: 0, y: 17.6),
                    control2: CGPoint(x: 3.438, y: 22.097)
                )
                path.addCurve(
                    to: CGPoint(x: 9.025, y: 23.105),
                    control1: CGPoint(x: 8.805, y: 23.795),
                    control2: CGPoint(x: 9.025, y: 23.424)
                )
                path.addCurve(
                    to: CGPoint(x: 9.01, y: 21.065),
                    control1: CGPoint(x: 9.025, y: 22.82),
                    control2: CGPoint(x: 9.015, y: 22.145)
                )
                path.addCurve(
                    to: CGPoint(x: 4.968, y: 19.455),
                    control1: CGPoint(x: 5.672, y: 21.789),
                    control2: CGPoint(x: 4.968, y: 19.455)
                )
                path.addCurve(
                    to: CGPoint(x: 3.633, y: 17.7),
                    control1: CGPoint(x: 4.422, y: 18.07),
                    control2: CGPoint(x: 3.633, y: 17.7)
                )
                path.addCurve(
                    to: CGPoint(x: 3.717, y: 16.971),
                    control1: CGPoint(x: 2.546, y: 16.956),
                    control2: CGPoint(x: 3.717, y: 16.971)
                )
                path.addCurve(
                    to: CGPoint(x: 5.555, y: 18.207),
                    control1: CGPoint(x: 4.922, y: 17.055),
                    control2: CGPoint(x: 5.555, y: 18.207)
                )
                path.addCurve(
                    to: CGPoint(x: 9.05, y: 18.205),
                    control1: CGPoint(x: 6.625, y: 20.042),
                    control2: CGPoint(x: 8.364, y: 19.51)
                )
                path.addCurve(
                    to: CGPoint(x: 9.81, y: 16.6),
                    control1: CGPoint(x: 9.158, y: 17.429),
                    control2: CGPoint(x: 9.467, y: 16.9)
                )
                path.addCurve(
                    to: CGPoint(x: 4.344, y: 10.67),
                    control1: CGPoint(x: 7.145, y: 16.3),
                    control2: CGPoint(x: 4.344, y: 15.268)
                )
                path.addCurve(
                    to: CGPoint(x: 5.579, y: 7.45),
                    control1: CGPoint(x: 4.344, y: 9.36),
                    control2: CGPoint(x: 4.809, y: 8.29)
                )
                path.addCurve(
                    to: CGPoint(x: 5.684, y: 4.274),
                    control1: CGPoint(x: 5.444, y: 7.147),
                    control2: CGPoint(x: 5.039, y: 5.927)
                )
                path.addCurve(
                    to: CGPoint(x: 8.984, y: 5.504),
                    control1: CGPoint(x: 5.684, y: 4.274),
                    control2: CGPoint(x: 6.689, y: 3.952)
                )
                path.addCurve(
                    to: CGPoint(x: 14.984, y: 5.504),
                    control1: CGPoint(x: 9.944, y: 5.237),
                    control2: CGPoint(x: 14.004, y: 5.099)
                )
                path.addCurve(
                    to: CGPoint(x: 18.269, y: 4.274),
                    control1: CGPoint(x: 17.264, y: 3.952),
                    control2: CGPoint(x: 18.269, y: 4.274)
                )
                path.addCurve(
                    to: CGPoint(x: 18.389, y: 7.45),
                    control1: CGPoint(x: 18.914, y: 5.927),
                    control2: CGPoint(x: 18.509, y: 7.147)
                )
                path.addCurve(
                    to: CGPoint(x: 19.619, y: 10.67),
                    control1: CGPoint(x: 19.154, y: 8.29),
                    control2: CGPoint(x: 19.619, y: 9.36)
                )
                path.addCurve(
                    to: CGPoint(x: 14.144, y: 16.59),
                    control1: CGPoint(x: 19.619, y: 15.28),
                    control2: CGPoint(x: 16.814, y: 16.295)
                )
                path.addCurve(
                    to: CGPoint(x: 14.954, y: 18.81),
                    control1: CGPoint(x: 14.564, y: 16.95),
                    control2: CGPoint(x: 14.954, y: 17.686)
                )
                path.addCurve(
                    to: CGPoint(x: 14.939, y: 22.096),
                    control1: CGPoint(x: 14.954, y: 20.416),
                    control2: CGPoint(x: 14.939, y: 21.706)
                )
                path.addCurve(
                    to: CGPoint(x: 15.764, y: 22.666),
                    control1: CGPoint(x: 14.939, y: 22.411),
                    control2: CGPoint(x: 15.149, y: 22.786)
                )
                path.addCurve(
                    to: CGPoint(x: 24, y: 12.297),
                    control1: CGPoint(x: 20.565, y: 22.092),
                    control2: CGPoint(x: 24, y: 17.592)
                )
                path.addCurve(
                    to: CGPoint(x: 12, y: 0.297),
                    control1: CGPoint(x: 24, y: 5.67),
                    control2: CGPoint(x: 18.627, y: 0.297)
                )
                path.closeSubpath()
            }.applying(CGAffineTransform(scaleX: scale, y: scale))

            context.fill(path, with: .color(color))
        }
        .frame(width: size, height: size)
    }
}

// MARK: - Color Extension

extension Color {
    init(hex: UInt, alpha: Double = 1.0) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255,
            opacity: alpha
        )
    }
}

#Preview {
    VStack(spacing: 20) {
        GoogleIcon(size: 48)
        GitHubIcon(size: 48)
        GitHubIcon(size: 48, color: .primary)
    }
    .padding()
}
