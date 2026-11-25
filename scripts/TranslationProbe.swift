import Foundation
import Translation

@main
struct TranslationProbe {
  static func main() async {
    let availability = LanguageAvailability()
    let source = Locale.Language(identifier: "en")
    let target = Locale.Language(identifier: "ar")
    let supported = await availability.supportedLanguages
    print("supported", supported.count)
    print("contains", supported.contains { $0.languageCode?.identifier == "ar" })
    print("status", await availability.status(from: source, to: target))
    let session = TranslationSession(installedSource: source, target: target)
    print("ready", await session.isReady)
    do {
      let result = try await session.translate("The doctor advised me to rest for a few days.")
      print("result", result.targetText)
    } catch {
      print("error", error.localizedDescription)
    }
  }
}
