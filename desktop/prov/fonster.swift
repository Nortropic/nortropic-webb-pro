// desktop/prov/fonster.swift (swiftc -O desktop/prov/fonster.swift -o desktop/prov/fonster): listar fönster för ett program (CGWindowListCopyWindowInfo): nummer, pid, lager, rubrik, ram. Används för screencapture -l.
import CoreGraphics
import Foundation
// fonster <ägarnamn> eller fonster --pid <pid> (en dialog kan ha ett annat ägarnamn än appen)
let args = CommandLine.arguments
let pidFilter: Int? = args.count > 2 && args[1] == "--pid" ? Int(args[2]) : nil
let agare = pidFilter == nil && args.count > 1 ? args[1] : "Nortropic"
let lista = CGWindowListCopyWindowInfo([.optionAll], kCGNullWindowID) as? [[String: Any]] ?? []
for w in lista {
  let o = w[kCGWindowOwnerName as String] as? String ?? ""
  if let p = pidFilter { if (w[kCGWindowOwnerPID as String] as? Int ?? -1) != p { continue } } else if o != agare { continue }
  let n = w[kCGWindowNumber as String] as? Int ?? -1
  let pid = w[kCGWindowOwnerPID as String] as? Int ?? -1
  let lager = w[kCGWindowLayer as String] as? Int ?? -1
  let namn = w[kCGWindowName as String] as? String ?? ""
  let pa = w[kCGWindowIsOnscreen as String] as? Bool ?? false
  let b = w[kCGWindowBounds as String] as? [String: Any] ?? [:]
  print("\(n)\t\(pid)\t\(lager)\t\(pa ? "synlig" : "dold")\t\(namn)\t\(b["X"] ?? 0),\(b["Y"] ?? 0) \(b["Width"] ?? 0)x\(b["Height"] ?? 0)")
}
