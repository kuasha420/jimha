use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::sync::{Arc, Mutex};
use std::time::Duration;

/// Logical button identifiers for Jimha controllers.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum JimhaButton {
    A,
    B,
    X,
    Y,
    LB,
    RB,
    LT,
    RT,
    SELECT,
    START,
    L3,
    R3,
    UP,
    DOWN,
    LEFT,
    RIGHT,
    GUIDE,
}

impl JimhaButton {
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::A => "A",
            Self::B => "B",
            Self::X => "X",
            Self::Y => "Y",
            Self::LB => "LB",
            Self::RB => "RB",
            Self::LT => "LT",
            Self::RT => "RT",
            Self::SELECT => "SELECT",
            Self::START => "START",
            Self::L3 => "L3",
            Self::R3 => "R3",
            Self::UP => "UP",
            Self::DOWN => "DOWN",
            Self::LEFT => "LEFT",
            Self::RIGHT => "RIGHT",
            Self::GUIDE => "GUIDE",
        }
    }

    #[must_use]
    pub fn from_gilrs_button(btn: gilrs::Button) -> Option<Self> {
        match btn {
            gilrs::Button::South => Some(Self::A),
            gilrs::Button::East => Some(Self::B),
            gilrs::Button::West => Some(Self::X),
            gilrs::Button::North => Some(Self::Y),
            gilrs::Button::LeftTrigger => Some(Self::LB),
            gilrs::Button::RightTrigger => Some(Self::RB),
            gilrs::Button::LeftTrigger2 => Some(Self::LT),
            gilrs::Button::RightTrigger2 => Some(Self::RT),
            gilrs::Button::Select => Some(Self::SELECT),
            gilrs::Button::Start => Some(Self::START),
            gilrs::Button::LeftThumb => Some(Self::L3),
            gilrs::Button::RightThumb => Some(Self::R3),
            gilrs::Button::DPadUp => Some(Self::UP),
            gilrs::Button::DPadDown => Some(Self::DOWN),
            gilrs::Button::DPadLeft => Some(Self::LEFT),
            gilrs::Button::DPadRight => Some(Self::RIGHT),
            gilrs::Button::Mode => Some(Self::GUIDE),
            _ => None,
        }
    }
}

/// Tracks analog stick deflection and maps to virtual D-pad buttons
/// with 0.25 deadzone and 0.50 engagement hysteresis.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
#[allow(clippy::struct_excessive_bools)]
pub struct VirtualDpadState {
    pub up: bool,
    pub down: bool,
    pub left: bool,
    pub right: bool,
}

impl VirtualDpadState {
    #[must_use]
    pub const fn new() -> Self {
        Self {
            up: false,
            down: false,
            left: false,
            right: false,
        }
    }

    pub fn update_axis(&mut self, axis: gilrs::Axis, val: f32) -> Vec<(JimhaButton, bool)> {
        let mut events = Vec::new();
        match axis {
            gilrs::Axis::LeftStickX => {
                // Negative direction: LEFT
                if !self.left && val <= -0.5 {
                    self.left = true;
                    events.push((JimhaButton::LEFT, true));
                } else if self.left && val > -0.25 {
                    self.left = false;
                    events.push((JimhaButton::LEFT, false));
                }

                // Positive direction: RIGHT
                if !self.right && val >= 0.5 {
                    self.right = true;
                    events.push((JimhaButton::RIGHT, true));
                } else if self.right && val < 0.25 {
                    self.right = false;
                    events.push((JimhaButton::RIGHT, false));
                }
            }
            gilrs::Axis::LeftStickY => {
                // In gilrs, positive Y is UP, negative Y is DOWN.
                if !self.up && val >= 0.5 {
                    self.up = true;
                    events.push((JimhaButton::UP, true));
                } else if self.up && val < 0.25 {
                    self.up = false;
                    events.push((JimhaButton::UP, false));
                }

                if !self.down && val <= -0.5 {
                    self.down = true;
                    events.push((JimhaButton::DOWN, true));
                } else if self.down && val > -0.25 {
                    self.down = false;
                    events.push((JimhaButton::DOWN, false));
                }
            }
            _ => {}
        }
        events
    }

    pub fn release_all(&mut self) -> Vec<(JimhaButton, bool)> {
        let mut events = Vec::new();
        if self.up {
            self.up = false;
            events.push((JimhaButton::UP, false));
        }
        if self.down {
            self.down = false;
            events.push((JimhaButton::DOWN, false));
        }
        if self.left {
            self.left = false;
            events.push((JimhaButton::LEFT, false));
        }
        if self.right {
            self.right = false;
            events.push((JimhaButton::RIGHT, false));
        }
        events
    }
}

