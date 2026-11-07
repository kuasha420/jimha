use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;
use std::process::Command;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct WindowEntry {
    pub id: String,
    pub title: String,
    pub icon: String,
}

/// Locate a binary on system PATH without invoking subshells.
pub fn find_binary(name: &str) -> Option<PathBuf> {
    if let Ok(path_var) = std::env::var("PATH") {
        for dir in std::env::split_paths(&path_var) {
            let full_path = dir.join(name);
            if full_path.is_file() {
                return Some(full_path);
            }
        }
    }
    None
}

/// Get the available qdbus executable path (qdbus6 or qdbus).
pub fn find_qdbus() -> Option<PathBuf> {
    find_binary("qdbus6").or_else(|| find_binary("qdbus"))
}

/// Extract UUID from a string if present (e.g. {12345678-1234-1234-1234-123456789abc})
pub fn extract_uuid(input: &str) -> Option<String> {
    let bytes = input.as_bytes();
    if bytes.len() < 36 {
        return None;
    }
    for i in 0..=(bytes.len() - 36) {
        let slice = &bytes[i..i + 36];
        let is_uuid = slice[8] == b'-'
            && slice[13] == b'-'
            && slice[18] == b'-'
            && slice[23] == b'-'
            && slice.iter().enumerate().all(|(idx, &b)| {
                if idx == 8 || idx == 13 || idx == 18 || idx == 23 {
                    true
                } else {
                    b.is_ascii_hexdigit()
                }
            });
        if is_uuid {
            return std::str::from_utf8(slice).ok().map(|s| s.to_string());
        }
    }
    None
}

/// Synthesize transient KWin ECMAScript for authoritative window handover.
/// Note: Window matching strictly targets Jimha's own window class and exact caption,
/// preventing accidental minimization of editors, browsers, or other tasks with "jimha" in title.
pub fn synthesize_kwin_handover_script(target_match_id: Option<&str>) -> (String, String) {
    let clean_target = match target_match_id {
        Some("desktop") => "desktop".to_string(),
        Some(raw) => {
            if let Some(uuid) = extract_uuid(raw) {
                uuid.to_lowercase()
            } else {
                raw.trim().to_string()
            }
        }
        None => String::new(),
    };

    let target_json = serde_json::to_string(&clean_target).unwrap_or_else(|_| "\"\"".to_string());

    let script = format!(
        r#"var wins = workspace.windowList();
for (var i = 0; i < wins.length; i++) {{
    var w = wins[i];
    if (w.resourceClass === "jimha" || w.caption === "Jimha" || (w.caption && w.caption.indexOf("JimHa's Magical Key Smash Game") !== -1)) {{
        w.minimized = true;
    }}
}}
var target = {};
if (target === "desktop") {{
    workspace.slotToggleShowDesktop();
}} else if (target) {{
    for (var i = 0; i < wins.length; i++) {{
        var w = wins[i];
        var wid = (w.internalId || w.uuid || "").toString().toLowerCase();
        if (wid && wid.indexOf(target) !== -1) {{
            w.minimized = false;
            workspace.activeWindow = w;
            workspace.raiseWindow(w);
            break;
        }}
    }}
}} else {{
    var stack = workspace.stackingOrder;
    for (var i = stack.length - 1; i >= 0; i--) {{
        var sw = stack[i];
        if (sw.resourceClass !== "jimha" && !sw.minimized && sw.normalWindow) {{
            workspace.activeWindow = sw;
            workspace.raiseWindow(sw);
            break;
        }}
    }}
}}
"#,
        target_json
    );

    (clean_target, script)
}

