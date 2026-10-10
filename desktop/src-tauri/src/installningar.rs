//! Appens inställningar i ~/Library/Application Support/se.nortropic.desktop/ (0600). Aldrig i apppaketet, en
//! monterad DMG eller en tempkatalog; inga kunddata här, bara registreringen och valen (kunskap/desktop.md, Lagring).

use serde::{Deserialize, Serialize};
use std::fs;
use std::io::Write;
use std::os::unix::fs::{OpenOptionsExt, PermissionsExt};
use std::path::{Path, PathBuf};

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct Verktyg {
    pub claude: Option<PathBuf>,
    pub node: Option<PathBuf>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Fonster {
    pub x: i32,
    pub y: i32,
    pub bredd: u32,
    pub hojd: u32,
    pub helskarm: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default)] // ett fält som saknas i en äldre fil får sitt standardvärde; resten av inställningarna står kvar
pub struct Installningar {
    /// Registrerad motorrot (en nortropic-webb-pro-utcheckning), vald av ägaren vid första starten.
    pub rot: Option<PathBuf>,
    pub port: u16,
    /// Verifierade absoluta sökvägar, upptäckta vid registreringen (Finder-starten ärver ingen terminal-PATH).
    pub verktyg: Verktyg,
    /// "fraga" (standard) eller "behall": vad Cmd-Q gör när arbete pågår.
    pub avslut: String,
    pub fonster: Option<Fonster>,
    /// Lås efter så många minuter utan aktivitet i appen (0 = aldrig).
    pub las_efter_min: u32,
    /// macOS-aviseringar när något nytt väntar på ägarens beslut; av tills ägaren slår på dem i Inställningar.
    #[serde(default)]
    pub aviseringar: bool,
}

impl Default for Installningar {
    fn default() -> Self {
        Installningar { rot: None, port: 4771, verktyg: Verktyg::default(), avslut: "fraga".into(), fonster: None, las_efter_min: 30, aviseringar: false }
    }
}

pub fn fil(data: &Path) -> PathBuf {
    data.join("installningar.json")
}

pub fn las(data: &Path) -> Installningar {
    fs::read(fil(data)).ok().and_then(|b| serde_json::from_slice(&b).ok()).unwrap_or_default()
}

/// Atomisk skrivning med 0600: först en tempfil i samma katalog, sedan rename.
pub fn skriv_privat(sokvag: &Path, innehall: &[u8]) -> Result<(), String> {
    let kat = sokvag.parent().ok_or("ingen katalog")?;
    fs::create_dir_all(kat).map_err(|e| e.to_string())?;
    fs::set_permissions(kat, fs::Permissions::from_mode(0o700)).ok();
    let tmp = kat.join(format!(".{}.{}.tmp", sokvag.file_name().and_then(|n| n.to_str()).unwrap_or("fil"), std::process::id()));
    {
        let mut f = fs::OpenOptions::new().write(true).create(true).truncate(true).mode(0o600).open(&tmp).map_err(|e| e.to_string())?;
        f.write_all(innehall).map_err(|e| e.to_string())?;
        f.sync_all().ok();
    }
    fs::rename(&tmp, sokvag).map_err(|e| e.to_string())
}

pub fn spara(data: &Path, i: &Installningar) -> Result<(), String> {
    let b = serde_json::to_vec_pretty(i).map_err(|e| e.to_string())?;
    skriv_privat(&fil(data), &b)
}
