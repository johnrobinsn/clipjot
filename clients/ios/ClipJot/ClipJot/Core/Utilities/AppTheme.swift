import SwiftUI

enum AppTheme {
    /// Primary brand color — adapts to light/dark mode for accessibility.
    /// Light: #0284c7 (sky-600), Dark: #38bdf8 (sky-400)
    static let primary = Color(UIColor { traitCollection in
        traitCollection.userInterfaceStyle == .dark
            ? UIColor(red: 56/255, green: 189/255, blue: 248/255, alpha: 1)
            : UIColor(red: 2/255, green: 132/255, blue: 199/255, alpha: 1)
    })
}

/// Material Design copy icon — matches Android's ic_copy.xml.
/// Viewbox: 0 0 24 24
struct CopyIconShape: Shape {
    func path(in rect: CGRect) -> Path {
        let sx = rect.width / 24.0
        let sy = rect.height / 24.0
        var path = Path()
        // Back page
        path.move(to: CGPoint(x: 16 * sx, y: 1 * sy))
        path.addLine(to: CGPoint(x: 4 * sx, y: 1 * sy))
        path.addCurve(
            to: CGPoint(x: 2 * sx, y: 3 * sy),
            control1: CGPoint(x: 2.9 * sx, y: 1 * sy),
            control2: CGPoint(x: 2 * sx, y: 1.9 * sy)
        )
        path.addLine(to: CGPoint(x: 2 * sx, y: 17 * sy))
        path.addLine(to: CGPoint(x: 4 * sx, y: 17 * sy))
        path.addLine(to: CGPoint(x: 4 * sx, y: 3 * sy))
        path.addLine(to: CGPoint(x: 16 * sx, y: 3 * sy))
        path.closeSubpath()
        // Front page
        path.move(to: CGPoint(x: 19 * sx, y: 5 * sy))
        path.addLine(to: CGPoint(x: 8 * sx, y: 5 * sy))
        path.addCurve(
            to: CGPoint(x: 6 * sx, y: 7 * sy),
            control1: CGPoint(x: 6.9 * sx, y: 5 * sy),
            control2: CGPoint(x: 6 * sx, y: 5.9 * sy)
        )
        path.addLine(to: CGPoint(x: 6 * sx, y: 21 * sy))
        path.addCurve(
            to: CGPoint(x: 8 * sx, y: 23 * sy),
            control1: CGPoint(x: 6 * sx, y: 22.1 * sy),
            control2: CGPoint(x: 6.9 * sx, y: 23 * sy)
        )
        path.addLine(to: CGPoint(x: 19 * sx, y: 23 * sy))
        path.addCurve(
            to: CGPoint(x: 21 * sx, y: 21 * sy),
            control1: CGPoint(x: 20.1 * sx, y: 23 * sy),
            control2: CGPoint(x: 21 * sx, y: 22.1 * sy)
        )
        path.addLine(to: CGPoint(x: 21 * sx, y: 7 * sy))
        path.addCurve(
            to: CGPoint(x: 19 * sx, y: 5 * sy),
            control1: CGPoint(x: 21 * sx, y: 5.9 * sy),
            control2: CGPoint(x: 20.1 * sx, y: 5 * sy)
        )
        path.closeSubpath()
        // Front page cutout (hollow inside)
        path.move(to: CGPoint(x: 19 * sx, y: 21 * sy))
        path.addLine(to: CGPoint(x: 8 * sx, y: 21 * sy))
        path.addLine(to: CGPoint(x: 8 * sx, y: 7 * sy))
        path.addLine(to: CGPoint(x: 19 * sx, y: 7 * sy))
        path.closeSubpath()
        return path
    }
}

