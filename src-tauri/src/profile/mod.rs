use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ProfileSettings {
    pub esc_hold_seconds: f32,
    pub parent_gate_seconds: f32,
    pub audio_volume: f32,
    pub instrument: String,
}

impl Default for ProfileSettings {
    fn default() -> Self {
        Self {
            esc_hold_seconds: 2.5,
            parent_gate_seconds: 2.0,
            audio_volume: 0.8,
            instrument: "celesta".to_string(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ChildProfile {
    pub child_name: String,
    pub total_play_time_sec: u64,
    pub total_key_presses: u64,
    pub total_bubbles_popped: u64,
    pub unlocked_stickers: Vec<String>,
    pub settings: ProfileSettings,
}

impl Default for ChildProfile {
    fn default() -> Self {
        Self {
            child_name: "Jimha".to_string(),
            total_play_time_sec: 0,
            total_key_presses: 0,
            total_bubbles_popped: 0,
            unlocked_stickers: Vec::new(),
            settings: ProfileSettings::default(),
        }
    }
}

#[derive(Debug)]
pub struct ProfileStore {
    path: PathBuf,
    profile: ChildProfile,
}

impl ProfileStore {
    pub fn new(path: PathBuf, profile: ChildProfile) -> Self {
        Self { path, profile }
    }

    pub fn profile(&self) -> &ChildProfile {
        &self.profile
    }

    pub fn profile_mut(&mut self) -> &mut ChildProfile {
        &mut self.profile
    }

    pub fn load_or_default(path: PathBuf) -> Self {
        if path.exists() {
            match fs::read_to_string(&path) {
                Ok(content) => match serde_json::from_str::<ChildProfile>(&content) {
                    Ok(profile) => return Self { path, profile },
                    Err(err) => {
                        eprintln!("[JimhaProfile] Corrupted profile JSON: {err}. Re-initializing default.");
                    }
                },
                Err(err) => {
                    eprintln!(
                        "[JimhaProfile] Failed to read profile: {err}. Re-initializing default."
                    );
                }
            }
        }

        let store = Self {
            path,
            profile: ChildProfile::default(),
        };
        if let Err(err) = store.save() {
            eprintln!("[JimhaProfile] Warning: Failed to persist initial default profile: {err}");
        }
        store
    }

    pub fn save(&self) -> Result<(), String> {
        if let Some(parent) = self.path.parent() {
            if !parent.exists() {
                fs::create_dir_all(parent)
                    .map_err(|e| format!("Failed to create profile dir: {e}"))?;
            }
        }
        let json = serde_json::to_string_pretty(&self.profile)
            .map_err(|e| format!("Failed to serialize profile: {e}"))?;
        fs::write(&self.path, json).map_err(|e| format!("Failed to write profile: {e}"))?;
        Ok(())
    }

    pub fn save_settings(&mut self, settings: ProfileSettings) -> Result<ChildProfile, String> {
        self.profile.settings = settings;
        self.save()?;
        Ok(self.profile.clone())
    }

    pub fn record_event(
        &mut self,
        event_type: &str,
        key: Option<&str>,
    ) -> Result<Option<String>, String> {
        let mut newly_unlocked: Option<String> = None;

        match event_type {
            "key_press" => {
                self.profile.total_key_presses += 1;
            }
            "bubble_pop" => {
                self.profile.total_bubbles_popped += 1;
            }
            "play_time" => {
                self.profile.total_play_time_sec += 1;
            }
            _ => {}
        }

        // Check sticker unlock eligibility
        let mut try_unlock = |id: &str| {
            if !self.profile.unlocked_stickers.iter().any(|s| s == id) {
                self.profile.unlocked_stickers.push(id.to_string());
                if newly_unlocked.is_none() {
                    newly_unlocked = Some(id.to_string());
                }
            }
        };

        // 1. First spark
        if self.profile.total_key_presses >= 1 || self.profile.total_bubbles_popped >= 1 {
            try_unlock("first_spark");
        }

        // 2. Bubble master (10+ bubbles popped)
        if self.profile.total_bubbles_popped >= 10 {
            try_unlock("bubble_popper");
        }

        // 3. Konami champion
        if event_type == "konami" || key == Some("KONAMI") {
            try_unlock("konami_champion");
        }

        // 4. Melody maestro (50+ key presses or melody event)
        if self.profile.total_key_presses >= 50 || event_type == "melody" {
            try_unlock("melody_maestro");
        }

        // 5. Chord harmonizer (chord event, SPACE or ENTER)
        if event_type == "chord" || key == Some("SPACE") || key == Some("ENTER") {
            try_unlock("chord_harmonizer");
        }

        // 6. Lullaby listener (lullaby event or LULLABY key)
        if event_type == "lullaby" || key == Some("LULLABY") {
            try_unlock("lullaby_listener");
        }

        // Key-based achievements
        if let Some(k) = key {
            let upper = k.trim().to_uppercase();

            if upper == "SPACE" || upper == "ENTER" || k == " " {
                try_unlock("chord_harmonizer");
            }

            if upper == "LULLABY" {
                try_unlock("lullaby_listener");
            }

            // Queen Jimha ('J')
            if upper == "J" {
                try_unlock("jimha_crown");
            }

            // Jim Heart ('H')
            if upper == "H" {
                try_unlock("jim_heart");
            }

            // Star Counter (Numbers 0-9, 10, or digit key)
            if upper == "0" || upper == "10" || upper.chars().all(|c| c.is_ascii_digit()) {
                try_unlock("star_counter");
            }

            // Rainbow Explorer ('R' or color event)
            if upper == "R" {
                try_unlock("rainbow_explorer");
            }
        }

        if event_type == "color" {
            try_unlock("rainbow_explorer");
        }

        if event_type == "number" {
            try_unlock("star_counter");
        }

        if newly_unlocked.is_some() {
            self.save()?;
        }

        Ok(newly_unlocked)
    }
}

pub fn resolve_default_profile_path() -> PathBuf {
    if let Ok(xdg) = std::env::var("XDG_DATA_HOME") {
        if !xdg.is_empty() {
            return PathBuf::from(xdg).join("jimha").join("profile.json");
        }
    }
    #[cfg(target_os = "windows")]
    if let Ok(appdata) = std::env::var("APPDATA") {
        return PathBuf::from(appdata).join("jimha").join("profile.json");
    }
    #[cfg(target_os = "macos")]
    if let Ok(home) = std::env::var("HOME") {
        return PathBuf::from(home)
            .join("Library")
            .join("Application Support")
            .join("jimha")
            .join("profile.json");
    }
    if let Ok(home) = std::env::var("HOME") {
        return PathBuf::from(home)
            .join(".local")
            .join("share")
            .join("jimha")
            .join("profile.json");
    }
    PathBuf::from("profile.json")
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn temp_profile_path(name: &str) -> PathBuf {
        let mut path = std::env::temp_dir();
        path.push(format!("jimha_test_{}_{}.json", name, std::process::id()));
        path
    }

    #[test]
    fn test_default_profile() {
        let profile = ChildProfile::default();
        assert_eq!(profile.child_name, "Jimha");
        assert_eq!(profile.total_play_time_sec, 0);
        assert_eq!(profile.total_key_presses, 0);
        assert_eq!(profile.total_bubbles_popped, 0);
        assert_eq!(profile.unlocked_stickers, [] as [std::string::String; 0]);
        assert_eq!(profile.settings.instrument, "celesta");
        assert_eq!(profile.settings.esc_hold_seconds, 2.5);
        assert_eq!(profile.settings.audio_volume, 0.8);
    }

    #[test]
    fn test_load_non_existent_creates_default() {
        let path = temp_profile_path("create_default");
        let _ = fs::remove_file(&path);

        let store = ProfileStore::load_or_default(path.clone());
        assert_eq!(store.profile().child_name, "Jimha");
        assert!(path.exists());

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn test_corrupted_profile_recovery() {
        let path = temp_profile_path("corrupt_recovery");
        fs::write(&path, "NOT_JSON_AT_ALL!!!").unwrap();

        let store = ProfileStore::load_or_default(path.clone());
        assert_eq!(store.profile().child_name, "Jimha");

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn test_unlock_first_spark_and_crown() {
        let path = temp_profile_path("unlock_spark");
        let _ = fs::remove_file(&path);
        let mut store = ProfileStore::load_or_default(path.clone());

        let unlocked = store.record_event("key_press", Some("j")).unwrap();
        assert!(unlocked.is_some());
        assert!(store
            .profile()
            .unlocked_stickers
            .contains(&"first_spark".to_string()));
        assert!(store
            .profile()
            .unlocked_stickers
            .contains(&"jimha_crown".to_string()));

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn test_bubble_master_unlock() {
        let path = temp_profile_path("bubble_master");
        let _ = fs::remove_file(&path);
        let mut store = ProfileStore::load_or_default(path.clone());

        for _ in 0..9 {
            let _ = store.record_event("bubble_pop", None).unwrap();
        }
        assert!(!store
            .profile()
            .unlocked_stickers
            .contains(&"bubble_popper".to_string()));

        let unlocked_10th = store.record_event("bubble_pop", None).unwrap();
        assert_eq!(unlocked_10th, Some("bubble_popper".to_string()));
        assert!(store
            .profile()
            .unlocked_stickers
            .contains(&"bubble_popper".to_string()));

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn test_konami_and_special_keys() {
        let path = temp_profile_path("konami_test");
        let _ = fs::remove_file(&path);
        let mut store = ProfileStore::load_or_default(path.clone());

        store.record_event("key_press", Some("h")).unwrap();
        assert!(store
            .profile()
            .unlocked_stickers
            .contains(&"jim_heart".to_string()));

        store.record_event("key_press", Some("0")).unwrap();
        assert!(store
            .profile()
            .unlocked_stickers
            .contains(&"star_counter".to_string()));

        store.record_event("key_press", Some("r")).unwrap();
        assert!(store
            .profile()
            .unlocked_stickers
            .contains(&"rainbow_explorer".to_string()));

        store.record_event("konami", None).unwrap();
        assert!(store
            .profile()
            .unlocked_stickers
            .contains(&"konami_champion".to_string()));

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn test_musical_achievements() {
        let path = temp_profile_path("musical_test");
        let _ = fs::remove_file(&path);
        let mut store = ProfileStore::load_or_default(path.clone());

        // 1. Chord harmonizer via SPACE
        let unlocked_chord = store.record_event("key_press", Some("SPACE")).unwrap();
        assert_eq!(unlocked_chord, Some("first_spark".to_string()));
        assert!(store
            .profile()
            .unlocked_stickers
            .contains(&"chord_harmonizer".to_string()));

        // 2. Lullaby listener via lullaby event
        store.record_event("lullaby", Some("LULLABY")).unwrap();
        assert!(store
            .profile()
            .unlocked_stickers
            .contains(&"lullaby_listener".to_string()));

        // 3. Melody maestro via 50 key presses
        for _ in 0..48 {
            let _ = store.record_event("key_press", Some("a")).unwrap();
        }
        // At 49 key presses (1 initial SPACE + 48 = 49)
        assert!(!store
            .profile()
            .unlocked_stickers
            .contains(&"melody_maestro".to_string()));

        // 50th key press unlocks melody_maestro
        store.record_event("key_press", Some("b")).unwrap();
        assert!(store
            .profile()
            .unlocked_stickers
            .contains(&"melody_maestro".to_string()));

        let _ = fs::remove_file(&path);
    }
}
