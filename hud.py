import pygame

SLIDERS = [
    ("max_speed",          "MAX SPD",   100, 800),
    ("acceleration_force", "ACCEL",      50, 500),
    ("brake_force",        "BRAKE",      50, 500),
    ("turn_speed",         "TURN",       50, 600),
    ("side_friction",      "FRICTION", 0.1, 2.0),
]


def _fmt_time(seconds):
    if seconds is None:
        return "--:--.--"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"


class HUD:
    PADDING = 12
    LINE_HEIGHT = 26
    VALUE_X = 100

    def __init__(self):
        self.level = 0
        self.font = pygame.font.SysFont("menlo", 22)
        self.font_label = pygame.font.SysFont("menlo", 17)
        self.font_btn = pygame.font.SysFont("menlo", 18)
        self.button_rect = None
        self._slider_rects = []  # list of (attr, bar_rect, min_v, max_v)
        self._dragging = None    # (attr, bar_rect, min_v, max_v)

    def toggle(self):
        self.level = (self.level + 1) % 5

    def handle_mousedown(self, pos, car=None):
        if self.button_rect and self.button_rect.collidepoint(pos):
            self.toggle()
            return
        if car is not None:
            for attr, bar_rect, min_v, max_v in self._slider_rects:
                if bar_rect.collidepoint(pos):
                    self._dragging = (attr, bar_rect, min_v, max_v)
                    self._apply_slider(pos, car, bar_rect, attr, min_v, max_v)
                    return

    def handle_mousemotion(self, pos, car):
        if self._dragging:
            attr, bar_rect, min_v, max_v = self._dragging
            self._apply_slider(pos, car, bar_rect, attr, min_v, max_v)

    def handle_mouseup(self):
        self._dragging = None

    def _apply_slider(self, pos, car, bar_rect, attr, min_v, max_v):
        t = (pos[0] - bar_rect.x) / bar_rect.width
        t = max(0.0, min(1.0, t))
        value = min_v + t * (max_v - min_v)
        setattr(car, attr, round(value, 2))

    def draw(self, screen, car, lap_timer, ai_stats=None):
        self._draw_toggle_button(screen)
        if self.level == 0:
            return
        self._draw_racing_panel(screen, car, lap_timer)
        if self.level == 2:
            self._draw_car_panel(screen, car)
            self._draw_ai_panel(screen, ai_stats)
        if self.level == 3:
            self._draw_lap_history(screen, lap_timer)
        if self.level == 4:
            self._draw_car_params(screen, car)

    def _draw_toggle_button(self, screen):
        sw, sh = screen.get_size()
        btn_w, btn_h = 64, 28
        x = sw // 2 - btn_w // 2
        y = sh - 52

        self.button_rect = pygame.Rect(x, y, btn_w, btn_h)

        surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 180))
        screen.blit(surf, (x, y))
        pygame.draw.rect(screen, (160, 160, 160), self.button_rect, 1)

        label = self.font_btn.render("HUD", True, (220, 220, 220))
        screen.blit(label, (x + btn_w // 2 - label.get_width() // 2, y + btn_h // 2 - label.get_height() // 2))

        hint = self.font_label.render("[TAB]", True, (130, 130, 130))
        screen.blit(hint, (sw // 2 - hint.get_width() // 2, y + btn_h + 3))

    def _draw_panel(self, screen, x, y, lines):
        panel_w = 240
        panel_h = self.PADDING * 2 + len(lines) * self.LINE_HEIGHT
        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 160))
        screen.blit(surf, (x, y))

        for i, (label, value) in enumerate(lines):
            ty = y + self.PADDING + i * self.LINE_HEIGHT
            screen.blit(self.font_label.render(label, True, (180, 180, 180)), (x + self.PADDING, ty + 5))
            screen.blit(self.font.render(str(value), True, (255, 255, 255)), (x + self.VALUE_X, ty))

    def _draw_racing_panel(self, screen, car, lap_timer):
        sw, sh = screen.get_size()

        speed_kmh = int((car.velocity.length() / 400) * 300)
        lap_count = (len(lap_timer.laps) + 1) if lap_timer.state == "timing" else 1
        current = _fmt_time(lap_timer.current_time() if lap_timer.state == "timing" else None)
        last = _fmt_time(lap_timer.laps[-1] if lap_timer.laps else None)
        best = _fmt_time(min(lap_timer.laps) if lap_timer.laps else None)

        panel_w = 240
        panel_h = self.PADDING * 2 + 5 * self.LINE_HEIGHT + 8
        x = sw - panel_w - 12
        y = sh - panel_h - 12

        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 160))
        screen.blit(surf, (x, y))

        ty = y + self.PADDING
        screen.blit(self.font_label.render("SPD", True, (180, 180, 180)), (x + self.PADDING, ty + 5))
        screen.blit(self.font.render(f"{speed_kmh} km/h", True, (255, 255, 255)), (x + self.VALUE_X, ty))

        bar_x = x + self.PADDING
        bar_y = ty + self.LINE_HEIGHT - 4
        bar_max_w = panel_w - self.PADDING * 2
        bar_fill = int(bar_max_w * min(speed_kmh / 300, 1.0))
        speed_pct = min(speed_kmh / 300, 1.0)
        bar_color = (int(255 * speed_pct), int(255 * (1 - speed_pct)), 50)
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_max_w, 5))
        if bar_fill > 0:
            pygame.draw.rect(screen, bar_color, (bar_x, bar_y, bar_fill, 5))

        remaining_lines = [("LAP", str(lap_count)), ("TIME", current), ("LAST", last), ("BEST", best)]
        base_y = y + self.PADDING + self.LINE_HEIGHT + 8
        for i, (label, value) in enumerate(remaining_lines):
            ty = base_y + i * self.LINE_HEIGHT
            screen.blit(self.font_label.render(label, True, (180, 180, 180)), (x + self.PADDING, ty + 5))
            screen.blit(self.font.render(value, True, (255, 255, 255)), (x + self.VALUE_X, ty))

    def _draw_car_panel(self, screen, car):
        fwd = car.get_forward_vector()
        lateral = car.get_right_vector().dot(car.velocity)
        lines = [
            ("POS X",   f"{car.position.x:.0f}"),
            ("POS Y",   f"{car.position.y:.0f}"),
            ("ANGLE",   f"{car.angle % 360:.1f}°"),
            ("SPD",     f"{car.velocity.length():.1f} px/s"),
            ("VEL X",   f"{car.velocity.x:.1f}"),
            ("VEL Y",   f"{car.velocity.y:.1f}"),
            ("LATERAL", f"{lateral:.1f}"),
            ("FWD X",   f"{fwd.x:.2f}"),
            ("FWD Y",   f"{fwd.y:.2f}"),
        ]
        self._draw_panel(screen, 12, 12, lines)

    def _draw_ai_panel(self, screen, ai_stats):
        sw, sh = screen.get_size()
        if ai_stats:
            lines = [
                ("GEN",     str(ai_stats.get("generation", "--"))),
                ("FITNESS", str(ai_stats.get("fitness", "--"))),
                ("SPECIES", str(ai_stats.get("species", "--"))),
                ("EPISODE", f"{ai_stats.get('episode_time', '--')}s"),
            ]
        else:
            lines = [("GEN", "--"), ("FITNESS", "--"), ("SPECIES", "--"), ("EPISODE", "--")]

        panel_w = 240
        x = sw - panel_w - 12
        self._draw_panel(screen, x, 12, lines)

    def _draw_lap_history(self, screen, lap_timer):
        sw, sh = screen.get_size()
        laps = lap_timer.laps
        best = min(laps) if laps else None

        header_h = self.LINE_HEIGHT + self.PADDING
        num_laps = max(len(laps), 1)
        panel_w = 260
        panel_h = header_h + num_laps * self.LINE_HEIGHT + self.PADDING
        x = 12
        y = 12

        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 160))
        screen.blit(surf, (x, y))
        screen.blit(self.font.render("LAP TIMES", True, (200, 200, 200)), (x + self.PADDING, y + self.PADDING))

        if not laps:
            screen.blit(self.font_label.render("no laps yet", True, (120, 120, 120)), (x + self.PADDING, y + header_h + 4))
            return

        for i, t in enumerate(laps):
            row_y = y + header_h + i * self.LINE_HEIGHT
            is_best = (t == best)
            screen.blit(self.font_label.render(f"L{i + 1}", True, (120, 120, 120)), (x + self.PADDING, row_y + 6))
            screen.blit(self.font.render(_fmt_time(t), True, (255, 215, 0) if is_best else (255, 255, 255)), (x + 46, row_y))
            delta_str = "BEST" if is_best else f"+{t - best:.2f}s"
            screen.blit(self.font_label.render(delta_str, True, (255, 215, 0) if is_best else (200, 100, 100)), (x + 160, row_y + 6))

    def _draw_car_params(self, screen, car):
        sw, sh = screen.get_size()
        self._slider_rects = []

        panel_w = 420
        row_h = 42
        header_h = self.LINE_HEIGHT + self.PADDING
        panel_h = header_h + len(SLIDERS) * row_h + self.PADDING
        x = sw // 2 - panel_w // 2
        y = sh // 2 - panel_h // 2

        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 180))
        screen.blit(surf, (x, y))
        screen.blit(self.font.render("CAR PARAMS", True, (200, 200, 200)), (x + self.PADDING, y + self.PADDING))

        bar_x = x + 110
        bar_w = 150
        bar_h = 10

        for i, (attr, label, min_v, max_v) in enumerate(SLIDERS):
            row_y = y + header_h + i * row_h
            cy = row_y + row_h // 2

            screen.blit(self.font_label.render(label, True, (180, 180, 180)), (x + self.PADDING, cy - 8))

            value = getattr(car, attr)
            t = max(0.0, min(1.0, (value - min_v) / (max_v - min_v)))
            fill_w = int(bar_w * t)

            bar_rect = pygame.Rect(bar_x, cy - bar_h // 2, bar_w, bar_h)
            self._slider_rects.append((attr, bar_rect, min_v, max_v))

            pygame.draw.rect(screen, (50, 50, 50), bar_rect)
            if fill_w > 0:
                is_active = self._dragging and self._dragging[0] == attr
                fill_color = (120, 200, 120) if is_active else (80, 160, 80)
                pygame.draw.rect(screen, fill_color, (bar_x, cy - bar_h // 2, fill_w, bar_h))

            knob_x = bar_x + fill_w
            pygame.draw.rect(screen, (220, 220, 220), (knob_x - 3, cy - bar_h, 6, bar_h * 2))

            val_str = str(int(value)) if isinstance(value, float) and value == int(value) else f"{value:.2f}"
            screen.blit(self.font_label.render(val_str, True, (255, 255, 255)), (bar_x + bar_w + 10, cy - 8))
