//! Upplåsningen med macOS LocalAuthentication: Touch ID eller användarens lösenord (deviceOwnerAuthentication).
//! Det är en lokal operatörsupplåsning, aldrig en extern kontoinloggning (kunskap/desktop.md, Identiteten).

#[cfg(target_os = "macos")]
pub fn las_upp(skal: &str) -> Result<(), String> {
    use block2::RcBlock;
    use objc2::runtime::Bool;
    use objc2_foundation::{NSError, NSString};
    use objc2_local_authentication::{LAContext, LAPolicy};
    use std::sync::mpsc;
    use std::time::Duration;

    let ctx = unsafe { LAContext::new() };
    if let Err(e) = unsafe { ctx.canEvaluatePolicy_error(LAPolicy::DeviceOwnerAuthentication) } {
        return Err(format!("macOS kan inte låsa upp här: {}", e.localizedDescription()));
    }
    let (tx, rx) = mpsc::channel::<Result<(), String>>();
    let svar = RcBlock::new(move |ok: Bool, fel: *mut NSError| {
        let r = if ok.as_bool() {
            Ok(())
        } else if fel.is_null() {
            Err("upplåsningen avbröts".to_string())
        } else {
            let fel = unsafe { &*fel };
            Err(match fel.code() {
                -2 | -4 | -9 => "upplåsningen avbröts".to_string(),
                -1 => "fel lösenord eller fingeravtryck".to_string(),
                _ => fel.localizedDescription().to_string(),
            })
        };
        let _ = tx.send(r);
    });
    unsafe { ctx.evaluatePolicy_localizedReason_reply(LAPolicy::DeviceOwnerAuthentication, &NSString::from_str(skal), &svar) };
    rx.recv_timeout(Duration::from_secs(300)).unwrap_or_else(|_| Err("upplåsningen tog för lång tid".into()))
}

#[cfg(not(target_os = "macos"))]
pub fn las_upp(_skal: &str) -> Result<(), String> {
    Err("upplåsningen finns bara på macOS".into())
}
