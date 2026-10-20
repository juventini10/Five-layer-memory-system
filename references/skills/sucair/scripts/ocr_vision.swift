import Foundation
import Vision
import AppKit

// 批量中文 OCR：macOS Vision（本机跑，不外发）
// 用法: ocr_vision <img1> [img2 ...]
// 输出: 每张图先打印 ###PAGE <文件名>，然后按视觉阅读顺序输出文本行

func ocr(_ path: String) -> String {
    let absPath = path.hasPrefix("/") ? path : (FileManager.default.currentDirectoryPath + "/" + path)
    let url = URL(fileURLWithPath: absPath)
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    if #available(macOS 13.0, *) {
        request.revision = VNRecognizeTextRequestRevision3
    }
    let handler = VNImageRequestHandler(url: url)
    do {
        try handler.perform([request])
    } catch {
        FileHandle.standardError.write("ERR \(path): \(error)\n".data(using: .utf8)!)
        return ""
    }
    guard let results = request.results else { return "" }

    // 按 y 降序（从上到下）、x 升序（从左到右）排序
    let sorted = results.sorted { a, b in
        let ay = a.boundingBox.midY, by = b.boundingBox.midY
        let h = a.boundingBox.height
        // 同一行判定：中线差值小于行高一半
        if abs(ay - by) < h * 0.5 {
            return a.boundingBox.minX < b.boundingBox.minX
        }
        return ay > by
    }

    var lines: [String] = []
    var currentLine: [String] = []
    var lastY: CGFloat = -1
    var lastH: CGFloat = 0
    for obs in sorted {
        guard let cand = obs.topCandidates(1).first else { continue }
        let bb = obs.boundingBox
        let y = bb.midY
        let h = bb.height
        if lastY < 0 {
            currentLine = [cand.string]
        } else if abs(y - lastY) < max(h, lastH) * 0.5 {
            currentLine.append(cand.string)
        } else {
            lines.append(currentLine.joined())
            currentLine = [cand.string]
        }
        lastY = y
        lastH = h
    }
    if !currentLine.isEmpty { lines.append(currentLine.joined()) }
    return lines.joined(separator: "\n")
}

let args = Array(CommandLine.arguments.dropFirst())
for p in args {
    print("###PAGE \(p)")
    print(ocr(p))
    print("###END")
}
