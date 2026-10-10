//! Nortropic.app: ett tunt Tauri 2-skal runt motorns arbetsyta (kunskap/desktop.md).
//!
//! Huvudfönstret visar först appens paketerade skal (tauri://localhost: lås, första start, diagnos, senast kända läge).
//! Efter upplåsningen och identitetsprovet navigerar appen fönstret till motorns arbetsyta på 127.0.0.1 med en
//! kortlivad engångskod som motorn byter mot en HttpOnly-session. Motorns sida och förhandsvisningarna har inga
//! native-rättigheter: kommandona nedan är bara tillåtna för appens egna sidor (capabilities/huvud.json).

mod http;
mod installningar;
mod motor;
mod upplasning;
mod uppdatering;
#[cfg(feature = "prov")]
mod prov;

use installningar::{Fonster, Installningar};
use serde_json::json;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, AtomicU16, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::webview::{NewWindowResponse, PageLoadEvent};
use tauri::{AppHandle, Manager, RunEvent, Url, WebviewUrl, WebviewWindow, WebviewWindowBuilder, WindowEvent};
use tauri_plugin_dialog::{DialogExt, MessageDialogButtons, MessageDialogKind, MessageDialogResult};

const HUVUD: &str = "huvud";
const SKAL: &str = "tauri://localhost/index.html";

pub struct Lage {
    data: PathBuf,
    inst: Mutex<Installningar>,
    upplast: AtomicBool,
    /// Porten som huvudfönstret får visa (satt efter identitetsprovet, 0 när appen är låst).
    motorport: AtomicU16,
    instans: Mutex<Option<String>>,
    /// Sekunder sedan epok då fönstret senast tappade fokus (0 = har fokus).
    ofokuserad_sedan: AtomicU64,
    uppmarksamhet: AtomicU64,
}

impl Lage {
    fn inst(&self) -> Installningar {
        self.inst.lock().unwrap().clone()
    }
}

fn nu() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0)
}

fn lage(app: &AppHandle) -> Arc<Lage> {
    app.state::<Arc<Lage>>().inner().clone()
}

fn huvudfonster(app: &AppHandle) -> Option<WebviewWindow> {
    app.get_webview_window(HUVUD)
}

fn visa(app: &AppHandle) {
    if let Some(w) = huvudfonster(app) {
        let _ = w.unminimize();
        let _ = w.show();
        let _ = w.set_focus();
    }
}

/// Öppnar en adress i systemets webbläsare (bara https och http; aldrig en fil eller ett schema). Det är det uttryckliga
/// undantaget för en förhandsvisning i en ny flik och för externa länkar (kunskap/desktop.md).
fn oppna_externt(url: &Url) {
    // https och http (också förhandsvisningen på 127.0.0.1); aldrig file:, javascript: eller ett eget schema
    let ok = matches!(url.scheme(), "https" | "http") && url.host_str().is_some();
    if ok {
        let _ = std::process::Command::new("/usr/bin/open").arg(url.as_str()).spawn();
    }
}

/// Låser appen: klientens session återkallas i motorn, fönstret visar skalet och motorns adress spärras för fönstret.
/// Godkänt arbete i motorn fortsätter enligt sitt mandat; låset stoppar inget.
fn las_appen(app: &AppHandle, orsak: &str) {
    let l = lage(app);
    let var_upplast = l.upplast.swap(false, Ordering::SeqCst);
    l.motorport.store(0, Ordering::SeqCst);
    if let Some(w) = huvudfonster(app) {
        let _ = w.navigate(Url::parse(&format!("{SKAL}#last={}", urlkoda(orsak))).unwrap());
    }
    if var_upplast {
        let inst = l.inst();
        std::thread::spawn(move || {
            let _ = motor::skriv(&inst, "/api/desktop/las", &json!({}));
        });
    }
}

fn urlkoda(s: &str) -> String {
    s.bytes().map(|b| if b.is_ascii_alphanumeric() || b"-_.".contains(&b) { (b as char).to_string() } else { format!("%{b:02X}") }).collect()
}

