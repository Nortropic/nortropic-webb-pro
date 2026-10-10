//! En liten HTTP/1.1-klient som bara når 127.0.0.1. Adressen är inbyggd: ingen sökväg, port eller URL från renderern,
//! kundmaterial eller en djuplänk kan få appen att skicka något någon annanstans (kunskap/desktop.md, Motorn).

use std::io::{Read, Write};
use std::net::{Ipv4Addr, SocketAddr, TcpStream};
use std::time::Duration;

pub struct Svar {
    pub status: u16,
    pub huvuden: Vec<(String, String)>,
    pub kropp: Vec<u8>,
}

impl Svar {
    pub fn json(&self) -> Result<serde_json::Value, String> {
        serde_json::from_slice(&self.kropp).map_err(|e| format!("svaret var inte JSON: {e}"))
    }
}

const TAK: usize = 4 * 1024 * 1024;

/// Ett anrop till motorn på loopback. `huvuden` är appens egna (aldrig renderarens).
pub fn anrop(port: u16, metod: &str, vag: &str, huvuden: &[(&str, &str)], kropp: Option<&[u8]>, frist: Duration) -> Result<Svar, String> {
    anrop_med_tak(port, metod, vag, huvuden, kropp, frist, TAK)
}

pub fn anrop_med_tak(port: u16, metod: &str, vag: &str, huvuden: &[(&str, &str)], kropp: Option<&[u8]>, frist: Duration, tak: usize) -> Result<Svar, String> {
    if !vag.starts_with('/') || vag.contains(['\r', '\n', ' ']) {
        return Err("ogiltig väg".into());
    }
    let adr = SocketAddr::from((Ipv4Addr::LOCALHOST, port));
    let mut s = TcpStream::connect_timeout(&adr, Duration::from_millis(1500)).map_err(|e| format!("ingen tjänst på 127.0.0.1:{port}: {e}"))?;
    s.set_read_timeout(Some(frist)).ok();
    s.set_write_timeout(Some(frist)).ok();
    let mut req = format!("{metod} {vag} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nConnection: close\r\nUser-Agent: Nortropic-desktop/{}\r\n", env!("CARGO_PKG_VERSION"));
    for (k, v) in huvuden {
        if k.contains(['\r', '\n', ':']) || v.contains(['\r', '\n']) {
            return Err("ogiltigt huvud".into());
        }
        req.push_str(&format!("{k}: {v}\r\n"));
    }
    if let Some(b) = kropp {
        req.push_str(&format!("Content-Type: application/json\r\nContent-Length: {}\r\n", b.len()));
    }
    req.push_str("\r\n");
    s.write_all(req.as_bytes()).map_err(|e| e.to_string())?;
    if let Some(b) = kropp {
        s.write_all(b).map_err(|e| e.to_string())?;
    }
    let mut buf = Vec::new();
    let mut chunk = [0u8; 16384];
    loop {
        match s.read(&mut chunk) {
            Ok(0) => break,
            Ok(n) => {
                buf.extend_from_slice(&chunk[..n]);
                if buf.len() > tak {
                    return Err("svaret är för stort".into());
                }
            }
            Err(e) if buf.is_empty() => return Err(format!("inget svar: {e}")),
            Err(_) => break,
        }
    }
    tolka(&buf)
}

fn tolka(buf: &[u8]) -> Result<Svar, String> {
    let slut = buf.windows(4).position(|w| w == b"\r\n\r\n").ok_or("ofullständigt svar")?;
    let huvud = String::from_utf8_lossy(&buf[..slut]);
    let mut rader = huvud.split("\r\n");
    let statusrad = rader.next().unwrap_or("");
    let status = statusrad.split_whitespace().nth(1).and_then(|s| s.parse().ok()).ok_or("ingen statusrad")?;
    let huvuden: Vec<(String, String)> = rader
        .filter_map(|r| r.split_once(':').map(|(k, v)| (k.trim().to_ascii_lowercase(), v.trim().to_string())))
        .collect();
    let mut kropp = buf[slut + 4..].to_vec();
    if huvuden.iter().any(|(k, v)| k == "transfer-encoding" && v.eq_ignore_ascii_case("chunked")) {
        kropp = avchunka(&kropp)?;
    }
    Ok(Svar { status, huvuden, kropp })
}

fn avchunka(mut b: &[u8]) -> Result<Vec<u8>, String> {
    let mut ut = Vec::new();
    loop {
        let rad = b.windows(2).position(|w| w == b"\r\n").ok_or("trasig chunk")?;
        let n = usize::from_str_radix(String::from_utf8_lossy(&b[..rad]).split(';').next().unwrap_or("").trim(), 16).map_err(|_| "trasig chunkstorlek")?;
        b = &b[rad + 2..];
        if n == 0 {
            return Ok(ut);
        }
        if b.len() < n + 2 {
            return Err("trasig chunk".into());
        }
        ut.extend_from_slice(&b[..n]);
        b = &b[n + 2..];
    }
}
