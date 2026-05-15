import pygame
import numpy as np
import config


PREVIEW_W = 320
PREVIEW_H = 240


class CockpitUI:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.Font(None, 64)
        self.body_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)

    def render(self, mode, shared_state, state_text="", calibration=None, show_help=False):
        self._render_main(mode, state_text)
        self._render_climate(mode)
        self._render_preview(shared_state)
        self._render_hint()
        if calibration is not None:
            self._render_calibration(calibration)
        if show_help:
            self._render_help()

    def _render_main(self, mode, state_text):
        # Mode name
        title_surf = self.title_font.render(
            mode.display_name, True, (255, 255, 255)
        )
        title_rect = title_surf.get_rect(
            center=(config.WINDOW_WIDTH // 2, 60)
        )
        self.screen.blit(title_surf, title_rect)

        # Light color label
        light_text = f"Ambient: {mode.ambient_color_name}"
        light_surf = self.body_font.render(light_text, True, (200, 200, 200))
        light_rect = light_surf.get_rect(
            center=(config.WINDOW_WIDTH // 2, 130)
        )
        self.screen.blit(light_surf, light_rect)

        # State indicator
        if state_text:
            surf = self.body_font.render(state_text, True, (255, 255, 100))
            rect = surf.get_rect(center=(config.WINDOW_WIDTH // 2, 600))
            self.screen.blit(surf, rect)

    def _render_climate(self, mode):
        y = 180
        for label, value in [
            ("Temperature", f"{mode.ac_temperature} C"),
            ("Fan Speed", mode.ac_fan_speed),
            ("Air Direction", mode.ac_direction),
        ]:
            text = f"{label}: {value}"
            surf = self.body_font.render(text, True, (200, 220, 255))
            rect = surf.get_rect(center=(config.WINDOW_WIDTH // 2, y))
            self.screen.blit(surf, rect)
            y += 35

    def _render_preview(self, shared):
        frame = shared.camera_frame
        mar = shared.debug_mar

        # Border rect (bottom-left corner)
        px, py = 10, config.WINDOW_HEIGHT - PREVIEW_H - 10
        pygame.draw.rect(self.screen, (60, 60, 80),
                         (px - 2, py - 2, PREVIEW_W + 4, PREVIEW_H + 4), 2)

        if frame is not None:
            try:
                small = np.array(frame[..., :3])
                surface = pygame.surfarray.make_surface(
                    np.transpose(small, (1, 0, 2))
                )
                surface = pygame.transform.scale(surface, (PREVIEW_W, PREVIEW_H))
                self.screen.blit(surface, (px, py))
            except Exception as e:
                print(f"[UI] Camera preview render failed: {e}",
                      file=__import__('sys').stderr)

        # MAR overlay on preview
        thr = config.MAR_THRESHOLD
        color = (0, 255, 0) if mar < thr else (255, 80, 0)
        mar_text = f"MAR: {mar:.3f} / Thr: {thr:.3f}"
        surf = self.small_font.render(mar_text, True, color)
        self.screen.blit(surf, (px + 6, py + 6))

        # Face status
        face_text = "Face: OK" if shared.face_detected else "Face: --"
        fs = self.small_font.render(face_text, True, (180, 180, 180))
        self.screen.blit(fs, (px + 6, py + PREVIEW_H - 44))

        # Mic level meter
        mic = shared.mic_level
        mic_color = (0, 255, 0) if mic > 0.01 else (100, 100, 100)
        mic_text = f"Mic: {mic:.4f}"
        ms = self.small_font.render(mic_text, True, mic_color)
        self.screen.blit(ms, (px + 6, py + PREVIEW_H - 24))

    def _render_hint(self):
        surf = self.small_font.render(
            "[1] Dynamic  [2] Rest  [Y] Yawn  [C] Calib  [D] Log  [H] Help  [Esc] Quit",
            True, (130, 130, 130)
        )
        rect = surf.get_rect(center=(config.WINDOW_WIDTH // 2, 680))
        self.screen.blit(surf, rect)

    def _render_calibration(self, cal):
        """Show calibration phase and countdown in the center-right area."""
        if cal.state == cal.PHASE_IDLE:
            return
        if cal.state == cal.PHASE_DONE:
            text = (
                f"Calibration complete — "
                f"Baseline: {cal.mar_baseline:.3f}  "
                f"Peak: {cal.mar_yawn_peak:.3f}  "
                f"Threshold: {cal.computed_threshold:.3f}"
            )
            color = (100, 255, 100)
        elif cal.state == cal.PHASE_NEUTRAL:
            text = f"Phase 1/2: Keep a neutral face... {cal.countdown:.0f}s"
            color = (255, 255, 100)
        else:
            text = f"Phase 2/2: Do one yawn now! {cal.countdown:.0f}s"
            color = (255, 200, 50)
        surf = self.body_font.render(text, True, color)
        rect = surf.get_rect(center=(config.WINDOW_WIDTH // 2, 560))
        self.screen.blit(surf, rect)

    def _render_help(self):
        """Semi-transparent overlay with all keyboard controls."""
        # Dark backdrop
        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((10, 10, 20))
        self.screen.blit(overlay, (0, 0))

        shortcuts = [
            ("Mode Control", ""),
            ("  1", "Switch to Dynamic Mode"),
            ("  2", "Switch to Rest Mode"),
            ("", ""),
            ("Perception", ""),
            ("  Y / Z", "Mock a yawn (for testing)"),
            ("  C", "Calibrate personal MAR threshold (30s)"),
            ("", ""),
            ("Data & Config", ""),
            ("  D", "Toggle CSV data logging (logs/session_*.csv)"),
            ("  F5", "Hot-reload config.json at runtime"),
            ("", ""),
            ("General", ""),
            ("  H", "Toggle this help screen"),
            ("  Esc", "Quit"),
        ]

        x = config.WINDOW_WIDTH // 2 - 180
        y = 80
        title = self.body_font.render("Keyboard Shortcuts", True, (255, 255, 100))
        self.screen.blit(title, (x, y))
        y += 40

        for key, desc in shortcuts:
            if not desc:
                y += 12
                continue
            color = (200, 200, 200) if key else (120, 180, 255)
            line = self.small_font.render(
                f"{key:<6}  {desc}" if key else f"  {desc}",
                True, color,
            )
            self.screen.blit(line, (x, y))
            y += 22