/// Navigeringsspärren. wry frågar för varje ram (också förhandsvisningens iframes), så här nekas bara det som aldrig
/// får laddas: filer, okända scheman och motorns adress när appen är låst. Huvudramen prövas dessutom i on_page_load.
fn tillat_navigering(app: &AppHandle, url: &Url) -> bool {
    let l = lage(app);
    match url.scheme() {
        "tauri" => url.host_str() == Some("localhost"),
        "http" => {
            let loopback = matches!(url.host_str(), Some("127.0.0.1") | Some("localhost"));
            if !loopback {
                return true; // en kundsajts inbäddningar i en förhandsvisning; huvudramen prövas vid sidladdningen
            }
            let port = url.port().unwrap_or(80);
            if port == l.inst().port {
                return l.upplast.load(Ordering::SeqCst) && l.motorport.load(Ordering::SeqCst) == port;
            }
            true // förhandsvisningarnas egna portar, i sandlådade iframes
        }
        "https" | "about" | "data" | "blob" => true,
        _ => false,
    }
}

/// Huvudramen får bara visa skalet eller den verifierade motorns arbetsyta. Allt annat leds tillbaka.
fn prova_huvudram(w: &WebviewWindow, url: &Url) {
    let app = w.app_handle().clone();
    let l = lage(&app);
    let motor = l.motorport.load(Ordering::SeqCst);
    // portalens Lås: sidan har redan loggat ut med POST /api/desktop/utloggning och går sedan till /desktop/last i
    // huvudramen; bara huvudramens sidladdning låser appen (en förhandsvisnings iframe kan aldrig göra det)
    if url.scheme() == "http" && url.host_str() == Some("127.0.0.1") && url.port() == Some(motor) && motor != 0 && url.path() == "/desktop/last" {
        std::thread::spawn(move || las_appen(&app, "utloggad"));
        return;
    }
    let ok = match url.scheme() {
        "tauri" => url.host_str() == Some("localhost"),
        "http" => l.upplast.load(Ordering::SeqCst) && url.host_str() == Some("127.0.0.1") && url.port() == Some(motor) && motor != 0,
        "about" => url.as_str() == "about:blank",
        _ => false,
    };
    if !ok {
        oppna_externt(url);
        let tillbaka = if l.upplast.load(Ordering::SeqCst) && motor != 0 { format!("http://127.0.0.1:{motor}/") } else { SKAL.to_string() };
        let _ = w.navigate(Url::parse(&tillbaka).unwrap());
    }
}

fn skapa_fonster(app: &AppHandle) -> tauri::Result<WebviewWindow> {
    let l = lage(app);
    let a1 = app.clone();
    let mut b = WebviewWindowBuilder::new(app, HUVUD, WebviewUrl::App("index.html".into()))
        .title("Nortropic")
        .inner_size(1440.0, 900.0)
        .min_inner_size(960.0, 640.0)
        .disable_drag_drop_handler() // Finder-filer går till sidans egen uppladdningsväg (HTML5 drop), inte till native
        .on_navigation(move |url| tillat_navigering(&a1, url))
        .on_new_window(|url, _| {
            oppna_externt(&url);
            NewWindowResponse::Deny
        })
        .on_page_load(|w, p| {
            if p.event() == PageLoadEvent::Started {
                prova_huvudram(&w, p.url());
            }
        });
    if let Some(f) = l.inst().fonster.as_ref().filter(|f| pa_en_skarm(app, f)) {
        b = b.position(f.x as f64, f.y as f64).inner_size(f.bredd as f64, f.hojd as f64);
    } else {
        b = b.center();
    }
    let w = b.build()?;
    Ok(w)
}

/// En sparad fönsterplats används bara när den hamnar på en skärm som finns nu.
fn pa_en_skarm(app: &AppHandle, f: &Fonster) -> bool {
    app.available_monitors().map(|ms| {
        ms.iter().any(|m| {
            let s = m.scale_factor();
            let p = m.position().to_logical::<f64>(s);
            let z = m.size().to_logical::<f64>(s);
            let (x, y) = (f.x as f64 + 40.0, f.y as f64 + 20.0);
            x >= p.x && x < p.x + z.width && y >= p.y && y < p.y + z.height
        })
    }).unwrap_or(false)
}

fn spara_fonster(w: &tauri::Window) {
    let app = w.app_handle();
    let l = lage(app);
    let (Ok(pos), Ok(stl), Ok(s)) = (w.outer_position(), w.inner_size(), w.scale_factor()) else { return };
    let pos = pos.to_logical::<f64>(s);
    let stl = stl.to_logical::<f64>(s);
    let mut inst = l.inst.lock().unwrap();
    inst.fonster = Some(Fonster { x: pos.x as i32, y: pos.y as i32, bredd: stl.width as u32, hojd: stl.height as u32, helskarm: w.is_fullscreen().unwrap_or(false) });
    let _ = installningar::spara(&l.data, &inst);
}

