//! Uppdateringen (kunskap/desktop.md, Uppdatering): en signerad utgåva som den verifierade motorn serverar från sin
//! utcheckning (`desktop/utgava/`, byggd av `desktop/bygg-utgava.sh`). Appen hämtar den över loopback, prövar minisign-
//! signaturen mot den inbyggda publika nyckeln och att signaturen är bunden till den annonserade versionen (samma kontroll
//! som Tauris uppdateringsmodul gör, `verify_signature`), packar upp i en tom katalog bredvid appen, prövar att paketet är
//! Nortropic i den versionen och byter sedan ut appen. Föregående version sparas i appens datakatalog för återgång.
//! Ingen uppdatering startar av sig själv: ägaren väljer Installera eller Senare, och pågående arbete i motorn påverkas
//! aldrig (det körs av motorn, inte av appen).

use crate::http;
use crate::installningar::Installningar;
use crate::motor;
use base64::Engine;
use serde::Serialize;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::Duration;

const PUBLIK_NYCKEL: &str = include_str!("../uppdatering.pub");
const IDENTIFIERARE: &str = "se.nortropic.desktop";

#[derive(Clone, Debug, Serialize)]
pub struct Utgava {
    pub version: String,
    pub kontrakt: String,
    pub noter: String,
    pub storlek: u64,
    pub signatur: String,
}

fn version_delar(v: &str) -> Vec<u64> {
    v.trim_start_matches('v').split(['.', '-', '+']).take(3).map(|x| x.parse().unwrap_or(0)).collect()
}

pub fn nyare(ny: &str, nu: &str) -> bool {
    version_delar(ny) > version_delar(nu)
}

/// Finns en nyare, kompatibel utgåva i den verifierade motorn?
pub fn sok(inst: &Installningar) -> Result<Option<Utgava>, String> {
    let motor::Status::Verifierad { .. } = motor::status(inst) else { return Err("motorn är inte verifierad".into()) };
    let s = http::anrop(inst.port, "GET", "/desktop/uppdatering/utgava", &[], None, Duration::from_secs(10))?;
    if s.status == 404 || s.status == 204 {
        return Ok(None);
    }
    if s.status != 200 {
        return Err(format!("utgåvan svarade {}", s.status));
    }
    let j = s.json()?;
    let g = |k: &str| j.get(k).and_then(|v| v.as_str()).unwrap_or("").to_string();
    let u = Utgava { version: g("version"), kontrakt: g("kontrakt"), noter: g("noter"), storlek: j.get("storlek").and_then(|v| v.as_u64()).unwrap_or(0), signatur: g("signatur") };
    if u.kontrakt != motor::KONTRAKT {
        return Err(format!("utgåvan kräver kontraktet {}, appen och motorn har {}", u.kontrakt, motor::KONTRAKT));
    }
    Ok(if nyare(&u.version, env!("CARGO_PKG_VERSION")) { Some(u) } else { None })
}

fn b64_text(s: &str) -> Result<String, String> {
    let b = base64::engine::general_purpose::STANDARD.decode(s.trim()).map_err(|_| "signaturen eller nyckeln är inte base64".to_string())?;
    String::from_utf8(b).map_err(|_| "signaturen eller nyckeln är inte text".into())
}

/// Minisign-signaturen över artefakten med den inbyggda nyckeln, och den signerade versionen lika med den annonserade.
pub fn verifiera(data: &[u8], signatur_b64: &str, version: &str, publik_b64: &str) -> Result<(), String> {
    let nyckel = minisign_verify::PublicKey::decode(&b64_text(publik_b64)?).map_err(|e| format!("den publika nyckeln: {e}"))?;
    let sig = minisign_verify::Signature::decode(&b64_text(signatur_b64)?).map_err(|e| format!("signaturen: {e}"))?;
    nyckel.verify(data, &sig, true).map_err(|_| "signaturen stämmer inte: utgåvan är ändrad eller signerad med en annan nyckel".to_string())?;
    let signerad = sig.trusted_comment().split('\t').find_map(|f| f.strip_prefix("version:")).ok_or("signaturen är inte bunden till en version")?;
    if version_delar(signerad) != version_delar(version) {
        return Err(format!("signaturen gäller version {signerad}, inte den annonserade {version}"));
    }
    Ok(())
}

fn las_plist_strang(plist: &[u8], nyckel: &str) -> Option<String> {
    let t = String::from_utf8_lossy(plist);
    let i = t.find(&format!("<key>{nyckel}</key>"))?;
    let rest = &t[i..];
    let a = rest.find("<string>")? + 8;
    let b = rest[a..].find("</string>")?;
    Some(rest[a..a + b].to_string())
}

/// Appens paket när den kör ur en Program-katalog; en app ur byggkatalogen uppdateras inte på plats.
pub fn eget_paket() -> Result<PathBuf, String> {
    let exe = std::env::current_exe().map_err(|e| e.to_string())?;
    let paket = exe.ancestors().nth(3).ok_or("okänd plats")?.to_path_buf();
    if paket.extension().and_then(|e| e.to_str()) != Some("app") {
        return Err("appen kör inte ur ett .app-paket".into());
    }
    let foralder = paket.parent().map(|p| p.display().to_string()).unwrap_or_default();
    if !(foralder.ends_with("/Applications")) {
        return Err(format!("appen kör ur {foralder}; uppdateringen installerar bara en app i Program (~/Applications)"));
    }
    Ok(paket)
}

