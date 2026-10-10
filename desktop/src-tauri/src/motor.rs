//! Motorn: registreringen, identitetsprovet och starten. En enda kodväg ansvarar för start och versionskontroll
//! (kunskap/desktop.md, Motorn och identiteten).
//!
//! Identiteten prövas innan något känsligt skickas: motorn bevisar att den har dashboardnyckeln genom HMAC-SHA256 över
//! appens utmaning, sin instans, rot, pid, port och commit (RFC 2104; ingen egen kryptografi). Appen skickar nyckeln
//! först när beviset stämmer, porten ägs av samma pid, processen kör ur den registrerade roten under samma användare och
//! kontraktet är `desktop/1`. Ett HTTP 200 på porten eller ett processnamn räcker aldrig.

use crate::http;
use crate::installningar::{Installningar, Verktyg};
use hmac::{Hmac, Mac};
use serde::Serialize;
use sha2::Sha256;
use std::fs;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;

pub const KONTRAKT: &str = "desktop/1";
const LSOF: &str = "/usr/sbin/lsof";
const GIT: &str = "/usr/bin/git";

#[derive(Clone, Debug, Serialize)]
pub struct Identitet {
    pub instans: String,
    pub rot: String,
    pub pid: u32,
    pub port: u16,
    pub commit: String,
    pub commit_pa_disk: String,
    pub ui: String,
    pub startad: String,
    pub utdaterad: bool,
    pub kontrakt: String,
}

#[derive(Clone, Debug, Serialize)]
#[serde(tag = "lage", rename_all = "snake_case")]
pub enum Status {
    /// Ingen motor registrerad (första starten).
    EjRegistrerad,
    /// Den registrerade roten finns inte längre eller är inte en nortropic-webb-pro-utcheckning.
    RotSaknas { orsak: String },
    /// Inget lyssnar på porten.
    Stoppad,
    /// Något lyssnar men är inte den registrerade motorn; appen skickar inget dit och stoppar det inte.
    FelInstans { orsak: String, pid: Option<u32> },
    /// Rätt motor men ett kontrakt appen inte stöder.
    Inkompatibel { orsak: String },
    /// Rätt motor, identiteten bevisad.
    Verifierad { identitet: Identitet },
}

/// Kör ett verktyg med absolut sökväg och en tidsgräns; ett verktyg som hänger dödas och ger None.
fn kor(program: &str, args: &[&str], sekunder: u64) -> Option<std::process::Output> {
    use std::process::Stdio;
    let mut c = Command::new(program).args(args).stdin(Stdio::null()).stdout(Stdio::piped()).stderr(Stdio::null()).spawn().ok()?;
    let slut = std::time::Instant::now() + Duration::from_secs(sekunder);
    loop {
        match c.try_wait() {
            Ok(Some(_)) => return c.wait_with_output().ok(),
            Ok(None) if std::time::Instant::now() < slut => std::thread::sleep(Duration::from_millis(20)),
            _ => {
                let _ = c.kill();
                let _ = c.wait();
                return None;
            }
        }
    }
}

pub fn hem() -> PathBuf {
    PathBuf::from(std::env::var_os("HOME").unwrap_or_default())
}

/// Huvudutcheckningen som server.py och dashboard.sh känner igen (deras nyckelfil skiljer sig från en worktrees).
pub fn huvudrot() -> Option<PathBuf> {
    fs::canonicalize(hem().join("nortropic-repos/nortropic-webb-pro")).ok()
}

pub fn nyckelfil(rot: &Path) -> PathBuf {
    if huvudrot().as_deref() == Some(rot) {
        hem().join(".nortropic-hemligheter/webb-pro/dashboard-nyckel")
    } else {
        rot.join("kunder/.dashboard-nyckel")
    }
}