// ---------- kommandona (bara för appens egna sidor) ----------

#[tauri::command]
async fn diagnos(app: AppHandle) -> Result<serde_json::Value, String> {
    let l = lage(&app);
    tauri::async_runtime::spawn_blocking(move || {
        let inst = l.inst();
        let motor = motor::status(&inst);
        if let motor::Status::Verifierad { identitet } = &motor {
            *l.instans.lock().unwrap() = Some(identitet.instans.clone());
        }
        let rotfel = inst.rot.as_ref().and_then(|r| motor::validera_rot(r).err());
        let forslag = if inst.rot.is_none() { motor::huvudrot().filter(|r| motor::validera_rot(r).is_ok()) } else { None };
        json!({
            "app": { "version": env!("CARGO_PKG_VERSION"), "kontrakt": motor::KONTRAKT, "prov": cfg!(feature = "prov") },
            "installningar": { "rot": inst.rot, "port": inst.port, "verktyg": inst.verktyg, "avslut": inst.avslut, "las_efter_min": inst.las_efter_min, "aviseringar": inst.aviseringar },
            "upptackta_verktyg": motor::hitta_verktyg(),
            "rotfel": rotfel,
            "rotforslag": forslag,
            "motor": motor,
            "upplast": l.upplast.load(Ordering::SeqCst),
            "natet": natet(),
        })
    })
    .await
    .map_err(|e| e.to_string())
}

static NATET: Mutex<Option<(u64, serde_json::Value)>> = Mutex::new(None);

/// Internet prövas för sig (en TCP-anslutning till modellernas tjänst), skilt från den lokala motorn; högst var 30:e sekund.
fn natet() -> serde_json::Value {
    use std::net::{TcpStream, ToSocketAddrs};
    if let Some((t, v)) = NATET.lock().unwrap().as_ref() {
        if nu().saturating_sub(*t) < 30 {
            return v.clone();
        }
    }
    let start = std::time::Instant::now();
    let ok = ("api.anthropic.com", 443).to_socket_addrs().ok().and_then(|mut a| a.next()).map(|a| TcpStream::connect_timeout(&a, Duration::from_millis(1500)).is_ok()).unwrap_or(false);
    let v = json!({ "nar": ok, "ms": start.elapsed().as_millis() as u64 });
    *NATET.lock().unwrap() = Some((nu(), v.clone()));
    v
}

#[tauri::command]
async fn valj_motorrot(app: AppHandle) -> Result<Option<String>, String> {
    let vald = app.dialog().file().set_title("Välj Nortropics motor (nortropic-webb-pro)").blocking_pick_folder();
    match vald {
        None => Ok(None),
        Some(p) => {
            let p = p.into_path().map_err(|e| e.to_string())?;
            motor::validera_rot(&p).map(|r| Some(r.display().to_string()))
        }
    }
}

#[tauri::command]
async fn registrera_motor(app: AppHandle, rot: String, port: u16) -> Result<serde_json::Value, String> {
    if !(1024..=65535).contains(&port) {
        return Err("porten ska vara mellan 1024 och 65535".into());
    }
    let r = motor::validera_rot(&PathBuf::from(&rot))?;
    let l = lage(&app);
    let v = motor::hitta_verktyg();
    let mut inst = l.inst.lock().unwrap();
    inst.rot = Some(r.clone());
    inst.port = port;
    inst.verktyg = v.clone();
    installningar::spara(&l.data, &inst)?;
    Ok(json!({ "rot": r, "port": port, "verktyg": v }))
}

