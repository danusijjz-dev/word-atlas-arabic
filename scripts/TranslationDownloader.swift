import SwiftUI
import Translation
import _Translation_SwiftUI
import AppKit

@main
struct TranslationDownloaderApp: App {
  var body: some Scene {
    WindowGroup {
      DownloadView()
        .frame(width: 520, height: 260)
    }
  }
}

struct DownloadView: View {
  var body: some View {
    VStack(spacing: 18) {
      Text("Word Atlas")
        .font(.largeTitle.bold())
      Text("正在准备英语 → 阿拉伯语翻译模型…")
        .multilineTextAlignment(.center)
      ProgressView()
    }
    .padding(30)
    .translationTask(
      source: Locale.Language(identifier: "en"),
      target: Locale.Language(identifier: "ar")
    ) { session in
      do {
        try await session.prepareTranslation()
        let result = try await session.translate("Hello. The doctor advised me to rest for a few days.")
        print("TRANSLATION_OK", result.targetText)
        fflush(stdout)
        await MainActor.run { NSApp.terminate(nil) }
      } catch {
        print("TRANSLATION_ERROR", error.localizedDescription)
        fflush(stdout)
        await MainActor.run { NSApp.terminate(nil) }
      }
    }
  }
}