/// Nyckeln läses bara när filen ägs av den här användaren och ingen annan kan läsa den (samma krav som granskarnyckeln).
pub fn las_nyckel(rot: &Path) -> Result<String, String> {
    let f = nyckelfil(rot);
    let m = fs::metadata(&f).map_err(|_| format!("motorns nyckelfil saknas ({})", f.display()))?;
    if m.uid() != unsafe { libc::getuid() } || m.mode() & 0o077 != 0 {
        return Err(format!("motorns nyckelfil gäller inte: andra än du kan läsa den eller den ägs av en annan användare ({})", f.display()));
    }
    let n = fs::read_to_string(&f).map_err(|e| e.to_string())?.trim().to_string();
    if n.len() < 16 {
        return Err("motorns nyckelfil är tom eller kort".into());
    }
    Ok(n)
}

pub fn validera_rot(rot: &Path) -> Result<PathBuf, String> {
    let r = fs::canonicalize(rot).map_err(|_| format!("{} finns inte", rot.display()))?;
    for del in ["dashboard/server.py", "dashboard.sh", "kontroller/meddelanden.py", ".venv/bin/python"] {
        if !r.join(del).exists() {
            return Err(format!("{} saknar {del}: inte en körbar nortropic-webb-pro-utcheckning", r.display()));
        }
    }
    let rs = r.display().to_string();
    let ut = kor(GIT, &["-C", &rs, "config", "--get", "remote.origin.url"], 5).ok_or("git svarade inte")?;
    let url = String::from_utf8_lossy(&ut.stdout).to_lowercase();
    if !url.contains("nortropic/nortropic-webb-pro") {
        return Err(format!("{} har inte Nortropic/nortropic-webb-pro som origin", r.display()));
    }
    Ok(r)
}

/// Verktygen hittas med absoluta sökvägar på kända platser, aldrig genom ett inloggningsskal eller en profil.
pub fn hitta_verktyg() -> Verktyg {
    let h = hem();
    let kataloger: Vec<PathBuf> = vec![
        "/opt/homebrew/bin".into(),
        "/usr/local/bin".into(),
        h.join(".local/bin"),
        h.join(".claude/local"),
        "/opt/homebrew/opt/node@24/bin".into(),
        "/opt/homebrew/opt/node@22/bin".into(),
    ];
    let hitta = |namn: &str| -> Option<PathBuf> {
        kataloger.iter().map(|k| k.join(namn)).find(|p| fs::metadata(p).map(|m| m.is_file() || m.file_type().is_symlink()).unwrap_or(false) && ar_korbar(p))
    };
    Verktyg { claude: hitta("claude"), node: hitta("node") }
}

fn ar_korbar(p: &Path) -> bool {
    fs::metadata(p).map(|m| m.mode() & 0o111 != 0).unwrap_or(false)
}

fn slump_hex(n: usize) -> String {
    let mut b = vec![0u8; n];
    getrandom::getrandom(&mut b).expect("slumptal");
    hex::encode(b)
}

/// Pid för den process som lyssnar på 127.0.0.1:port, ur lsof (absolut sökväg).
pub fn lyssnande_pid(port: u16) -> Option<u32> {
    let ut = kor(LSOF, &["-nP", &format!("-iTCP@127.0.0.1:{port}"), "-sTCP:LISTEN", "-t"], 5)?;
    String::from_utf8_lossy(&ut.stdout).lines().next().and_then(|l| l.trim().parse().ok())
}

fn process_cwd(pid: u32) -> Option<PathBuf> {
    let ut = kor(LSOF, &["-a", "-p", &pid.to_string(), "-d", "cwd", "-Fn"], 5)?;
    String::from_utf8_lossy(&ut.stdout).lines().find_map(|l| l.strip_prefix('n').map(PathBuf::from)).and_then(|p| fs::canonicalize(p).ok())
}

fn process_uid(pid: u32) -> Option<u32> {
    let ut = kor("/bin/ps", &["-o", "uid=", "-p", &pid.to_string()], 5)?;
    String::from_utf8_lossy(&ut.stdout).trim().parse().ok()
}