#[tauri::command]
async fn starta_motor(app: AppHandle) -> Result<serde_json::Value, String> {
    let l = lage(&app);
    tauri::async_runtime::spawn_blocking(move || motor::starta(&l.inst()).map(|s| json!(s))).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn las_upp(app: AppHandle) -> Result<serde_json::Value, String> {
    let l = lage(&app);
    let skal = "låsa upp Nortropic och dina kunders material";
    let r = tauri::async_runtime::spawn_blocking(move || {
        #[cfg(feature = "prov")]
        if prov::upplasning_attrapp() {
            return Ok(());
        }
        upplasning::las_upp(skal)
    })
    .await
    .map_err(|e| e.to_string())?;
    r?;
    l.upplast.store(true, Ordering::SeqCst);
    l.ofokuserad_sedan.store(0, Ordering::SeqCst);
    oppna_arbetsytan(app, None).await
}

/// Öppnar motorns arbetsyta i huvudfönstret: nytt identitetsprov, en engångskod med nyckeln (native), sedan navigering
/// till motorns inloggningsväg som sätter en HttpOnly-session. Nyckeln når aldrig renderern.
#[tauri::command]
async fn oppna_arbetsytan(app: AppHandle, till: Option<String>) -> Result<serde_json::Value, String> {
    let l = lage(&app);
    if !l.upplast.load(Ordering::SeqCst) {
        return Err("appen är låst".into());
    }
    let till = till.filter(|t| t.len() <= 120 && t.bytes().all(|b| b.is_ascii_alphanumeric() || b"/-".contains(&b))).unwrap_or_default();
    let l2 = l.clone();
    let (status, kod) = tauri::async_runtime::spawn_blocking(move || {
        let inst = l2.inst();
        let s = motor::status(&inst);
        let motor::Status::Verifierad { identitet } = &s else { return (s, None) };
        let k = motor::skriv(&inst, "/api/desktop/session", &json!({ "instans": identitet.instans })).ok().and_then(|j| j.get("kod").and_then(|v| v.as_str()).map(String::from));
        (s, k)
    })
    .await
    .map_err(|e| e.to_string())?;
    let motor::Status::Verifierad { identitet } = &status else {
        return Ok(json!({ "oppnad": false, "motor": status }));
    };
    let Some(kod) = kod else { return Err("motorn gav ingen inloggningskod".into()) };
    *l.instans.lock().unwrap() = Some(identitet.instans.clone());
    l.motorport.store(identitet.port, Ordering::SeqCst);
    let url = format!("http://127.0.0.1:{}/desktop/inloggning?kod={kod}&till={till}", identitet.port);
    if let Some(w) = huvudfonster(&app) {
        w.navigate(Url::parse(&url).map_err(|e| e.to_string())?).map_err(|e| e.to_string())?;
    }
    let inst = l.inst();
    let data = l.data.clone();
    std::thread::spawn(move || spara_senast_kanda(&inst, &data));
    Ok(json!({ "oppnad": true, "motor": status }))
}

#[tauri::command]
async fn las(app: AppHandle) -> Result<(), String> {
    las_appen(&app, "last");
    Ok(())
}

/// Senast kända översikt (åtkomstbunden: bara när appen är upplåst). Visas när motorn är stoppad, märkt med tiden.
#[tauri::command]
async fn senast_kanda(app: AppHandle) -> Result<serde_json::Value, String> {
    let l = lage(&app);
    if !l.upplast.load(Ordering::SeqCst) {
        return Err("appen är låst".into());
    }
    let b = std::fs::read(l.data.join("senast-kanda.json")).map_err(|_| "inget sparat läge än".to_string())?;
    serde_json::from_slice(&b).map_err(|e| e.to_string())
}

fn spara_senast_kanda(inst: &Installningar, data: &std::path::Path) {
    if let Ok(j) = motor::las(inst, "/api/desktop/oversikt") {
        let ut = json!({ "sparad": nu(), "oversikt": j });
        let _ = installningar::skriv_privat(&data.join("senast-kanda.json"), &serde_json::to_vec(&ut).unwrap_or_default());
    }
}

/// Finns en nyare signerad utgåva i den verifierade motorn? Installerar ingenting.
#[tauri::command]
async fn sok_uppdatering(app: AppHandle) -> Result<serde_json::Value, String> {
    let l = lage(&app);
    tauri::async_runtime::spawn_blocking(move || {
        let inst = l.inst();
        let u = uppdatering::sok(&inst)?;
        let pagaende = motor::las(&inst, "/api/desktop/pagaende").ok().and_then(|j| j.get("pagaende").cloned()).unwrap_or(json!([]));
        let plats = uppdatering::eget_paket().map(|p| p.display().to_string());
        Ok(json!({ "nuvarande": env!("CARGO_PKG_VERSION"), "utgava": u, "pagaende": pagaende, "plats": plats.as_ref().ok(), "platsfel": plats.err(),
                   "forra_finns": l.data.join("forra-version/Nortropic.app/Contents/Info.plist").exists() }))
    })
    .await
    .map_err(|e| e.to_string())?
}

/// Installerar den signerade utgåvan efter ägarens val och startar om appen. Pågår arbete i motorn visar skalet det och
/// knappen säger "Installera ändå" (arbetet påverkas inte: det körs av motorn); utan det klicket skjuts den upp.
#[tauri::command]
async fn installera_uppdatering(app: AppHandle, version: String, aven_under_arbete: bool) -> Result<serde_json::Value, String> {
    let l = lage(&app);
    let a = app.clone();
    tauri::async_runtime::spawn_blocking(move || {
        let inst = l.inst();
        let u = uppdatering::sok(&inst)?.ok_or("ingen nyare utgåva finns")?;
        if u.version != version {
            return Err(format!("utgåvan har ändrats sedan du valde (nu {}); sök igen", u.version));
        }
        let pagar = motor::las(&inst, "/api/desktop/pagaende").ok().and_then(|j| j.get("pagaende").and_then(|v| v.as_array()).map(|x| x.len())).unwrap_or(0);
        if pagar > 0 && !aven_under_arbete {
            return Ok(json!({ "installerad": false, "uppskjuten": true, "pagaende": pagar }));
        }
        let paket = uppdatering::installera(&inst, &u, &l.data)?;
        uppdatering::starta_om(&paket);
        aterkalla_sessioner(&inst);
        a.exit(0);
        Ok(json!({ "installerad": true, "version": u.version }))
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
async fn ga_tillbaka_version(app: AppHandle) -> Result<(), String> {
    let l = lage(&app);
    let paket = uppdatering::ga_tillbaka(&l.data)?;
    uppdatering::starta_om(&paket);
    app.exit(0);
    Ok(())
}

#[tauri::command]
async fn installning(app: AppHandle, nyckel: String, varde: String) -> Result<serde_json::Value, String> {
    let l = lage(&app);
    let mut inst = l.inst.lock().unwrap();
    match nyckel.as_str() {
        "avslut" if ["fraga", "behall"].contains(&varde.as_str()) => inst.avslut = varde,
        "las_efter_min" => inst.las_efter_min = varde.parse::<u32>().ok().filter(|m| *m <= 480).ok_or("0–480 minuter")?,
        "aviseringar" if ["pa", "av"].contains(&varde.as_str()) => inst.aviseringar = varde == "pa",
        _ => return Err("okänd inställning".into()),
    }
    installningar::spara(&l.data, &inst)?;
    Ok(json!({ "avslut": inst.avslut, "las_efter_min": inst.las_efter_min, "aviseringar": inst.aviseringar }))
}

// ---------- menyn ----------

fn meny(app: &AppHandle) -> tauri::Result<Menu<tauri::Wry>> {
    let om = PredefinedMenuItem::about(app, Some("Om Nortropic"), None)?;
    let las = MenuItem::with_id(app, "las", "Lås Nortropic", true, Some("CmdOrCtrl+Shift+L"))?;
    let diagnos = MenuItem::with_id(app, "diagnos", "Motor och diagnos…", true, None::<&str>)?;
    let uppd = MenuItem::with_id(app, "uppdatering", "Sök efter uppdatering…", true, None::<&str>)?;
    let avsluta = MenuItem::with_id(app, "avsluta", "Avsluta Nortropic", true, Some("CmdOrCtrl+Q"))?;
    let appmeny = Submenu::with_items(app, "Nortropic", true, &[
        &om,
        &PredefinedMenuItem::separator(app)?,
        &diagnos,
        &uppd,
        &las,
        &PredefinedMenuItem::separator(app)?,
        &PredefinedMenuItem::services(app, None)?,
        &PredefinedMenuItem::separator(app)?,
        &PredefinedMenuItem::hide(app, Some("Göm Nortropic"))?,
        &PredefinedMenuItem::hide_others(app, Some("Göm övriga"))?,
        &PredefinedMenuItem::show_all(app, Some("Visa alla"))?,
        &PredefinedMenuItem::separator(app)?,
        &avsluta,
    ])?;
    let arkiv = Submenu::with_items(app, "Arkiv", true, &[
        &MenuItem::with_id(app, "ny_kund", "Ny kund", true, Some("CmdOrCtrl+N"))?,
        &MenuItem::with_id(app, "kunder", "Kunder", true, Some("CmdOrCtrl+1"))?,
        &MenuItem::with_id(app, "testkunder", "Testkunder", true, Some("CmdOrCtrl+2"))?,
        &MenuItem::with_id(app, "oversikt", "Översikt", true, Some("CmdOrCtrl+Shift+H"))?,
        &PredefinedMenuItem::separator(app)?,
        &PredefinedMenuItem::close_window(app, Some("Stäng fönstret"))?,
    ])?;
    let redigera = Submenu::with_items(app, "Redigera", true, &[
        &PredefinedMenuItem::undo(app, Some("Ångra"))?,
        &PredefinedMenuItem::redo(app, Some("Gör om"))?,
        &PredefinedMenuItem::separator(app)?,
        &PredefinedMenuItem::cut(app, Some("Klipp ut"))?,
        &PredefinedMenuItem::copy(app, Some("Kopiera"))?,
        &PredefinedMenuItem::paste(app, Some("Klistra in"))?,
        &PredefinedMenuItem::select_all(app, Some("Markera allt"))?,
    ])?;
    let visa_ = Submenu::with_items(app, "Visa", true, &[
        &MenuItem::with_id(app, "ladda_om", "Läs in arbetsytan igen", true, Some("CmdOrCtrl+R"))?,
        &PredefinedMenuItem::separator(app)?,
        &MenuItem::with_id(app, "storre", "Större", true, Some("CmdOrCtrl+Plus"))?,
        &MenuItem::with_id(app, "mindre", "Mindre", true, Some("CmdOrCtrl+-"))?,
        &MenuItem::with_id(app, "verklig", "Verklig storlek", true, Some("CmdOrCtrl+0"))?,
        &PredefinedMenuItem::separator(app)?,
        &PredefinedMenuItem::fullscreen(app, Some("Helskärm"))?,
    ])?;
    let fonster = Submenu::with_items(app, "Fönster", true, &[
        &PredefinedMenuItem::minimize(app, Some("Minimera"))?,
        &PredefinedMenuItem::maximize(app, Some("Zooma"))?,
        &PredefinedMenuItem::separator(app)?,
        &MenuItem::with_id(app, "visa", "Nortropic", true, None::<&str>)?,
    ])?;
    let hjalp = Submenu::with_items(app, "Hjälp", true, &[&MenuItem::with_id(app, "hjalp", "Nortropic hjälp", true, None::<&str>)?])?;
    Menu::with_items(app, &[&appmeny, &arkiv, &redigera, &visa_, &fonster, &hjalp])
}

/// En vy i motorns arbetsyta via adressens fragment (ingen omladdning, inget utkast går förlorat). Menyval går genom
/// sidans egna vyer och samma handlingskontrakt som knapparna; inget menyval skriver något självt.
fn ga_till(app: &AppHandle, fragment: &str) {
    let l = lage(app);
    visa(app);
    let Some(w) = huvudfonster(app) else { return };
    if l.upplast.load(Ordering::SeqCst) && l.motorport.load(Ordering::SeqCst) != 0 {
        let _ = w.eval(&format!("location.hash = {};", serde_json::to_string(fragment).unwrap()));
    }
}

static ZOOM: Mutex<f64> = Mutex::new(1.0);

fn menyval(app: &AppHandle, id: &str) {
    match id {
        "las" => las_appen(app, "last"),
        "avsluta" => {
            let a = app.clone();
            std::thread::spawn(move || avsluta(&a));
        }
        "diagnos" | "hjalp" | "uppdatering" => {
            visa(app);
            if let Some(w) = huvudfonster(app) {
                let frag = match id { "hjalp" => "hjalp", "uppdatering" => "diagnos-uppdatering", _ => "diagnos" };
                if lage(app).upplast.load(Ordering::SeqCst) {
                    // skalet visar diagnosen; arbetsytan står kvar i motorn och öppnas igen därifrån
                    let _ = w.navigate(Url::parse(&format!("{SKAL}#{frag}")).unwrap());
                } else {
                    let _ = w.eval(&format!("location.hash = '#{frag}';"));
                }
            }
        }
        "ny_kund" => ga_till(app, "#/ny-kund"),
        "kunder" => ga_till(app, "#/kunder"),
        "testkunder" => ga_till(app, "#/testkunder"),
        "oversikt" => ga_till(app, "#/start"),
        "ladda_om" => {
            if let Some(w) = huvudfonster(app) {
                let _ = w.eval("location.reload();");
            }
        }
        "storre" | "mindre" | "verklig" => {
            let mut z = ZOOM.lock().unwrap();
            *z = match id { "storre" => (*z + 0.1).min(2.0), "mindre" => (*z - 0.1).max(0.6), _ => 1.0 };
            if let Some(w) = huvudfonster(app) {
                let _ = w.set_zoom(*z);
            }
        }
        "visa" => visa(app),
        _ => {}
    }
}

/// Cmd-Q: pågår arbete frågar appen först (om inte "behåll" valts i inställningarna). Avslutet stänger bara appen;
/// motorn och dess arbeten är fristående och fortsätter enligt sina mandat. Stopp görs i arbetsytan med motorns stoppväg.
fn avsluta(app: &AppHandle) {
    let l = lage(app);
    let inst = l.inst();
    let pagaende: Vec<serde_json::Value> = match motor::status(&inst) {
        motor::Status::Verifierad { .. } => motor::las(&inst, "/api/desktop/pagaende").ok().and_then(|j| j.get("pagaende").and_then(|v| v.as_array()).cloned()).unwrap_or_default(),
        _ => vec![],
    };
    if pagaende.is_empty() || inst.avslut == "behall" {
        aterkalla_sessioner(&inst);
        app.exit(0);
        return;
    }
    let upplast = l.upplast.load(Ordering::SeqCst);
    let lista = if upplast {
        pagaende.iter().take(6).map(|p| format!("• {} ({})", p.get("slug").and_then(|v| v.as_str()).unwrap_or("okänd kund"), p.get("vad").and_then(|v| v.as_str()).unwrap_or("arbete"))).collect::<Vec<_>>().join("\n")
    } else {
        format!("{} pågående {} (lås upp för att se vilka)", pagaende.len(), if pagaende.len() == 1 { "arbete" } else { "arbeten" })
    };
    let r = app
        .dialog()
        .message(format!("{lista}\n\nArbetet körs av den lokala motorn, inte av fönstret. Avslutar du Nortropic fortsätter godkänt arbete i bakgrunden, och appen visar läget när du öppnar den igen. Vill du stoppa ett arbete gör du det under Kontroller i arbetsytan."))
        .title("Arbete pågår")
        .kind(MessageDialogKind::Info)
        .buttons(MessageDialogButtons::YesNoCancelCustom("Avsluta, arbetet fortsätter".into(), "Visa pågående arbete".into(), "Avbryt".into()))
        .blocking_show_with_result();
    match r {
        MessageDialogResult::Yes | MessageDialogResult::Ok => {
            aterkalla_sessioner(&inst);
            app.exit(0)
        }
        MessageDialogResult::Custom(t) if t.starts_with("Avsluta") => {
            aterkalla_sessioner(&inst);
            app.exit(0)
        }
        MessageDialogResult::No => {
            let slug = pagaende.first().and_then(|p| p.get("slug")).and_then(|v| v.as_str()).unwrap_or("").to_string();
            ga_till(app, &format!("#/arbetsyta/{slug}"));
        }
        MessageDialogResult::Custom(t) if t.starts_with("Visa") => {
            let slug = pagaende.first().and_then(|p| p.get("slug")).and_then(|v| v.as_str()).unwrap_or("").to_string();
            ga_till(app, &format!("#/arbetsyta/{slug}"));
        }
        _ => {}
    }
}

/// Appens sessioner i motorn återkallas när appen avslutas (högst två sekunder; kakan är dessutom en sessionskaka).
fn aterkalla_sessioner(inst: &Installningar) {
    let inst = inst.clone();
    let (tx, rx) = std::sync::mpsc::channel();
    std::thread::spawn(move || {
        let _ = motor::skriv(&inst, "/api/desktop/las", &json!({}));
        let _ = tx.send(());
    });
    let _ = rx.recv_timeout(Duration::from_secs(2));
}

/// Låset efter tid utan fokus, i en egen tråd som aldrig väntar på motorn eller ett verktyg.
fn lastimer(app: AppHandle) {
    std::thread::spawn(move || loop {
        std::thread::sleep(Duration::from_secs(15));
        let l = lage(&app);
        let min = l.inst().las_efter_min;
        let sedan = l.ofokuserad_sedan.load(Ordering::SeqCst);
        if l.upplast.load(Ordering::SeqCst) && min > 0 && sedan > 0 && nu().saturating_sub(sedan) > min as u64 * 60 {
            las_appen(&app, "tidsgrans");
        }
    });
}

/// Bakgrundsvakten: låser efter inställd tid utan fokus, upptäcker en ny motorinstans och aviserar när något nytt
/// väntar på ägaren. Läser bara; startar aldrig något arbete eller någon modell.
fn vakt(app: AppHandle) {
    std::thread::spawn(move || loop {
        std::thread::sleep(Duration::from_secs(20));
        let l = lage(&app);
        let inst = l.inst();
        let upplast = l.upplast.load(Ordering::SeqCst);
        if inst.rot.is_none() {
            continue;
        }
        let s = motor::status(&inst);
        let motor::Status::Verifierad { identitet } = &s else {
            if upplast && l.motorport.load(Ordering::SeqCst) != 0 {
                // motorn försvann eller bytte identitet medan arbetsytan var öppen: visa skalets frånkopplade läge
                l.motorport.store(0, Ordering::SeqCst);
                if let Some(w) = huvudfonster(&app) {
                    let _ = w.navigate(Url::parse(&format!("{SKAL}#franKopplad")).unwrap());
                }
            }
            continue;
        };
        let byttes = l.instans.lock().unwrap().as_deref().map(|i| i != identitet.instans).unwrap_or(false);
        if byttes && upplast && l.motorport.load(Ordering::SeqCst) != 0 {
            // en omstartad motor har inga sessioner: ny kod genom samma väg, sidan laddas om i samma vy
            let a = app.clone();
            tauri::async_runtime::spawn(async move {
                let _ = oppna_arbetsytan(a, None).await;
            });
        }
        if let Ok(j) = motor::las(&inst, "/api/desktop/uppmarksamhet") {
            let n = j.get("antal").and_then(|v| v.as_u64()).unwrap_or(0);
            let forra = l.uppmarksamhet.swap(n, Ordering::SeqCst);
            if n > forra && forra != u64::MAX && inst.aviseringar {
                aviser(&app, upplast, n, &j);
            }
        }
    });
}

fn aviser(app: &AppHandle, upplast: bool, n: u64, j: &serde_json::Value) {
    use tauri_plugin_notification::NotificationExt;
    // låst: ingen kunduppgift i aviseringen
    let text = if upplast {
        j.get("forsta").and_then(|v| v.as_str()).map(|s| s.to_string()).unwrap_or_else(|| format!("{n} saker väntar på dig"))
    } else {
        "Något väntar på ditt beslut. Lås upp Nortropic för att se vad.".to_string()
    };
    let _ = app.notification().builder().title("Nortropic").body(text).show();
}

pub fn kor() {
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _argv, _cwd| visa(app)))
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_notification::init())
        .invoke_handler(tauri::generate_handler![
            diagnos,
            registrera_motor,
            valj_motorrot,
            starta_motor,
            las_upp,
            oppna_arbetsytan,
            las,
            senast_kanda,
            installning,
            sok_uppdatering,
            installera_uppdatering,
            ga_tillbaka_version
        ])
        .setup(|app| {
            let h = app.handle().clone();
            let data = app.path().app_data_dir()?;
            #[cfg(feature = "prov")]
            let data = prov::datakatalog().unwrap_or(data);
            std::fs::create_dir_all(&data)?;
            let inst = installningar::las(&data);
            app.manage(Arc::new(Lage {
                data,
                inst: Mutex::new(inst),
                upplast: AtomicBool::new(false),
                motorport: AtomicU16::new(0),
                instans: Mutex::new(None),
                ofokuserad_sedan: AtomicU64::new(0),
                uppmarksamhet: AtomicU64::new(u64::MAX),
            }));
            let m = meny(&h)?;
            app.set_menu(m)?;
            app.on_menu_event(|app, ev| menyval(app, ev.id().as_ref()));
            skapa_fonster(&h)?;
            vakt(h.clone());
            lastimer(h.clone());
            #[cfg(feature = "prov")]
            prov::starta(h.clone());
            Ok(())
        })
        .on_window_event(|w, ev| match ev {
            WindowEvent::CloseRequested { api, .. } if w.label() == HUVUD => {
                // röda knappen och Cmd-W stänger fönstret, inte appen eller motorn; Dock öppnar det igen
                api.prevent_close();
                spara_fonster(w);
                let _ = w.hide();
            }
            WindowEvent::Moved(_) | WindowEvent::Resized(_) => spara_fonster(w),
            WindowEvent::Focused(f) => {
                let l = lage(w.app_handle());
                l.ofokuserad_sedan.store(if *f { 0 } else { nu() }, Ordering::SeqCst);
            }
            _ => {}
        })
        .build(tauri::generate_context!())
        .expect("Nortropic kunde inte starta")
        .run(|app, ev| match ev {
            RunEvent::Reopen { .. } => visa(app),
            RunEvent::Exit => {
                // också Dock-menyns Avsluta och utloggning ur macOS (Apple Event): sessionerna återkallas
                let l = lage(app);
                if l.upplast.load(Ordering::SeqCst) {
                    aterkalla_sessioner(&l.inst());
                }
            }
            RunEvent::ExitRequested { api, code, .. } => {
                // sista fönstret som göms avslutar inte appen (Mac-konventionen); bara Avsluta gör det
                if code.is_none() {
                    api.prevent_exit();
                }
            }
            _ => {}
        });
}
