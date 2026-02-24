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
