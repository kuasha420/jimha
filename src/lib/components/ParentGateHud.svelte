<script lang="ts">
  interface Props {
    progress: number; // 0.0 to 1.0
    remainingSec: number;
  }

  let { progress = 0.0, remainingSec = 2.0 }: Props = $props();

  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  let strokeDashoffset = $derived(circumference * (1 - Math.max(0, Math.min(1, progress))));
  let formattedTime = $derived(`${Math.max(0, remainingSec).toFixed(1)}s`);
</script>

<div class="parent-gate-overlay" role="status" aria-live="polite">
  <div class="hud-card">
    <div class="hud-top-label">
      🎓 PARENT GATE: Unlocking Desktop Switch... ({formattedTime})
    </div>

    <div class="hud-dial">
      <svg class="progress-ring" width="120" height="120" viewBox="0 0 120 120">
        <!-- Background track -->
        <circle class="ring-bg" cx="60" cy="60" r={radius} stroke-width="8" />
        <!-- Progress arc in Gold (#FFD700) -->
        <circle
          class="ring-progress"
          cx="60"
          cy="60"
          r={radius}
          stroke-width="8"
          stroke-dasharray={circumference}
          stroke-dashoffset={strokeDashoffset}
        />
      </svg>
      <span class="hud-time">{formattedTime}</span>
    </div>

    <div class="hud-cancel-hint">Hold Alt+Tab 2.0s to switch • Release to cancel</div>
  </div>
</div>

<style>
  .parent-gate-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding-top: 10vh;
    z-index: 100;
  }

  .hud-card {
    background: rgba(10, 30, 20, 0.9);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 2px solid #00e676;
    border-radius: 24px;
    padding: 1.5rem 2.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    box-shadow: 0 12px 40px rgba(0, 230, 118, 0.25);
  }

  .hud-top-label {
    font-size: 1.1rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #00e676;
    text-transform: uppercase;
  }

  .hud-dial {
    position: relative;
    width: 120px;
    height: 120px;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .progress-ring {
    transform: rotate(-90deg);
  }

  .ring-bg {
    fill: none;
    stroke: rgba(30, 70, 50, 0.8);
  }

  .ring-progress {
    fill: none;
    stroke: #ffd700;
    stroke-linecap: round;
    transition: stroke-dashoffset 0.05s linear;
  }

  .hud-time {
    position: absolute;
    font-size: 1.5rem;
    font-weight: 800;
    color: #ffffff;
  }

  .hud-cancel-hint {
    font-size: 0.95rem;
    font-weight: 600;
    color: #a7ffeb;
  }
</style>