pub fn status(inst: &Installningar) -> Status {
    let Some(rot) = inst.rot.as_ref() else { return Status::EjRegistrerad };
    let rot = match validera_rot(rot) {
        Ok(r) => r,
        Err(e) => return Status::RotSaknas { orsak: e },
    };
    let Some(pid) = lyssnande_pid(inst.port) else { return Status::Stoppad };
    if process_uid(pid) != Some(unsafe { libc::getuid() }) {
        return Status::FelInstans { orsak: format!("porten {} hålls av en annan användares process", inst.port), pid: Some(pid) };
    }
    match process_cwd(pid) {
        Some(c) if c == rot => {}
        Some(c) => return Status::FelInstans { orsak: format!("porten {} hålls av en process ur {}, inte den registrerade motorn", inst.port, c.display()), pid: Some(pid) },
        None => return Status::FelInstans { orsak: "processens arbetskatalog gick inte att läsa".into(), pid: Some(pid) },
    }
    let nyckel = match las_nyckel(&rot) {
        Ok(n) => n,
        Err(e) => return Status::FelInstans { orsak: e, pid: Some(pid) },
    };
    let utmaning = slump_hex(32);
    let svar = match http::anrop(inst.port, "GET", &format!("/api/desktop/identitet?utmaning={utmaning}"), &[], None, Duration::from_secs(5)) {
        Ok(s) => s,
        Err(e) => return Status::FelInstans { orsak: e, pid: Some(pid) },
    };
    if svar.status == 404 {
        return Status::Inkompatibel { orsak: "motorn saknar desktopkontraktet (desktop/1): den kör en äldre version; starta om den när inget arbete pågår".into() };
    }
    let j = match svar.json() {
        Ok(j) if svar.status == 200 => j,
        Ok(j) => return Status::FelInstans { orsak: format!("identiteten svarade {}: {}", svar.status, j.get("fel").and_then(|v| v.as_str()).unwrap_or("")), pid: Some(pid) },
        Err(e) => return Status::FelInstans { orsak: e, pid: Some(pid) },
    };
    let s = |k: &str| j.get(k).and_then(|v| v.as_str()).unwrap_or("").to_string();
    let v = |k: &str| j.get("version").and_then(|x| x.get(k)).and_then(|x| x.as_str()).unwrap_or("").to_string();
    let id = Identitet {
        instans: s("instans"),
        rot: s("rot"),
        pid: j.get("pid").and_then(|v| v.as_u64()).unwrap_or(0) as u32,
        port: j.get("port").and_then(|v| v.as_u64()).unwrap_or(0) as u16,
        commit: v("commit"),
        commit_pa_disk: v("commit_pa_disk"),
        ui: v("ui"),
        startad: v("startad"),
        utdaterad: j.get("version").and_then(|x| x.get("utdaterad")).and_then(|x| x.as_bool()).unwrap_or(false),
        kontrakt: s("kontrakt"),
    };
    let meddelande = format!("nwp-desktop/1\n{utmaning}\n{}\n{}\n{}\n{}\n{}", id.instans, id.rot, id.pid, id.port, id.commit);
    let mut mac = <Hmac<Sha256> as Mac>::new_from_slice(nyckel.as_bytes()).expect("hmac");
    mac.update(meddelande.as_bytes());
    let bevis = match hex::decode(s("bevis")) {
        Ok(b) => b,
        Err(_) => return Status::FelInstans { orsak: "beviset var inte hex".into(), pid: Some(pid) },
    };
    if mac.verify_slice(&bevis).is_err() {
        return Status::FelInstans { orsak: "motorn kunde inte bevisa nyckeln (en annan instans, eller en nyckelfil från en tidigare start)".into(), pid: Some(pid) };
    }
    if id.pid != pid || id.port != inst.port || PathBuf::from(&id.rot) != rot {
        return Status::FelInstans { orsak: "identiteten gäller inte den process som lyssnar på porten".into(), pid: Some(pid) };
    }
    if id.kontrakt != KONTRAKT && !id.kontrakt.starts_with(&format!("{KONTRAKT}.")) {
        return Status::Inkompatibel { orsak: format!("motorn har kontraktet {}, appen stöder {KONTRAKT}", id.kontrakt) };
    }
    Status::Verifierad { identitet: id }
}

/// PATH för motorn: de registrerade verktygens kataloger och systemets, inget ur en profil.
pub fn kontrollerad_path(v: &Verktyg) -> String {
    let mut delar: Vec<String> = Vec::new();
    for p in [&v.claude, &v.node].into_iter().flatten() {
        if let Some(k) = p.parent() {
            let k = k.display().to_string();
            if !delar.contains(&k) {
                delar.push(k);
            }
        }
    }
    for k in ["/usr/bin", "/bin", "/usr/sbin", "/sbin"] {
        delar.push(k.into());
    }
    delar.join(":")
}