/// Composite multi-device gamepad state tracker with logical OR-gating.
/// Aggregates all connected controllers into a unified logical button state.
/// First controller to press a button emits down; releases only when all devices release it.
#[derive(Debug, Default)]
pub struct CompositeGamepadState {
    connected_gamepads: HashSet<usize>,
    device_buttons: HashMap<usize, HashSet<JimhaButton>>,
    device_dpads: HashMap<usize, VirtualDpadState>,
    global_pressed: HashSet<JimhaButton>,
}

impl CompositeGamepadState {
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    pub fn handle_connected_id(&mut self, id: usize) -> usize {
        self.connected_gamepads.insert(id);
        self.connected_gamepads.len()
    }

    pub fn handle_disconnected_id(&mut self, id: usize) -> (usize, Vec<JimhaButton>) {
        self.connected_gamepads.remove(&id);
        self.device_dpads.remove(&id);
        let held = self.device_buttons.remove(&id).unwrap_or_default();
        let mut released = Vec::new();
        for btn in held {
            let still_held = self.device_buttons.values().any(|set| set.contains(&btn));
            if !still_held && self.global_pressed.remove(&btn) {
                released.push(btn);
            }
        }
        (self.connected_gamepads.len(), released)
    }

    pub fn handle_button_press_id(
        &mut self,
        id: usize,
        button: JimhaButton,
    ) -> Option<JimhaButton> {
        self.connected_gamepads.insert(id);
        self.device_buttons.entry(id).or_default().insert(button);
        if self.global_pressed.insert(button) {
            Some(button)
        } else {
            None
        }
    }

    pub fn handle_button_release_id(
        &mut self,
        id: usize,
        button: JimhaButton,
    ) -> Option<JimhaButton> {
        if let Some(buttons) = self.device_buttons.get_mut(&id) {
            buttons.remove(&button);
        }
        let still_held = self
            .device_buttons
            .values()
            .any(|set| set.contains(&button));
        if !still_held && self.global_pressed.remove(&button) {
            Some(button)
        } else {
            None
        }
    }

    pub fn handle_axis_id(
        &mut self,
        id: usize,
        axis: gilrs::Axis,
        val: f32,
    ) -> Vec<(JimhaButton, bool)> {
        self.connected_gamepads.insert(id);
        let dpad = self.device_dpads.entry(id).or_default();
        let transitions = dpad.update_axis(axis, val);
        let mut emitted = Vec::new();
        for (btn, pressed) in transitions {
            if pressed {
                if let Some(b) = self.handle_button_press_id(id, btn) {
                    emitted.push((b, true));
                }
            } else if let Some(b) = self.handle_button_release_id(id, btn) {
                emitted.push((b, false));
            }
        }
        emitted
    }

    pub fn handle_connected(&mut self, id: gilrs::GamepadId) -> usize {
        self.handle_connected_id(id.into())
    }

    pub fn handle_disconnected(&mut self, id: gilrs::GamepadId) -> (usize, Vec<JimhaButton>) {
        self.handle_disconnected_id(id.into())
    }

    pub fn handle_button_press(
        &mut self,
        id: gilrs::GamepadId,
        button: JimhaButton,
    ) -> Option<JimhaButton> {
        self.handle_button_press_id(id.into(), button)
    }

    pub fn handle_button_release(
        &mut self,
        id: gilrs::GamepadId,
        button: JimhaButton,
    ) -> Option<JimhaButton> {
        self.handle_button_release_id(id.into(), button)
    }

    pub fn handle_axis(
        &mut self,
        id: gilrs::GamepadId,
        axis: gilrs::Axis,
        val: f32,
    ) -> Vec<(JimhaButton, bool)> {
        self.handle_axis_id(id.into(), axis, val)
    }

    pub fn reset_all(&mut self) -> Vec<JimhaButton> {
        let released: Vec<JimhaButton> = self.global_pressed.drain().collect();
        for buttons in self.device_buttons.values_mut() {
            buttons.clear();
        }
        for dpad in self.device_dpads.values_mut() {
            let _ = dpad.release_all();
        }
        released
    }

    #[must_use]
    pub fn connected_count(&self) -> usize {
        self.connected_gamepads.len()
    }

    #[must_use]
    pub fn is_button_pressed(&self, button: JimhaButton) -> bool {
        self.global_pressed.contains(&button)
    }

