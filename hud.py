import pygame

SLIDERS = [
    ("max_speed", "MAX SPD", 100, 800),
    ("acceleration_force", "ACCEL", 50, 500),
    ("brake_force", "BRAKE", 50, 500),
    ("turn_speed", "TURN", 50, 600),
    ("side_friction", "FRICTION", 0.1, 2.0),
    ("track_margin", "MARGIN", -30, 20),
    ("bounce", "BOUNCE", 0.0, 1.0),
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
        self.graph_idx = 0
        self.font = pygame.font.SysFont("menlo", 22)
        self.font_label = pygame.font.SysFont("menlo", 17)
        self.font_btn = pygame.font.SysFont("menlo", 18)
        self.button_rect = None
        self._slider_rects = []  # list of (attr, bar_rect, min_v, max_v)
        self._dragging = None  # (attr, bar_rect, min_v, max_v)

    def toggle(self):
        self.level = (self.level + 1) % 6

    def handle_keydown(self, key):
        if key == pygame.K_TAB:
            self.toggle()
        elif self.level == 5:
            if key == pygame.K_LEFT:
                self.graph_idx = (self.graph_idx - 1) % 2
            elif key == pygame.K_RIGHT:
                self.graph_idx = (self.graph_idx + 1) % 2

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

    def draw(self, screen, car, lap_timer, telemetry=None, ai_stats=None):
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
        if self.level == 5:
            self._draw_graphs(screen, lap_timer, telemetry)

    def _draw_toggle_button(self, screen):
        sw, sh = screen.get_size()
        btn_w, btn_h = 64, 28
        x = 12
        y = sh - 52

        self.button_rect = pygame.Rect(x, y, btn_w, btn_h)

        surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 180))
        screen.blit(surf, (x, y))
        pygame.draw.rect(screen, (160, 160, 160), self.button_rect, 1)

        label = self.font_btn.render("HUD", True, (220, 220, 220))
        screen.blit(
            label,
            (
                x + btn_w // 2 - label.get_width() // 2,
                y + btn_h // 2 - label.get_height() // 2,
            ),
        )

        hint = self.font_label.render("[TAB]", True, (130, 130, 130))
        screen.blit(hint, (x + btn_w // 2 - hint.get_width() // 2, y + btn_h + 3))

    def _draw_panel(self, screen, x, y, lines):
        panel_w = 240
        panel_h = self.PADDING * 2 + len(lines) * self.LINE_HEIGHT
        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 160))
        screen.blit(surf, (x, y))

        for i, (label, value) in enumerate(lines):
            ty = y + self.PADDING + i * self.LINE_HEIGHT
            screen.blit(
                self.font_label.render(label, True, (180, 180, 180)),
                (x + self.PADDING, ty + 5),
            )
            screen.blit(
                self.font.render(str(value), True, (255, 255, 255)),
                (x + self.VALUE_X, ty),
            )

    def _draw_racing_panel(self, screen, car, lap_timer):
        sw, sh = screen.get_size()

        speed_kmh = int((car.velocity.length() / 400) * 300)
        lap_count = (len(lap_timer.laps) + 1) if lap_timer.state == "timing" else 1
        current = _fmt_time(
            lap_timer.current_time() if lap_timer.state == "timing" else None
        )
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
        screen.blit(
            self.font_label.render("SPD", True, (180, 180, 180)),
            (x + self.PADDING, ty + 5),
        )
        screen.blit(
            self.font.render(f"{speed_kmh} km/h", True, (255, 255, 255)),
            (x + self.VALUE_X, ty),
        )

        bar_x = x + self.PADDING
        bar_y = ty + self.LINE_HEIGHT - 4
        bar_max_w = panel_w - self.PADDING * 2
        bar_fill = int(bar_max_w * min(speed_kmh / 300, 1.0))
        speed_pct = min(speed_kmh / 300, 1.0)
        bar_color = (int(255 * speed_pct), int(255 * (1 - speed_pct)), 50)
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_max_w, 5))
        if bar_fill > 0:
            pygame.draw.rect(screen, bar_color, (bar_x, bar_y, bar_fill, 5))

        remaining_lines = [
            ("LAP", str(lap_count)),
            ("TIME", current),
            ("LAST", last),
            ("BEST", best),
        ]
        base_y = y + self.PADDING + self.LINE_HEIGHT + 8
        for i, (label, value) in enumerate(remaining_lines):
            ty = base_y + i * self.LINE_HEIGHT
            screen.blit(
                self.font_label.render(label, True, (180, 180, 180)),
                (x + self.PADDING, ty + 5),
            )
            screen.blit(
                self.font.render(value, True, (255, 255, 255)), (x + self.VALUE_X, ty)
            )

    def _draw_car_panel(self, screen, car):
        fwd = car.get_forward_vector()
        lateral = car.get_right_vector().dot(car.velocity)
        lines = [
            ("POS X", f"{car.position.x:.0f}"),
            ("POS Y", f"{car.position.y:.0f}"),
            ("ANGLE", f"{car.angle % 360:.1f}°"),
            ("SPD", f"{car.velocity.length():.1f} px/s"),
            ("VEL X", f"{car.velocity.x:.1f}"),
            ("VEL Y", f"{car.velocity.y:.1f}"),
            ("LATERAL", f"{lateral:.1f}"),
            ("FWD X", f"{fwd.x:.2f}"),
            ("FWD Y", f"{fwd.y:.2f}"),
        ]
        self._draw_panel(screen, 12, 12, lines)

    def _draw_ai_panel(self, screen, ai_stats):
        sw, sh = screen.get_size()
        if ai_stats:
            lines = [
                ("GEN", str(ai_stats.get("generation", "--"))),
                ("FITNESS", str(ai_stats.get("fitness", "--"))),
                ("SPECIES", str(ai_stats.get("species", "--"))),
                ("EPISODE", f"{ai_stats.get('episode_time', '--')}s"),
            ]
        else:
            lines = [
                ("GEN", "--"),
                ("FITNESS", "--"),
                ("SPECIES", "--"),
                ("EPISODE", "--"),
            ]

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
        screen.blit(
            self.font.render("LAP TIMES", True, (200, 200, 200)),
            (x + self.PADDING, y + self.PADDING),
        )

        if not laps:
            screen.blit(
                self.font_label.render("no laps yet", True, (120, 120, 120)),
                (x + self.PADDING, y + header_h + 4),
            )
            return

        for i, t in enumerate(laps):
            row_y = y + header_h + i * self.LINE_HEIGHT
            is_best = t == best
            screen.blit(
                self.font_label.render(f"L{i + 1}", True, (120, 120, 120)),
                (x + self.PADDING, row_y + 6),
            )
            screen.blit(
                self.font.render(
                    _fmt_time(t), True, (255, 215, 0) if is_best else (255, 255, 255)
                ),
                (x + 46, row_y),
            )
            delta_str = "BEST" if is_best else f"+{t - best:.2f}s"
            screen.blit(
                self.font_label.render(
                    delta_str, True, (255, 215, 0) if is_best else (200, 100, 100)
                ),
                (x + 160, row_y + 6),
            )

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
        screen.blit(
            self.font.render("CAR PARAMS", True, (200, 200, 200)),
            (x + self.PADDING, y + self.PADDING),
        )

        bar_x = x + 110
        bar_w = 150
        bar_h = 10

        for i, (attr, label, min_v, max_v) in enumerate(SLIDERS):
            row_y = y + header_h + i * row_h
            cy = row_y + row_h // 2

            screen.blit(
                self.font_label.render(label, True, (180, 180, 180)),
                (x + self.PADDING, cy - 8),
            )

            value = getattr(car, attr)
            t = max(0.0, min(1.0, (value - min_v) / (max_v - min_v)))
            fill_w = int(bar_w * t)

            bar_rect = pygame.Rect(bar_x, cy - bar_h // 2, bar_w, bar_h)
            self._slider_rects.append((attr, bar_rect, min_v, max_v))

            pygame.draw.rect(screen, (50, 50, 50), bar_rect)
            if fill_w > 0:
                is_active = self._dragging and self._dragging[0] == attr
                fill_color = (120, 200, 120) if is_active else (80, 160, 80)
                pygame.draw.rect(
                    screen, fill_color, (bar_x, cy - bar_h // 2, fill_w, bar_h)
                )

            knob_x = bar_x + fill_w
            pygame.draw.rect(
                screen, (220, 220, 220), (knob_x - 3, cy - bar_h, 6, bar_h * 2)
            )

            val_str = (
                str(int(value))
                if isinstance(value, float) and value == int(value)
                else f"{value:.2f}"
            )
            screen.blit(
                self.font_label.render(val_str, True, (255, 255, 255)),
                (bar_x + bar_w + 10, cy - 8),
            )

    def _draw_graphs(self, screen, lap_timer, telemetry):
        sw, sh = screen.get_size()
        panel_w, panel_h = 920, 520
        px = sw // 2 - panel_w // 2
        py = sh // 2 - panel_h // 2

        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 210))
        screen.blit(surf, (px, py))

        GRAPH_NAMES = ["LAP TIMES", "SPEED PROFILE"]
        title = self.font.render(GRAPH_NAMES[self.graph_idx], True, (200, 200, 200))
        screen.blit(
            title, (px + panel_w // 2 - title.get_width() // 2, py + self.PADDING)
        )

        gx = px + 68
        gy = py + 50
        gw = panel_w - 88
        gh = panel_h - 100

        if self.graph_idx == 0:
            self._draw_lap_times_graph(screen, gx, gy, gw, gh, lap_timer)
        else:
            self._draw_speed_profile_graph(screen, gx, gy, gw, gh, lap_timer, telemetry)

        nav_y = py + panel_h - 26
        if self.graph_idx > 0:
            lbl = self.font_label.render(
                f"<- {GRAPH_NAMES[self.graph_idx - 1]}", True, (120, 120, 120)
            )
            screen.blit(lbl, (px + 14, nav_y))
        if self.graph_idx < len(GRAPH_NAMES) - 1:
            lbl = self.font_label.render(
                f"{GRAPH_NAMES[self.graph_idx + 1]} ->", True, (120, 120, 120)
            )
            screen.blit(lbl, (px + panel_w - lbl.get_width() - 14, nav_y))

    def _draw_lap_times_graph(self, screen, gx, gy, gw, gh, lap_timer):
        laps = lap_timer.laps
        if len(laps) < 2:
            msg = self.font.render("complete 2+ laps to see graph", True, (80, 80, 80))
            screen.blit(
                msg,
                (
                    gx + gw // 2 - msg.get_width() // 2,
                    gy + gh // 2 - msg.get_height() // 2,
                ),
            )
            return

        best = min(laps)
        worst = max(laps)
        span = max(worst - best, 0.5)
        y_min = max(0, best - span * 0.15)
        y_max = worst + span * 0.15
        best_idx = laps.index(best)

        def to_pt(i, t):
            x = gx + int(i / (len(laps) - 1) * gw)
            y = gy + gh - int((t - y_min) / (y_max - y_min) * gh)
            return (x, max(gy, min(gy + gh, y)))

        # axes
        pygame.draw.line(screen, (55, 55, 55), (gx, gy), (gx, gy + gh), 1)
        pygame.draw.line(screen, (55, 55, 55), (gx, gy + gh), (gx + gw, gy + gh), 1)

        # faint gold grid line at best time
        best_y = gy + gh - int((best - y_min) / (y_max - y_min) * gh)
        pygame.draw.line(screen, (60, 50, 15), (gx, best_y), (gx + gw, best_y), 1)

        # connecting line also dots
        points = [to_pt(i, t) for i, t in enumerate(laps)]
        pygame.draw.lines(screen, (100, 100, 100), False, points, 1)

        for i, (t, pt) in enumerate(zip(laps, points)):
            is_best = i == best_idx
            is_last = i == len(laps) - 1
            color = (
                (255, 215, 0) if is_best else (220, 80, 80) if is_last else (90, 90, 90)
            )
            r = 5 if (is_best or is_last) else 3
            pygame.draw.circle(screen, color, pt, r)

        # labels for best and last
        for i, color, offset_y in [
            (best_idx, (255, 215, 0), -20),
            (len(laps) - 1, (220, 80, 80), 8),
        ]:
            if i == best_idx and i == len(laps) - 1:
                offset_y = -20  # only draw once
            pt = points[i]
            lbl = self.font_label.render(_fmt_time(laps[i]), True, color)
            screen.blit(lbl, (pt[0] - lbl.get_width() // 2, pt[1] + offset_y))

        # x-axis lap numbers
        step = max(1, len(laps) // 12)
        for i in range(0, len(laps), step):
            pt = points[i]
            lbl = self.font_label.render(str(i + 1), True, (70, 70, 70))
            screen.blit(lbl, (pt[0] - lbl.get_width() // 2, gy + gh + 5))

    def _draw_speed_profile_graph(self, screen, gx, gy, gw, gh, lap_timer, telemetry):
        if not telemetry or not telemetry.laps:
            msg = self.font.render("complete a lap to see graph", True, (80, 80, 80))
            screen.blit(
                msg,
                (
                    gx + gw // 2 - msg.get_width() // 2,
                    gy + gh // 2 - msg.get_height() // 2,
                ),
            )
            return

        n = len(telemetry.laps)
        last_tele = telemetry.laps[-1]

        best_tele = None
        if n > 1 and len(lap_timer.laps) >= n:
            times = lap_timer.laps[-n:]
            best_idx = times.index(min(times))
            if best_idx != n - 1:
                best_tele = telemetry.laps[best_idx]

        all_speeds = [s for lap in telemetry.laps for s, _, _ in lap]
        max_kmh = max(s / 400 * 300 for s in all_speeds) * 1.08 if all_speeds else 200
        max_kmh = max(max_kmh, 50)

        def to_pt(idx, total, speed_raw):
            x = gx + int(idx / max(total - 1, 1) * gw)
            kmh = speed_raw / 400 * 300
            y = gy + gh - int(kmh / max_kmh * gh)
            return (x, max(gy, min(gy + gh, y)))

        # axes
        pygame.draw.line(screen, (55, 55, 55), (gx, gy), (gx, gy + gh), 1)
        pygame.draw.line(screen, (55, 55, 55), (gx, gy + gh), (gx + gw, gy + gh), 1)

        # horizontal grid lines
        for spd in range(50, int(max_kmh), 50):
            sy = gy + gh - int(spd / max_kmh * gh)
            pygame.draw.line(screen, (40, 40, 40), (gx, sy), (gx + gw, sy), 1)
            lbl = self.font_label.render(str(spd), True, (60, 60, 60))
            screen.blit(lbl, (gx - lbl.get_width() - 5, sy - lbl.get_height() // 2))

        # best lap, faint gold
        if best_tele:
            step_b = max(1, len(best_tele) // 500)
            pts_b = [
                to_pt(i, len(best_tele), best_tele[i][0])
                for i in range(0, len(best_tele), step_b)
            ]
            if len(pts_b) >= 2:
                pygame.draw.lines(screen, (90, 75, 15), False, pts_b, 1)

        # last lap, colored by input
        total = len(last_tele)
        step = max(1, total // 500)
        for i in range(0, total - step, step):
            speed, accel, brake = last_tele[i]
            pt0 = to_pt(i, total, speed)
            pt1 = to_pt(
                min(i + step, total - 1), total, last_tele[min(i + step, total - 1)][0]
            )
            color = (
                (80, 220, 80) if accel else (220, 80, 80) if brake else (160, 160, 160)
            )
            pygame.draw.line(screen, color, pt0, pt1, 2)

        # legend
        lx = gx + gw - 130
        ly = gy + 10
        for text, color in [
            ("ACCEL", (80, 220, 80)),
            ("BRAKE", (220, 80, 80)),
            ("COAST", (160, 160, 160)),
        ]:
            lbl = self.font_label.render(f"- {text}", True, color)
            screen.blit(lbl, (lx, ly))
            ly += lbl.get_height() + 3
        if best_tele:
            lbl = self.font_label.render("- BEST LAP", True, (90, 75, 15))
            screen.blit(lbl, (lx, ly))
