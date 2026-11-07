// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! Welcome to Jimha!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet])
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