    #[must_use]
    pub fn snapshot(&self) -> GamepadStateSnapshot {
        let mut pressed_buttons: Vec<String> = self
            .global_pressed
            .iter()
            .map(|b| b.as_str().to_string())
            .collect();
        pressed_buttons.sort();
        GamepadStateSnapshot {
            connected_count: self.connected_gamepads.len(),
            pressed_buttons,
        }
    }
}

/// Tauri IPC push event payload streamed across `jimha://gamepad-event`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GamepadEventPayload {
    pub button: String,
    pub pressed: bool,
    pub value: f32,
    pub connected_count: usize,
}

/// Instantaneous state snapshot returned by `gamepad_get_state`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GamepadStateSnapshot {
    pub connected_count: usize,
    pub pressed_buttons: Vec<String>,
}

/// Sovereign Native Gamepad Engine managing low-level hardware controller I/O.
#[derive(Debug, Clone)]
pub struct NativeGamepadEngine {
    state: Arc<Mutex<CompositeGamepadState>>,
}

impl Default for NativeGamepadEngine {
    fn default() -> Self {
        Self {
            state: Arc::new(Mutex::new(CompositeGamepadState::new())),
        }
    }
}

impl NativeGamepadEngine {
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    pub fn start(app_handle: tauri::AppHandle) -> Self {
        use tauri::Emitter;

        let state = Arc::new(Mutex::new(CompositeGamepadState::new()));
        let thread_state = Arc::clone(&state);

        let _ = std::thread::Builder::new()
            .name("jimha-gamepad".to_string())
            .spawn(move || {
                let mut gilrs = match gilrs::Gilrs::new() {
                    Ok(g) => g,
                    Err(err) => {
                        eprintln!("[NativeGamepadEngine] Failed to initialize gilrs: {err}");
                        return;
                    }
                };

                // Seed initial connected devices
                if let Ok(mut lock) = thread_state.lock() {
                    for (id, _gp) in gilrs.gamepads() {
                        lock.handle_connected(id);
                    }
                }

                loop {
                    let first_event = gilrs.next_event_blocking(Some(Duration::from_millis(50)));
                    let mut events = Vec::new();
                    if let Some(ev) = first_event {
                        events.push(ev);
                    }
                    while let Some(ev) = gilrs.next_event() {
                        events.push(ev);
                    }

                    for gilrs::Event { id, event, .. } in events {
                        match event {
                            gilrs::EventType::ButtonPressed(btn, _) => {
                                if let Some(jimha_btn) = JimhaButton::from_gilrs_button(btn) {
                                    if let Ok(mut lock) = thread_state.lock() {
                                        if lock.handle_button_press(id, jimha_btn).is_some() {
                                            let count = lock.connected_count();
                                            let payload = GamepadEventPayload {
                                                button: jimha_btn.as_str().to_string(),
                                                pressed: true,
                                                value: 1.0,
                                                connected_count: count,
                                            };
                                            let _ =
                                                app_handle.emit("jimha://gamepad-event", payload);
                                        }
                                    }
                                }
                            }
                            gilrs::EventType::ButtonReleased(btn, _) => {
                                if let Some(jimha_btn) = JimhaButton::from_gilrs_button(btn) {
                                    if let Ok(mut lock) = thread_state.lock() {
                                        if lock.handle_button_release(id, jimha_btn).is_some() {
                                            let count = lock.connected_count();
                                            let payload = GamepadEventPayload {
                                                button: jimha_btn.as_str().to_string(),
                                                pressed: false,
                                                value: 0.0,
                                                connected_count: count,
                                            };
                                            let _ =
                                                app_handle.emit("jimha://gamepad-event", payload);
                                        }
                                    }
                                }
                            }
                            gilrs::EventType::AxisChanged(axis, val, _) => {
                                if let Ok(mut lock) = thread_state.lock() {
                                    let transitions = lock.handle_axis(id, axis, val);
                                    let count = lock.connected_count();
                                    for (btn, pressed) in transitions {
                                        let payload = GamepadEventPayload {
                                            button: btn.as_str().to_string(),
                                            pressed,
                                            value: if pressed { 1.0 } else { 0.0 },
                                            connected_count: count,
                                        };
                                        let _ = app_handle.emit("jimha://gamepad-event", payload);
                                    }
                                }
                            }
                            gilrs::EventType::Connected => {
                                if let Ok(mut lock) = thread_state.lock() {
                                    let count = lock.handle_connected(id);
                                    let payload = GamepadEventPayload {
                                        button: "CONNECT".to_string(),
                                        pressed: false,
                                        value: 0.0,
                                        connected_count: count,
                                    };
                                    let _ = app_handle.emit("jimha://gamepad-event", payload);
                                }
                            }
                            gilrs::EventType::Disconnected => {
                                if let Ok(mut lock) = thread_state.lock() {
                                    let (count, released) = lock.handle_disconnected(id);
                                    for btn in released {
                                        let payload = GamepadEventPayload {
                                            button: btn.as_str().to_string(),
                                            pressed: false,
                                            value: 0.0,
                                            connected_count: count,
                                        };
                                        let _ = app_handle.emit("jimha://gamepad-event", payload);
                                    }
                                    let payload = GamepadEventPayload {
                                        button: "DISCONNECT".to_string(),
                                        pressed: false,
                                        value: 0.0,
                                        connected_count: count,
                                    };
                                    let _ = app_handle.emit("jimha://gamepad-event", payload);
                                }
                            }
                            _ => {}
                        }
                    }
                }
            });

        Self { state }
    }

