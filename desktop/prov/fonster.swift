// desktop/prov/fonster.swift (swiftc -O desktop/prov/fonster.swift -o desktop/prov/fonster): listar fönster för ett program (CGWindowListCopyWindowInfo): nummer, pid, lager, rubrik, ram. Används för screencapture -l.
import CoreGraphics
import Foundation
let agare = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "Nortropic"
let lista = CGWindowListCopyWindowInfo([.optionAll], kCGNullWindowID) as? [[String: Any]] ?? []
for w in lista {
  guard let o = w[kCGWindowOwnerName as String] as? String, o == agare else { continue }
  let n = w[kCGWindowNumber as String] as? Int ?? -1
  let pid = w[kCGWindowOwnerPID as String] as? Int ?? -1
  let lager = w[kCGWindowLayer as String] as? Int ?? -1
  let namn = w[kCGWindowName as String] as? String ?? ""
  let pa = w[kCGWindowIsOnscreen as String] as? Bool ?? false
  let b = w[kCGWindowBounds as String] as? [String: Any] ?? [:]
  print("\(n)\t\(pid)\t\(lager)\t\(pa ? "synlig" : "dold")\t\(namn)\t\(b["X"] ?? 0),\(b["Y"] ?? 0) \(b["Width"] ?? 0)x\(b["Height"] ?? 0)")
}
