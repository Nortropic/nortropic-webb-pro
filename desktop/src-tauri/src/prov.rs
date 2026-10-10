//! Provinstrumenteringen: finns bara när appen byggs med `--features prov` (kunskap/desktop.md, Prov). Användarbygget
//! saknar modulen helt; prov_desktop prövar det negativt (ingen provsträng i binären, ingen provport).
//!
//! Provstyrningen (nwp-provstyrning) lyssnar på 127.0.0.1 på en slumpad port med en slumpad token i provets datakatalog
//! (0600). Den kör JavaScript i huvudfönstrets riktiga WKWebView, navigerar, väljer i menyn, flyttar fönstret och ger
//! fönstrets nummer för screencapture -l. Den finns för att prova den riktiga appen, aldrig i en användarbyggd app.

use crate::{huvudfonster, lage, menyval};
use std::io::{BufRead, BufReader, Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::atomic::Ordering;
use std::sync::mpsc;
use std::time::Duration;
use tauri::{AppHandle, Url};

pub const MARKE: &str = "nwp-provstyrning";

pub fn upplasning_attrapp() -> bool {
    std::env::var("NWP_DESKTOP_PROV_UPPLAS").as_deref() == Ok("1")
}

pub fn datakatalog() -> Option<std::path::PathBuf> {
    std::env::var_os("NWP_DESKTOP_DATA").map(std::path::PathBuf::from)
}

pub fn starta(app: AppHandle) {
    let lyss = match TcpListener::bind("127.0.0.1:0") {
        Ok(l) => l,
        Err(e) => {
            eprintln!("{MARKE}: ingen port: {e}");
            return;
        }
    };
    let port = lyss.local_addr().map(|a| a.port()).unwrap_or(0);
    let mut t = [0u8; 24];
    getrandom::getrandom(&mut t).expect("slumptal");
    let token = hex::encode(t);
    let data = lage(&app).data.clone();
    let _ = crate::installningar::skriv_privat(&data.join("provstyrning.json"), serde_json::json!({ "marke": MARKE, "port": port, "token": token, "pid": std::process::id() }).to_string().as_bytes());
    std::thread::spawn(move || {
        for s in lyss.incoming().flatten() {
            let app = app.clone();
            let token = token.clone();
            std::thread::spawn(move || {
                let _ = hantera(&app, s, &token);
            });
        }
    });
}

fn hantera(app: &AppHandle, mut s: TcpStream, token: &str) -> std::io::Result<()> {
    s.set_read_timeout(Some(Duration::from_secs(30)))?;
    let mut r = BufReader::new(s.try_clone()?);
    let mut rad = String::new();
    r.read_line(&mut rad)?;
    let mut delar = rad.split_whitespace();
    let metod = delar.next().unwrap_or("").to_string();
    let vag = delar.next().unwrap_or("").to_string();
    let mut langd = 0usize;
    let mut tok = String::new();
    loop {
        let mut h = String::new();
        r.read_line(&mut h)?;
        let h = h.trim_end();
        if h.is_empty() {
            break;
        }
        if let Some((k, v)) = h.split_once(':') {
            match k.trim().to_ascii_lowercase().as_str() {
                "content-length" => langd = v.trim().parse().unwrap_or(0),
                "x-prov-token" => tok = v.trim().to_string(),
                _ => {}
            }
        }
    }
    let mut kropp = vec![0u8; langd.min(1 << 20)];
    r.read_exact(&mut kropp)?;
    let kropp = String::from_utf8_lossy(&kropp).to_string();
    let (kod, svar) = if tok != token { (403, serde_json::json!({ "fel": "fel token" })) } else { utfor(app, &metod, &vag, &kropp) };
    let b = svar.to_string();
    write!(s, "HTTP/1.1 {kod} OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{b}", b.len())?;
    Ok(())
}

fn utfor(app: &AppHandle, metod: &str, vag: &str, kropp: &str) -> (u16, serde_json::Value) {
    let Some(w) = huvudfonster(app) else { return (500, serde_json::json!({ "fel": "inget huvudfönster" })) };
    match (metod, vag) {
        ("POST", "/eval") => {
            let (tx, rx) = mpsc::channel();
            if let Err(e) = w.eval_with_callback(kropp.to_string(), move |v| {
                let _ = tx.send(v);
            }) {
                return (500, serde_json::json!({ "fel": e.to_string() }));
            }
            match rx.recv_timeout(Duration::from_secs(15)) {
                Ok(v) => (200, serde_json::json!({ "varde": serde_json::from_str::<serde_json::Value>(&v).unwrap_or(serde_json::Value::String(v)) })),
                Err(_) => (504, serde_json::json!({ "fel": "inget svar från webvyn" })),
            }
        }
        ("POST", "/navigera") => match Url::parse(kropp.trim()) {
            Ok(u) => (200, serde_json::json!({ "ok": w.navigate(u).is_ok() })),
            Err(e) => (400, serde_json::json!({ "fel": e.to_string() })),
        },
        ("POST", "/meny") => {
            let id = kropp.trim().to_string();
            let a = app.clone();
            let _ = app.run_on_main_thread(move || menyval(&a, &id));
            (200, serde_json::json!({ "ok": true }))
        }
        ("POST", "/redigera") => {
            // Redigera-menyns åtgärd (copy:, paste:, cut:, selectAll:) skickad som menyn skickar den, genom svarskedjan till
            // den webvy som har fokus; provet styr inget tangentbord (det kräver tillgänglighetsbehörighet)
            let atgard = match kropp.trim() { "kopiera" => "copy:", "klistra" => "paste:", "klipp" => "cut:", "markera" => "selectAll:", _ => "" };
            if atgard.is_empty() {
                return (400, serde_json::json!({ "fel": "kopiera, klistra, klipp eller markera" }));
            }
            let (tx, rx) = std::sync::mpsc::channel();
            let _ = app.run_on_main_thread(move || unsafe {
                use objc2::runtime::{AnyClass, AnyObject, Sel};
                let nsapp: *mut AnyObject = objc2::msg_send![AnyClass::get(c"NSApplication").expect("NSApplication"), sharedApplication];
                let sel = Sel::register(&std::ffi::CString::new(atgard).unwrap());
                let ingen: *mut AnyObject = std::ptr::null_mut();
                let ok: bool = objc2::msg_send![nsapp, sendAction: sel, to: ingen, from: ingen];
                let _ = tx.send(ok);
            });
            match rx.recv_timeout(Duration::from_secs(5)) {
                Ok(ok) => (200, serde_json::json!({ "skickad": ok })),
                Err(_) => (504, serde_json::json!({ "fel": "huvudtråden svarade inte" })),
            }
        }
        ("POST", "/stang") => {
            // som röda knappen: CloseRequested går genom appens egen hantering
            let _ = w.close();
            (200, serde_json::json!({ "ok": true }))
        }
        ("POST", "/visa") => {
            crate::visa(app);
            (200, serde_json::json!({ "ok": true }))
        }
        ("POST", "/fonster") => {
            let j: serde_json::Value = serde_json::from_str(kropp).unwrap_or_default();
            let g = |k: &str| j.get(k).and_then(|v| v.as_f64());
            if let (Some(x), Some(y)) = (g("x"), g("y")) {
                let _ = w.set_position(tauri::LogicalPosition::new(x, y));
            }
            if let (Some(b), Some(h)) = (g("bredd"), g("hojd")) {
                let _ = w.set_size(tauri::LogicalSize::new(b, h));
            }
            if let Some(h) = j.get("helskarm").and_then(|v| v.as_bool()) {
                let _ = w.set_fullscreen(h);  // samma som menyns Helskärm (NSWindow toggleFullScreen)
            }
            (200, serde_json::json!({ "ok": true }))
        }
        ("GET", "/lage") => {
            let l = lage(app);
            let s = w.scale_factor().unwrap_or(1.0);
            let storlek = w.inner_size().map(|p| p.to_logical::<f64>(s)).ok();
            let pos = w.outer_position().map(|p| p.to_logical::<f64>(s)).ok();
            let nummer: isize = w.ns_window().map(|p| unsafe { objc2::msg_send![p as *mut objc2::runtime::AnyObject, windowNumber] }).unwrap_or(-1);
            (200, serde_json::json!({
                "upplast": l.upplast.load(Ordering::SeqCst),
                "motorport": l.motorport.load(Ordering::SeqCst),
                "url": w.url().map(|u| u.to_string()).ok(),
                "synlig": w.is_visible().unwrap_or(false),
                "fokus": w.is_focused().unwrap_or(false),
                "helskarm": w.is_fullscreen().unwrap_or(false),
                "skala": s,
                "storlek": storlek.map(|z| [z.width, z.height]),
                "position": pos.map(|p| [p.x, p.y]),
                "fonsternummer": nummer,
                "pid": std::process::id(),
                "skarmar": app.available_monitors().map(|ms| ms.iter().map(|m| serde_json::json!({ "namn": m.name(), "skala": m.scale_factor(), "storlek": [m.size().width, m.size().height], "position": [m.position().x, m.position().y] })).collect::<Vec<_>>()).unwrap_or_default(),
            }))
        }
        _ => (404, serde_json::json!({ "fel": "okänd provväg" })),
    }
}
