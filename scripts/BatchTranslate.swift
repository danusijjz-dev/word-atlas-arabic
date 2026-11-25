import Foundation
import Translation

@main
struct BatchTranslate {
  static func main() async {
    guard CommandLine.arguments.count >= 3 else {
      fputs("usage: BatchTranslate input.json output.json [global-start] [count]\n", stderr)
      exit(2)
    }
    let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
    let outputURL = URL(fileURLWithPath: CommandLine.arguments[2])
    do {
      let data = try Data(contentsOf: inputURL)
      let allRequests = try JSONDecoder().decode([String].self, from: data)
      let globalStart = CommandLine.arguments.count > 3 ? Int(CommandLine.arguments[3]) ?? 0 : 0
      let requestedCount = CommandLine.arguments.count > 4 ? Int(CommandLine.arguments[4]) ?? (allRequests.count - globalStart) : (allRequests.count - globalStart)
      let endRequest = min(allRequests.count, globalStart + requestedCount)
      let requests = Array(allRequests[globalStart..<endRequest])
      let source = Locale.Language(identifier: "en")
      let target = Locale.Language(identifier: "ar")
      var session = TranslationSession(installedSource: source, target: target)
      guard await session.isReady else {
        throw NSError(domain: "BatchTranslate", code: 1, userInfo: [NSLocalizedDescriptionKey: "Arabic translation model is not installed"])
      }

      var result: [String] = []
      if FileManager.default.fileExists(atPath: outputURL.path),
         let prior = try? JSONDecoder().decode([String].self, from: Data(contentsOf: outputURL)),
         prior.count <= requests.count {
        result = prior
      }
      result.reserveCapacity(requests.count)
      let chunkSize = 80
      var nextStart = result.count
      while nextStart < requests.count {
        let start = nextStart
        let end = min(start + chunkSize, requests.count)
        let batch = requests[start..<end].enumerated().map { offset, text in
          TranslationSession.Request(
            sourceText: text,
            clientIdentifier: String(globalStart + start + offset)
          )
        }
        var translated: [TranslationSession.Response]
        do {
          translated = try await session.translations(from: batch)
        } catch {
          fputs("batch failed at \(globalStart + start); retrying with a new session\n", stderr)
          session = TranslationSession(installedSource: source, target: target)
          do {
            translated = try await session.translations(from: batch)
          } catch {
            translated = []
            for request in batch {
              do {
                let one = try await session.translate(request.sourceText)
                translated.append(TranslationSession.Response(
                  sourceLanguage: one.sourceLanguage,
                  targetLanguage: one.targetLanguage,
                  sourceText: one.sourceText,
                  targetText: one.targetText,
                  clientIdentifier: request.clientIdentifier
                ))
              } catch {
                throw NSError(
                  domain: "BatchTranslate",
                  code: 3,
                  userInfo: [NSLocalizedDescriptionKey: "Unable to translate \(request.clientIdentifier ?? "?"): \(error.localizedDescription)"]
                )
              }
            }
          }
        }
        var ordered = Dictionary(uniqueKeysWithValues: translated.map {
          (Int($0.clientIdentifier ?? "-1") ?? -1, $0.targetText)
        })
        for index in start..<end {
          let globalIndex = globalStart + index
          guard let text = ordered.removeValue(forKey: globalIndex) else {
            throw NSError(domain: "BatchTranslate", code: 2, userInfo: [NSLocalizedDescriptionKey: "Missing translation at index \(index)"])
          }
          result.append(text)
        }
        let output = try JSONSerialization.data(withJSONObject: result, options: [])
        try output.write(to: outputURL, options: .atomic)
        fputs("translated \(globalStart + end)/\(allRequests.count)\n", stderr)
        fflush(stderr)
        nextStart = end
      }
      print("Translated \(result.count) items")
    } catch {
      fputs("error: \(error.localizedDescription)\n", stderr)
      exit(1)
    }
  }
}