/// Extract a single quoted string handling escaped quotes (\").
fn extract_quoted_string(input: &str) -> Option<(String, String)> {
    let start_quote = input.find('"')?;
    let content_start = start_quote + 1;
    let mut escaped = false;
    let mut end_quote = None;

    for (idx, ch) in input[content_start..].char_indices() {
        if escaped {
            escaped = false;
        } else if ch == '\\' {
            escaped = true;
        } else if ch == '"' {
            end_quote = Some(content_start + idx);
            break;
        }
    }

    let end = end_quote?;
    let raw = &input[content_start..end];
    let remainder = &input[end + 1..];
    let unescaped = raw.replace(r#"\""#, "\"").replace(r#"\\"#, "\\");
    Some((unescaped, remainder.to_string()))
}

/// Robust parsing of QDBus WindowsRunner Match output:
/// [Argument: (sssida{sv}) "id", "title", "icon", ...]
pub fn parse_qdbus_matches(text: &str) -> Vec<(String, String, String)> {
    let mut results = Vec::new();
    for block in text.split("[Argument:") {
        if block.trim().is_empty() {
            continue;
        }
        if let Some(close_paren) = block.find(')') {
            let after = &block[close_paren + 1..];
            if let Some((id, rem1)) = extract_quoted_string(after) {
                if let Some((title, rem2)) = extract_quoted_string(&rem1) {
                    if let Some((icon, _)) = extract_quoted_string(&rem2) {
                        results.push((id, title, icon));
                    }
                }
            }
        }
    }
    results
}

/// Encode arbitrary bytes into standard base64 string.
pub fn encode_base64(bytes: &[u8]) -> String {
    const CHARSET: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity(bytes.len().div_ceil(3) * 4);
    for chunk in bytes.chunks(3) {
        let b0 = chunk[0] as usize;
        let b1 = chunk.get(1).map(|&b| b as usize).unwrap_or(0);
        let b2 = chunk.get(2).map(|&b| b as usize).unwrap_or(0);
        let triple = (b0 << 16) | (b1 << 8) | b2;
        out.push(CHARSET[(triple >> 18) & 0x3f] as char);
        out.push(CHARSET[(triple >> 12) & 0x3f] as char);
        if chunk.len() > 1 {
            out.push(CHARSET[(triple >> 6) & 0x3f] as char);
        } else {
            out.push('=');
        }
        if chunk.len() > 2 {
            out.push(CHARSET[triple & 0x3f] as char);
        } else {
            out.push('=');
        }
    }
    out
}

/// Locate a system application icon and convert it to a base64 Data URL.
pub fn resolve_icon_data_url(icon_name: &str) -> Option<String> {
    if icon_name.trim().is_empty() {
        return None;
    }
    let clean = icon_name.trim();

    let search_roots = [
        "/usr/share/icons/hicolor/128x128/apps",
        "/usr/share/icons/hicolor/64x64/apps",
        "/usr/share/icons/hicolor/48x48/apps",
        "/usr/share/icons/hicolor/32x32/apps",
        "/usr/share/icons/hicolor/scalable/apps",
        "/usr/share/pixmaps",
        "/usr/share/icons/breeze/apps/48",
    ];

    for root in search_roots {
        let dir = PathBuf::from(root);
        let png = dir.join(format!("{}.png", clean));
        if png.is_file() {
            if let Ok(bytes) = fs::read(&png) {
                return Some(format!("data:image/png;base64,{}", encode_base64(&bytes)));
            }
        }
        let svg = dir.join(format!("{}.svg", clean));
        if svg.is_file() {
            if let Ok(bytes) = fs::read(&svg) {
                return Some(format!(
                    "data:image/svg+xml;base64,{}",
                    encode_base64(&bytes)
                ));
            }
        }
    }
    None
}

/// Filter raw window matches to remove Jimha itself and empty entries.
pub fn filter_window_matches(raw: Vec<(String, String, String)>) -> Vec<WindowEntry> {
    let mut windows = Vec::new();
    let mut seen = HashSet::new();

    for (id, title, icon) in raw {
        let id_clean = id.trim().to_string();
        let title_clean = title.trim().to_string();
        let icon_clean = icon.trim().to_string();

        if id_clean.is_empty() || seen.contains(&id_clean) {
            continue;
        }

        if title_clean.is_empty()
            || title_clean.starts_with("JimHa's Magical Key Smash Game")
            || title_clean == "Jimha"
        {
            continue;
        }

        let resolved_icon = resolve_icon_data_url(&icon_clean).unwrap_or(icon_clean);

        seen.insert(id_clean.clone());
        windows.push(WindowEntry {
            id: id_clean,
            title: title_clean,
            icon: resolved_icon,
        });
    }

    if windows.is_empty() {
        windows.push(WindowEntry {
            id: "desktop".to_string(),
            title: "Desktop / Workspace".to_string(),
            icon: "user-desktop".to_string(),
        });
    }

    windows
}

/// Check and configure KWin shortcut inhibition rule under KDE Plasma.
pub fn ensure_kwin_shortcut_inhibition() -> Result<bool, String> {
    let kread_path = match find_binary("kreadconfig6") {
        Some(p) => p,
        None => return Ok(false), // Graceful non-KDE fallback
    };
    let kwrite_path = match find_binary("kwriteconfig6") {
        Some(p) => p,
        None => return Ok(false),
    };

    let read_res = Command::new(&kread_path)
        .args([
            "--file",
            "kwinrulesrc",
            "--group",
            "General",
            "--key",
            "rules",
        ])
        .output()
        .map_err(|e| format!("Failed to execute kreadconfig6: {}", e))?;

    let current_rules = if read_res.status.success() {
        String::from_utf8_lossy(&read_res.stdout).trim().to_string()
    } else {
        String::new()
    };

    let mut rules: Vec<String> = current_rules
        .split(',')
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();

    if !rules.contains(&"jimha_lockdown".to_string()) {
        rules.push("jimha_lockdown".to_string());
        let new_rules = rules.join(",");
        let count_str = rules.len().to_string();

        let w1 = Command::new(&kwrite_path)
            .args([
                "--file",
                "kwinrulesrc",
                "--group",
                "General",
                "--key",
                "rules",
                &new_rules,
            ])
            .output()
            .map_err(|e| format!("Failed to write kwinrulesrc rules list: {}", e))?;
        if !w1.status.success() {
            return Err(format!(
                "kwriteconfig6 rules error: {}",
                String::from_utf8_lossy(&w1.stderr)
            ));
        }

        let w2 = Command::new(&kwrite_path)
            .args([
                "--file",
                "kwinrulesrc",
                "--group",
                "General",
                "--key",
                "count",
                &count_str,
            ])
            .output()
            .map_err(|e| format!("Failed to write kwinrulesrc count: {}", e))?;
        if !w2.status.success() {
            return Err(format!(
                "kwriteconfig6 count error: {}",
                String::from_utf8_lossy(&w2.stderr)
            ));
        }

        let props = [
            ("description", "Jimha Toddler Game Lockdown"),
            ("wmclass", "jimha"),
            ("wmclassmatch", "1"),
            ("types", "1"),
            ("disableglobalshortcuts", "true"),
            ("disableglobalshortcutsrule", "2"),
        ];

        for (k, v) in props {
            let wp = Command::new(&kwrite_path)
                .args([
                    "--file",
                    "kwinrulesrc",
                    "--group",
                    "jimha_lockdown",
                    "--key",
                    k,
                    v,
                ])
                .output()
                .map_err(|e| format!("Failed to write rule property {}: {}", k, e))?;
            if !wp.status.success() {
                return Err(format!(
                    "kwriteconfig6 property {} error: {}",
                    k,
                    String::from_utf8_lossy(&wp.stderr)
                ));
            }
        }

        // Notify KWin to reload rules
        if let Some(qdbus_bin) = find_qdbus() {
            let q_res = Command::new(qdbus_bin)
                .args(["org.kde.KWin", "/KWin", "reconfigure"])
                .output()
                .map_err(|e| format!("Failed to reconfigure KWin via D-Bus: {}", e))?;
            if !q_res.status.success() {
                return Err(format!(
                    "KWin reconfigure error: {}",
                    String::from_utf8_lossy(&q_res.stderr)
                ));
            }
        }
    }

    Ok(true)
}

/// Query active windows from KWin via D-Bus / qdbus.
pub async fn query_kwin_windows() -> Result<Vec<WindowEntry>, String> {
    let qdbus_cmd = match find_qdbus() {
        Some(p) => p,
        None => return Ok(filter_window_matches(Vec::new())), // Fallback to desktop
    };

    let output = Command::new(qdbus_cmd)
        .args([
            "--literal",
            "org.kde.KWin",
            "/WindowsRunner",
            "org.kde.krunner1.Match",
            "",
        ])
        .output()
        .map_err(|e| format!("Failed to execute qdbus WindowsRunner: {}", e))?;

    if !output.status.success() {
        return Ok(filter_window_matches(Vec::new()));
    }

    let text = String::from_utf8_lossy(&output.stdout);
    let raw = parse_qdbus_matches(&text);
    Ok(filter_window_matches(raw))
}

/// Execute transient KWin script to minimize Jimha and raise target.
pub async fn execute_kwin_handover(target_match_id: Option<String>) -> Result<bool, String> {
    let qdbus_cmd = match find_qdbus() {
        Some(p) => p,
        None => return Err("Neither qdbus nor qdbus6 binary found on PATH".to_string()),
    };

    let (_clean_target, script_content) =
        synthesize_kwin_handover_script(target_match_id.as_deref());

    let temp_dir = std::env::temp_dir();
    let temp_file = temp_dir.join(format!("jimha_handover_{}.js", std::process::id()));

    fs::write(&temp_file, &script_content).map_err(|e| {
        format!(
            "Failed to write transient KWin script {}: {}",
            temp_file.display(),
            e
        )
    })?;

    let plugin_name = "jimha_handover";

    // Best-effort unload
    let _ = Command::new(&qdbus_cmd)
        .args([
            "org.kde.KWin",
            "/Scripting",
            "org.kde.kwin.Scripting.unloadScript",
            plugin_name,
        ])
        .output();

    let load_res = Command::new(&qdbus_cmd)
        .args([
            "org.kde.KWin",
            "/Scripting",
            "org.kde.kwin.Scripting.loadScript",
            temp_file.to_string_lossy().as_ref(),
            plugin_name,
        ])
        .output()
        .map_err(|e| {
            let _ = fs::remove_file(&temp_file);
            format!("Failed to load KWin handover script via D-Bus: {}", e)
        })?;

    if !load_res.status.success() {
        let _ = fs::remove_file(&temp_file);
        return Err(format!(
            "KWin loadScript failed (exit code {:?}): {}",
            load_res.status.code(),
            String::from_utf8_lossy(&load_res.stderr).trim()
        ));
    }

    let stdout_str = String::from_utf8_lossy(&load_res.stdout);
    let num_str = stdout_str
        .split_whitespace()
        .find(|w| w.chars().all(|c| c.is_ascii_digit()))
        .ok_or_else(|| {
            let _ = fs::remove_file(&temp_file);
            format!(
                "KWin loadScript returned invalid script ID: {}",
                stdout_str.trim()
            )
        })?;

    let run_res = Command::new(&qdbus_cmd)
        .args([
            "org.kde.KWin",
            &format!("/Scripting/Script{}", num_str),
            "org.kde.kwin.Script.run",
        ])
        .output()
        .map_err(|e| {
            let _ = fs::remove_file(&temp_file);
            format!("Failed to run KWin handover script: {}", e)
        })?;

    let run_success = run_res.status.success();
    let run_stderr = String::from_utf8_lossy(&run_res.stderr).trim().to_string();

    // Cleanup
    let _ = Command::new(&qdbus_cmd)
        .args([
            "org.kde.KWin",
            "/Scripting",
            "org.kde.kwin.Scripting.unloadScript",
            plugin_name,
        ])
        .output();
    let _ = fs::remove_file(&temp_file);

    if !run_success {
        return Err(format!("KWin Script.run failed: {}", run_stderr));
    }

    Ok(true)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_uuid() {
        let input = "windows runner {12345678-abcd-ef01-2345-6789abcdef01} item";
        assert_eq!(
            extract_uuid(input),
            Some("12345678-abcd-ef01-2345-6789abcdef01".to_string())
        );
        assert_eq!(extract_uuid("no uuid here"), None);
    }

    #[test]
    fn test_synthesize_handover_script_desktop() {
        let (target, script) = synthesize_kwin_handover_script(Some("desktop"));
        assert_eq!(target, "desktop");
        assert!(script.contains("workspace.slotToggleShowDesktop()"));
        assert!(script.contains("w.resourceClass === \"jimha\""));
        assert!(script.contains("w.caption === \"Jimha\""));
        assert!(!script.contains("indexOf(\"Jimha\")"));
        assert!(script.contains("w.minimized = true;"));
    }

    #[test]
    fn test_synthesize_handover_script_target_window() {
        let (target, script) =
            synthesize_kwin_handover_script(Some("{AABBCCDD-1122-3344-5566-778899AABBCC}"));
        assert_eq!(target, "aabbccdd-1122-3344-5566-778899aabbcc");
        assert!(script.contains("workspace.raiseWindow(w);"));
        assert!(script.contains("w.minimized = false;"));
    }

    #[test]
    fn test_synthesize_handover_script_none() {
        let (target, script) = synthesize_kwin_handover_script(None);
        assert_eq!(target, "");
        assert!(script.contains("workspace.stackingOrder"));
        assert!(script.contains("sw.resourceClass !== \"jimha\""));
    }

    #[test]
    fn test_parse_qdbus_matches_with_quotes() {
        let sample = r#"[Argument: (sssida{sv}) "id-1", "Code - \"Project Jimha\"", "code", 100, 1.0, [Argument: a{sv} {}]], [Argument: (sssida{sv}) "id-2", "Web Browser", "browser", 100, 1.0, [Argument: a{sv} {}]]"#;
        let parsed = parse_qdbus_matches(sample);
        assert_eq!(parsed.len(), 2);
        assert_eq!(parsed[0].0, "id-1");
        assert_eq!(parsed[0].1, "Code - \"Project Jimha\"");
        assert_eq!(parsed[0].2, "code");
        assert_eq!(parsed[1].1, "Web Browser");
    }

    #[test]
    fn test_filter_window_matches() {
        let raw = vec![
            (
                "uuid-1".to_string(),
                "Jimha".to_string(),
                "jimha".to_string(),
            ),
            (
                "uuid-2".to_string(),
                "Firefox".to_string(),
                "firefox".to_string(),
            ),
            ("uuid-3".to_string(), "".to_string(), "unknown".to_string()),
            (
                "uuid-2".to_string(),
                "Firefox Duplicate".to_string(),
                "firefox".to_string(),
            ),
            (
                "uuid-4".to_string(),
                "VS Code - Jimha Project".to_string(),
                "code".to_string(),
            ),
        ];

        let filtered = filter_window_matches(raw);
        assert_eq!(filtered.len(), 2);
        assert_eq!(filtered[0].title, "Firefox");
        // Non-Jimha exact match window (e.g. IDE editing Jimha) is preserved!
        assert_eq!(filtered[1].title, "VS Code - Jimha Project");
    }

    #[test]
    fn test_filter_window_matches_fallback_desktop() {
        let raw = vec![(
            "uuid-1".to_string(),
            "Jimha".to_string(),
            "jimha".to_string(),
        )];
        let filtered = filter_window_matches(raw);
        assert_eq!(filtered.len(), 1);
        assert_eq!(filtered[0].id, "desktop");
        assert_eq!(filtered[0].title, "Desktop / Workspace");
    }

    #[test]
    fn test_find_binary_path() {
        // Standard system binaries should resolve or return None gracefully
        let sh = find_binary("sh");
        assert!(sh.is_some());
        let none = find_binary("nonexistent_binary_xyz123");
        assert_eq!(none, None);
    }

    #[test]
    fn test_encode_base64() {
        assert_eq!(encode_base64(b""), "");
        assert_eq!(encode_base64(b"f"), "Zg==");
        assert_eq!(encode_base64(b"fo"), "Zm8=");
        assert_eq!(encode_base64(b"foo"), "Zm9v");
        assert_eq!(encode_base64(b"Jimha"), "SmltaGE=");
    }

    #[test]
    fn test_resolve_icon_data_url() {
        assert_eq!(resolve_icon_data_url(""), None);
        assert_eq!(resolve_icon_data_url("nonexistent_icon_12345"), None);
    }
}