/// Material Design edit/pencil icon — matches Android's ic_edit.xml.
/// Viewbox: 0 0 24 24
struct EditPencilShape: Shape {
    func path(in rect: CGRect) -> Path {
        let sx = rect.width / 24.0
        let sy = rect.height / 24.0
        var path = Path()
        // Pencil body + baseline
        path.move(to: CGPoint(x: 3 * sx, y: 17.25 * sy))
        path.addLine(to: CGPoint(x: 3 * sx, y: 21 * sy))
        path.addLine(to: CGPoint(x: 6.75 * sx, y: 21 * sy))
        path.addLine(to: CGPoint(x: 17.81 * sx, y: 9.94 * sy))
        path.addLine(to: CGPoint(x: 14.06 * sx, y: 6.19 * sy))
        path.closeSubpath()
        // Pencil tip
        path.move(to: CGPoint(x: 20.71 * sx, y: 7.04 * sy))
        path.addCurve(
            to: CGPoint(x: 20.71 * sx, y: 5.63 * sy),
            control1: CGPoint(x: 21.1 * sx, y: 6.65 * sy),
            control2: CGPoint(x: 21.1 * sx, y: 6.02 * sy)
        )
        path.addLine(to: CGPoint(x: 18.37 * sx, y: 3.29 * sy))
        path.addCurve(
            to: CGPoint(x: 16.96 * sx, y: 3.29 * sy),
            control1: CGPoint(x: 17.98 * sx, y: 2.9 * sy),
            control2: CGPoint(x: 17.35 * sx, y: 2.9 * sy)
        )
        path.addLine(to: CGPoint(x: 15.13 * sx, y: 5.12 * sy))
        path.addLine(to: CGPoint(x: 18.88 * sx, y: 8.87 * sy))
        path.closeSubpath()
        return path
    }
}

/// Heroicons bookmark (solid) — exact SVG path used across all platforms.
/// Viewbox: 0 0 24 24
struct BookmarkLogoShape: Shape {
    func path(in rect: CGRect) -> Path {
        let sx = rect.width / 24.0
        let sy = rect.height / 24.0

        var path = Path()

        // M6.32 2.577
        path.move(to: CGPoint(x: 6.32 * sx, y: 2.577 * sy))

        // a49.255 49.255 0 0 1 11.36 0 — gentle arc across top
        // Large radius relative to chord ≈ nearly flat curve
        path.addQuadCurve(
            to: CGPoint(x: 17.68 * sx, y: 2.577 * sy),
            control: CGPoint(x: 12.0 * sx, y: 1.93 * sy)
        )

        // c1.497.174 2.57 1.46 2.57 2.93 — top-right corner rounding
        path.addCurve(
            to: CGPoint(x: 20.25 * sx, y: 5.507 * sy),
            control1: CGPoint(x: 19.177 * sx, y: 2.751 * sy),
            control2: CGPoint(x: 20.25 * sx, y: 4.037 * sy)
        )

        // V21 — right edge down
        path.addLine(to: CGPoint(x: 20.25 * sx, y: 21.0 * sy))

        // a.75.75 0 0 1-1.085.67 — small arc at bottom-right
        path.addQuadCurve(
            to: CGPoint(x: 19.165 * sx, y: 21.67 * sy),
            control: CGPoint(x: 20.25 * sx, y: 21.56 * sy)
        )

        // L12 18.089 — right side of V-notch
        path.addLine(to: CGPoint(x: 12.0 * sx, y: 18.089 * sy))

        // l-7.165 3.583 — left side of V-notch
        path.addLine(to: CGPoint(x: 4.835 * sx, y: 21.672 * sy))

        // A.75.75 0 0 1 3.75 21 — small arc at bottom-left
        path.addQuadCurve(
            to: CGPoint(x: 3.75 * sx, y: 21.0 * sy),
            control: CGPoint(x: 3.75 * sx, y: 21.56 * sy)
        )

        // V5.507 — left edge up
        path.addLine(to: CGPoint(x: 3.75 * sx, y: 5.507 * sy))

        // c0-1.47 1.073-2.756 2.57-2.93 — top-left corner rounding
        path.addCurve(
            to: CGPoint(x: 6.32 * sx, y: 2.577 * sy),
            control1: CGPoint(x: 3.75 * sx, y: 4.037 * sy),
            control2: CGPoint(x: 4.823 * sx, y: 2.751 * sy)
        )

        path.closeSubpath()
        return path
    }
}
