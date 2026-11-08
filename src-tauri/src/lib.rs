#![cfg_attr(test, allow(clippy::unwrap_used))]

pub mod audio;
pub mod kiosk;
pub mod profile;

use audio::NativeAudioEngine;
use kiosk::WindowEntry;
use profile::{ChildProfile, ProfileSettings, ProfileStore};
use std::sync::Mutex;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {name}! Welcome to Jimha!")
}

#[tauri::command]
fn kiosk_inhibit_shortcuts() -> Result<bool, String> {
    if cfg!(debug_assertions) {
        return Ok(false); // In dev mode, leave shortcuts intact for developer comfort
    }
    kiosk::ensure_kwin_shortcut_inhibition()
}

#[tauri::command]
fn audio_play_key(state: tauri::State<'_, NativeAudioEngine>, key: String) -> Result<(), String> {
    state.play_key(&key);
    Ok(())
}

#[tauri::command]
async fn kiosk_query_windows() -> Result<Vec<WindowEntry>, String> {
    kiosk::query_kwin_windows().await
}

#[tauri::command]
async fn kiosk_handover(target_id: Option<String>) -> Result<bool, String> {
    kiosk::execute_kwin_handover(target_id).await
}

#[tauri::command]
fn kiosk_minimize(window: tauri::Window) -> Result<(), String> {
    window
        .minimize()
        .map_err(|e| format!("Failed to minimize window: {e}"))
}

#[tauri::command]
fn kiosk_close(app: tauri::AppHandle, window: tauri::Window) -> Result<(), String> {
    let _ = window.close();
    app.exit(0);
    Ok(())
}

#[tauri::command]
fn profile_get(state: tauri::State<'_, Mutex<ProfileStore>>) -> Result<ChildProfile, String> {
    let store = state.lock().map_err(|e| e.to_string())?;
    Ok(store.profile().clone())
}

#[tauri::command]
fn profile_record_event(
    state: tauri::State<'_, Mutex<ProfileStore>>,
    event_type: String,
    key: Option<String>,
) -> Result<Option<String>, String> {
    let mut store = state.lock().map_err(|e| e.to_string())?;
    store.record_event(&event_type, key.as_deref())
}

#[tauri::command]
fn profile_save_settings(
    state: tauri::State<'_, Mutex<ProfileStore>>,
    settings: ProfileSettings,
) -> Result<ChildProfile, String> {
    let mut store = state.lock().map_err(|e| e.to_string())?;
    store.save_settings(settings)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let profile_path = profile::resolve_default_profile_path();
    let profile_store = ProfileStore::load_or_default(profile_path);

    tauri::Builder::default()
        .manage(Mutex::new(profile_store))
        .manage(NativeAudioEngine::new())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            audio_play_key,
            kiosk_inhibit_shortcuts,
            kiosk_query_windows,
            kiosk_handover,
            kiosk_minimize,
            kiosk_close,
            profile_get,
            profile_record_event,
            profile_save_settings
        ])
        .run(tauri::generate_context!())
        .expect("error while running Jimha application");
}

#[cfg(test)]
mod tests {
    use super::greet;

    #[test]
    fn test_greet() {
        assert_eq!(greet("Toddler"), "Hello, Toddler! Welcome to Jimha!");
    }

    #[test]
    fn test_brand_name() {
        let greeting = greet("World");
        assert!(greeting.contains("Jimha"));
        assert!(!greeting.contains("JimHa"));
    }
}