/// Startar motorn genom den befintliga startvägen (`dashboard.sh start`, ingen webbläsare) om inget lyssnar på porten.
/// En motor som redan kör återansluts, aldrig ersätts; en främmande process på porten stoppas aldrig.
pub fn starta(inst: &Installningar) -> Result<Status, String> {
    let rot = validera_rot(inst.rot.as_ref().ok_or("ingen motor registrerad")?)?;
    if lyssnande_pid(inst.port).is_some() {
        return Ok(status(inst));
    }
    let v = &inst.verktyg;
    if v.claude.is_none() {
        return Err("claude hittades inte; installera Claude Code eller välj verktygen igen under Inställningar".into());
    }
    if v.node.is_none() {
        return Err("node hittades inte; installera Node (node@24 via Homebrew) eller välj verktygen igen".into());
    }
    let mut c = Command::new("/bin/bash");
    c.arg(rot.join("dashboard.sh")).arg("start").current_dir(&rot).env_clear();
    for k in ["HOME", "USER", "LOGNAME", "TMPDIR", "LANG", "LC_ALL", "SHELL"] {
        if let Some(val) = std::env::var_os(k) {
            c.env(k, val);
        }
    }
    c.env("PATH", kontrollerad_path(v)).env("NWP_UTAN_OPPNA", "1").env("NWP_DASHBOARD_PORT", inst.port.to_string());
    let ut = c.output().map_err(|e| format!("dashboard.sh kunde inte köras: {e}"))?;
    if !ut.status.success() {
        let fel = String::from_utf8_lossy(&ut.stderr);
        return Err(format!("motorn startade inte: {}", fel.lines().last().unwrap_or("okänt fel (se ~/Library/Logs/nortropic-dashboard.log)")));
    }
    Ok(status(inst))
}

/// Skriver till motorns två vägar för appen (/api/desktop/session och /las), först efter ett nytt identitetsprov. Anropet
/// bevisas med HMAC-SHA256(nyckeln, tid, nonce, väg, kroppens sha256) i X-Desktop-Bevis; nyckeln själv skickas aldrig,
/// så en process som tar porten mellan provet och skrivningen får inget den kan använda.
pub fn skriv(inst: &Installningar, vag: &str, kropp: &serde_json::Value) -> Result<serde_json::Value, String> {
    use sha2::Digest;
    let Status::Verifierad { identitet } = status(inst) else { return Err("motorn är inte verifierad".into()) };
    let rot = PathBuf::from(&identitet.rot);
    let nyckel = las_nyckel(&rot)?;
    let ursprung = format!("http://127.0.0.1:{}", inst.port);
    let b = serde_json::to_vec(kropp).map_err(|e| e.to_string())?;
    let ts = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
    let nonce = slump_hex(16);
    let msg = format!("nwp-desktop/1 skriv\n{ts}\n{nonce}\n{vag}\n{}", hex::encode(Sha256::digest(&b)));
    let mut mac = <Hmac<Sha256> as Mac>::new_from_slice(nyckel.as_bytes()).expect("hmac");
    mac.update(msg.as_bytes());
    let bevis = format!("{ts}.{nonce}.{}", hex::encode(mac.finalize().into_bytes()));
    let s = http::anrop(inst.port, "POST", vag, &[("X-Desktop-Bevis", &bevis), ("Origin", &ursprung)], Some(&b), Duration::from_secs(10))?;
    let j = s.json()?;
    if s.status >= 300 {
        return Err(j.get("fel").and_then(|v| v.as_str()).unwrap_or("motorn nekade").to_string());
    }
    Ok(j)
}

pub fn las(inst: &Installningar, vag: &str) -> Result<serde_json::Value, String> {
    let s = http::anrop(inst.port, "GET", vag, &[], None, Duration::from_secs(10))?;
    if s.status != 200 {
        return Err(format!("{vag} svarade {}", s.status));
    }
    s.json()
}