/// Hämtar, verifierar och installerar utgåvan. Ger sökvägen till den nya appen; anroparen startar om.
pub fn installera(inst: &Installningar, u: &Utgava, data: &Path) -> Result<PathBuf, String> {
    let paket = eget_paket()?;
    let motor::Status::Verifierad { .. } = motor::status(inst) else { return Err("motorn är inte verifierad".into()) };
    let s = http::anrop_med_tak(inst.port, "GET", "/desktop/uppdatering/artefakt", &[], None, Duration::from_secs(120), 256 * 1024 * 1024)?;
    if s.status != 200 {
        return Err(format!("artefakten svarade {}", s.status));
    }
    verifiera(&s.kropp, &u.signatur, &u.version, PUBLIK_NYCKEL)?;
    let kat = paket.parent().ok_or("ingen katalog")?;
    let ny_kat = kat.join(format!(".Nortropic-uppdatering-{}", std::process::id()));
    let _ = fs::remove_dir_all(&ny_kat);
    fs::create_dir_all(&ny_kat).map_err(|e| e.to_string())?;
    let mut ark = tar::Archive::new(flate2::read::GzDecoder::new(&s.kropp[..]));
    ark.set_preserve_permissions(true);
    for post in ark.entries().map_err(|e| e.to_string())? {
        let mut post = post.map_err(|e| e.to_string())?;
        let p = post.path().map_err(|e| e.to_string())?.to_path_buf();
        if p.is_absolute() || p.components().any(|c| matches!(c, std::path::Component::ParentDir)) || !p.starts_with("Nortropic.app") {
            let _ = fs::remove_dir_all(&ny_kat);
            return Err(format!("artefakten innehåller en otillåten sökväg: {}", p.display()));
        }
        post.unpack_in(&ny_kat).map_err(|e| e.to_string())?;
    }
    let ny = ny_kat.join("Nortropic.app");
    let plist = fs::read(ny.join("Contents/Info.plist")).map_err(|_| "utgåvan saknar Info.plist".to_string())?;
    if las_plist_strang(&plist, "CFBundleIdentifier").as_deref() != Some(IDENTIFIERARE) || las_plist_strang(&plist, "CFBundleShortVersionString").as_deref() != Some(u.version.as_str()) {
        let _ = fs::remove_dir_all(&ny_kat);
        return Err("utgåvan är inte Nortropic i den annonserade versionen".into());
    }
    let forra = data.join("forra-version");
    let gammal = data.join(format!("forra-version-gammal-{}", std::process::id()));
    let _ = fs::remove_dir_all(&gammal);
    if forra.exists() {
        fs::rename(&forra, &gammal).map_err(|e| e.to_string())?;
    }
    let atergang = |fel: String| {
        let _ = fs::remove_dir_all(&forra);
        if gammal.exists() {
            let _ = fs::rename(&gammal, &forra);
        }
        let _ = fs::remove_dir_all(&ny_kat);
        fel
    };
    fs::create_dir_all(&forra).map_err(|e| atergang(e.to_string()))?;
    if let Err(e) = fs::rename(&paket, forra.join("Nortropic.app")) {
        return Err(atergang(format!("den nuvarande appen kunde inte flyttas undan: {e}")));
    }
    if let Err(e) = fs::rename(&ny, &paket) {
        let _ = fs::rename(forra.join("Nortropic.app"), &paket);
        return Err(atergang(format!("den nya appen kunde inte läggas på plats; den gamla är tillbaka: {e}")));
    }
    let _ = fs::remove_dir_all(&gammal);
    let _ = fs::remove_dir_all(&ny_kat);
    Ok(paket)
}

/// Återgång till den sparade föregående versionen (bara appkoden; motorns data och kontrakt berörs inte).
pub fn ga_tillbaka(data: &Path) -> Result<PathBuf, String> {
    let paket = eget_paket()?;
    let forra = data.join("forra-version/Nortropic.app");
    if !forra.join("Contents/Info.plist").exists() {
        return Err("ingen föregående version är sparad".into());
    }
    let tmp = data.join("forra-version/.nuvarande.app");
    let _ = fs::remove_dir_all(&tmp);
    fs::rename(&paket, &tmp).map_err(|e| e.to_string())?;
    if let Err(e) = fs::rename(&forra, &paket) {
        let _ = fs::rename(&tmp, &paket);
        return Err(e.to_string());
    }
    fs::rename(&tmp, &forra).map_err(|e| e.to_string())?;
    Ok(paket)
}

/// Startar den installerade appen igen efter att den här har avslutats (en andra instans skulle annars bara fokusera den
/// här, Single Instance).
pub fn starta_om(paket: &Path) {
    let _ = std::process::Command::new("/bin/sh")
        .arg("-c")
        .arg("while kill -0 \"$1\" 2>/dev/null; do sleep 0.2; done; /usr/bin/open \"$0\"")
        .arg(paket)
        .arg(std::process::id().to_string())
        .stdin(std::process::Stdio::null())
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn versioner() {
        assert!(nyare("0.2.0", "0.1.9"));
        assert!(!nyare("0.1.0", "0.1.0"));
        assert!(!nyare("0.0.9", "0.1.0"));
        assert!(nyare("v1.0.0", "0.9.9"));
    }

    #[test]
    fn fel_nyckel_och_skrap_nekas() {
        assert!(verifiera(b"data", "inte-base64!!", "0.1.0", PUBLIK_NYCKEL).is_err());
        assert!(verifiera(b"data", "", "0.1.0", PUBLIK_NYCKEL).is_err());
    }
}
