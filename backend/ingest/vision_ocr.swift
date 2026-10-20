import AppKit
import Foundation
import Vision

// Reads image paths from stdin (one per line) and prints one JSON object per image:
// {"path": ..., "tokens": [{"text", "confidence", "x", "y"}]} or {"path": ..., "error": ...}.
// x and y are the centre of the text box as fractions of the image size, origin top-left.

struct Token: Codable {
    let text: String
    let confidence: Float
    let x: Double
    let y: Double
}

struct Output: Codable {
    let path: String
    let tokens: [Token]?
    let error: String?
}

let encoder = JSONEncoder()

func emit(_ output: Output) {
    guard let data = try? encoder.encode(output), let line = String(data: data, encoding: .utf8) else {
        return
    }
    print(line)
    fflush(stdout)
}

func recognise(path: String) -> Output {
    guard let image = NSImage(contentsOfFile: path),
        let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil)
    else {
        return Output(path: path, tokens: nil, error: "cannot load image")
    }
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    do {
        try VNImageRequestHandler(cgImage: cgImage).perform([request])
    } catch {
        return Output(path: path, tokens: nil, error: "\(error)")
    }
    let tokens = (request.results ?? []).compactMap { observation -> Token? in
        guard let candidate = observation.topCandidates(1).first else { return nil }
        let box = observation.boundingBox
        return Token(
            text: candidate.string,
            confidence: candidate.confidence,
            x: Double(box.midX),
            y: 1.0 - Double(box.midY))
    }
    return Output(path: path, tokens: tokens, error: nil)
}

while let line = readLine() {
    let path = line.trimmingCharacters(in: .whitespacesAndNewlines)
    if path.isEmpty { continue }
    emit(recognise(path: path))
}
