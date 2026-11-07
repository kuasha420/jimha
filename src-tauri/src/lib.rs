pub mod kiosk;

use kiosk::WindowEntry;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! Welcome to Jimha!", name)
}

#[tauri::command]
fn kiosk_inhibit_shortcuts() -> Result<bool, String> {
    kiosk::ensure_kwin_shortcut_inhibition()
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
    window.minimize().map_err(|e| format!("Failed to minimize window: {}", e))
}

#[tauri::command]
fn kiosk_close(window: tauri::Window) -> Result<(), String> {
    window.close().map_err(|e| format!("Failed to close window: {}", e))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            kiosk_inhibit_shortcuts,
            kiosk_query_windows,
            kiosk_handover,
            kiosk_minimize,
            kiosk_close
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