    pub fn get_state(&self) -> Result<GamepadStateSnapshot, String> {
        let lock = self.state.lock().map_err(|e| e.to_string())?;
        Ok(lock.snapshot())
    }

    pub fn reset_all(&self) -> Result<Vec<JimhaButton>, String> {
        let mut lock = self.state.lock().map_err(|e| e.to_string())?;
        Ok(lock.reset_all())
    }
}

#[tauri::command]
pub fn gamepad_get_state(
    state: tauri::State<'_, NativeGamepadEngine>,
) -> Result<GamepadStateSnapshot, String> {
    state.get_state()
}

#[tauri::command]
pub fn gamepad_reset_state(
    state: tauri::State<'_, NativeGamepadEngine>,
) -> Result<Vec<String>, String> {
    let released = state.reset_all()?;
    Ok(released
        .into_iter()
        .map(|b| b.as_str().to_string())
        .collect())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_button_mapping_and_string_representation() {
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::South),
            Some(JimhaButton::A)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::East),
            Some(JimhaButton::B)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::West),
            Some(JimhaButton::X)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::North),
            Some(JimhaButton::Y)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::LeftTrigger),
            Some(JimhaButton::LB)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::RightTrigger),
            Some(JimhaButton::RB)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::LeftTrigger2),
            Some(JimhaButton::LT)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::RightTrigger2),
            Some(JimhaButton::RT)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::Select),
            Some(JimhaButton::SELECT)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::Start),
            Some(JimhaButton::START)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::LeftThumb),
            Some(JimhaButton::L3)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::RightThumb),
            Some(JimhaButton::R3)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::DPadUp),
            Some(JimhaButton::UP)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::DPadDown),
            Some(JimhaButton::DOWN)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::DPadLeft),
            Some(JimhaButton::LEFT)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::DPadRight),
            Some(JimhaButton::RIGHT)
        );
        assert_eq!(
            JimhaButton::from_gilrs_button(gilrs::Button::Mode),
            Some(JimhaButton::GUIDE)
        );
        assert_eq!(JimhaButton::from_gilrs_button(gilrs::Button::C), None);
        assert_eq!(JimhaButton::from_gilrs_button(gilrs::Button::Z), None);

        assert_eq!(JimhaButton::A.as_str(), "A");
        assert_eq!(JimhaButton::SELECT.as_str(), "SELECT");
        assert_eq!(JimhaButton::START.as_str(), "START");
    }

    #[test]
    fn test_virtual_dpad_deadzone_and_hysteresis() {
        let mut dpad = VirtualDpadState::new();

        // 1. Minor drift below deadzone: 0.15 is ignored
        let evs = dpad.update_axis(gilrs::Axis::LeftStickX, 0.15);
        assert_eq!(evs, Vec::new());
        assert!(!dpad.right);

        // 2. Deflection below engagement threshold: 0.40 still not engaged
        let evs = dpad.update_axis(gilrs::Axis::LeftStickX, 0.40);
        assert_eq!(evs, Vec::new());
        assert!(!dpad.right);

        // 3. Deflection reaching 0.50 threshold: engages RIGHT
        let evs = dpad.update_axis(gilrs::Axis::LeftStickX, 0.60);
        assert_eq!(evs, vec![(JimhaButton::RIGHT, true)]);
        assert!(dpad.right);

        // 4. Stick relaxes to 0.35 (above 0.25 deadzone): hysteresis holds engagement
        let evs = dpad.update_axis(gilrs::Axis::LeftStickX, 0.35);
        assert_eq!(evs, Vec::new());
        assert!(dpad.right);

        // 5. Stick drops below deadzone: releases RIGHT
        let evs = dpad.update_axis(gilrs::Axis::LeftStickX, 0.10);
        assert_eq!(evs, vec![(JimhaButton::RIGHT, false)]);
        assert!(!dpad.right);

        // 6. Test negative X direction (LEFT)
        let evs = dpad.update_axis(gilrs::Axis::LeftStickX, -0.60);
        assert_eq!(evs, vec![(JimhaButton::LEFT, true)]);
        assert!(dpad.left);

        let evs = dpad.update_axis(gilrs::Axis::LeftStickX, -0.30);
        assert_eq!(evs, Vec::new());
        assert!(dpad.left);

        let evs = dpad.update_axis(gilrs::Axis::LeftStickX, -0.10);
        assert_eq!(evs, vec![(JimhaButton::LEFT, false)]);
        assert!(!dpad.left);

        // 7. Test Y direction (UP positive, DOWN negative in gilrs)
        let evs = dpad.update_axis(gilrs::Axis::LeftStickY, 0.70);
        assert_eq!(evs, vec![(JimhaButton::UP, true)]);
        assert!(dpad.up);

        let evs = dpad.update_axis(gilrs::Axis::LeftStickY, 0.0);
        assert_eq!(evs, vec![(JimhaButton::UP, false)]);
        assert!(!dpad.up);

        let evs = dpad.update_axis(gilrs::Axis::LeftStickY, -0.80);
        assert_eq!(evs, vec![(JimhaButton::DOWN, true)]);
        assert!(dpad.down);

        let evs = dpad.update_axis(gilrs::Axis::LeftStickY, -0.10);
        assert_eq!(evs, vec![(JimhaButton::DOWN, false)]);
        assert!(!dpad.down);
    }

    #[test]
    fn test_composite_state_multi_device_or_gating() {
        let mut composite = CompositeGamepadState::new();

        // Connect 2 controllers (e.g. Physical Deck + Steam Input virtual)
        assert_eq!(composite.handle_connected_id(0), 1);
        assert_eq!(composite.handle_connected_id(1), 2);

        // Device 0 presses A -> emits press
        let ev = composite.handle_button_press_id(0, JimhaButton::A);
        assert_eq!(ev, Some(JimhaButton::A));
        assert!(composite.is_button_pressed(JimhaButton::A));

        // Device 1 also presses A -> deduplicated, no emit
        let ev = composite.handle_button_press_id(1, JimhaButton::A);
        assert_eq!(ev, None);
        assert!(composite.is_button_pressed(JimhaButton::A));

        // Device 0 releases A -> Device 1 is still holding A, so composite state still holds A!
        let ev = composite.handle_button_release_id(0, JimhaButton::A);
        assert_eq!(ev, None);
        assert!(composite.is_button_pressed(JimhaButton::A));

        // Device 1 releases A -> now no devices are holding A, emits release!
        let ev = composite.handle_button_release_id(1, JimhaButton::A);
        assert_eq!(ev, Some(JimhaButton::A));
        assert!(!composite.is_button_pressed(JimhaButton::A));
    }

    #[test]
    fn test_composite_state_disconnection_cleanup() {
        let mut composite = CompositeGamepadState::new();
        composite.handle_connected_id(0);
        composite.handle_connected_id(1);

        // Device 0 holds A and B
        composite.handle_button_press_id(0, JimhaButton::A);
        composite.handle_button_press_id(0, JimhaButton::B);

        // Device 1 holds B and X
        composite.handle_button_press_id(1, JimhaButton::B);
        composite.handle_button_press_id(1, JimhaButton::X);

        assert!(composite.is_button_pressed(JimhaButton::A));
        assert!(composite.is_button_pressed(JimhaButton::B));
        assert!(composite.is_button_pressed(JimhaButton::X));

        // Device 0 disconnects abruptly
        let (remaining_count, released) = composite.handle_disconnected_id(0);
        assert_eq!(remaining_count, 1);

        // A was only held by Device 0, so it must be released
        assert_eq!(released, vec![JimhaButton::A]);
        assert!(!composite.is_button_pressed(JimhaButton::A));

        // B is still held by Device 1
        assert!(composite.is_button_pressed(JimhaButton::B));
        // X is still held by Device 1
        assert!(composite.is_button_pressed(JimhaButton::X));
    }

    #[test]
    fn test_composite_state_reset_all() {
        let mut composite = CompositeGamepadState::new();
        composite.handle_connected_id(0);
        composite.handle_button_press_id(0, JimhaButton::SELECT);
        composite.handle_button_press_id(0, JimhaButton::START);

        assert_eq!(composite.snapshot().pressed_buttons.len(), 2);

        let released = composite.reset_all();
        assert_eq!(released.len(), 2);
        assert_eq!(composite.snapshot().pressed_buttons, Vec::<String>::new());
    }
}
