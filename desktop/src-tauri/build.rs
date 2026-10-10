// Kommandona är namngivna i appmanifestet, så att varje kommando kräver en uttrycklig behörighet i capabilities/
// (minsta rättighet per fönster och ursprung; kunskap/desktop.md, Native-bryggan).
fn main() {
    tauri_build::try_build(tauri_build::Attributes::new().app_manifest(
        tauri_build::AppManifest::new().commands(&[
            "diagnos",
            "registrera_motor",
            "valj_motorrot",
            "starta_motor",
            "las_upp",
            "oppna_arbetsytan",
            "las",
            "senast_kanda",
            "installning",
            "prov_ogonblick",
        ]),
    ))
    .expect("tauri-build");
}
