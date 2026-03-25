import pygame
import config


class LapTimer:
    COOLDOWN = 0.5

    def __init__(self, line_center, forward_normal, proximity_threshold):
        self.center = line_center
        self.normal = forward_normal
        self.proximity = proximity_threshold
        self.state = "waiting"  # "waiting" | "timing"
        self.start_time = 0.0
        self.laps = []
        self.prev_dist = None
        self.cooldown = 0.0
        self.paused = False
        self.paused_time = 0.0

    def update(self, pos, vel, dt):
        dist = self.normal.dot(pos - self.center)
        self.cooldown = max(0.0, self.cooldown - dt)

        if self.prev_dist is not None and self.cooldown == 0.0:
            crossed = (self.prev_dist < 0) != (dist < 0)
            near_line = pos.distance_to(self.center) < self.proximity
            going_forward = vel.dot(self.normal) < 0

            if crossed and near_line and going_forward:
                now = pygame.time.get_ticks() / 1000.0
                if self.state == "waiting":
                    self.state = "timing"
                    self.start_time = now
                    self.cooldown = self.COOLDOWN
                elif self.state == "timing":
                    self.laps.append(now - self.start_time)
                    self.start_time = now
                    self.cooldown = self.COOLDOWN

        self.prev_dist = dist

    def pause(self):
        self.paused_time = self.current_time()
        self.paused = True

    def unpause(self):
        self.paused = False
        self.start_time += self.current_time() - self.paused_time

    def current_time(self):
        if self.paused:
            return self.paused_time
        elif self.state == "timing":
            return pygame.time.get_ticks() / 1000.0 - self.start_time
        return 0.0

    def draw(self, screen, font, pos=(20, 20)):
        if self.state == "timing":
            t = self.current_time()
            label = font.render(f"Lap: {t:.2f}s", True, config.BLACK)
        else:
            label = font.render("Cross start line to begin", True, config.BLACK)
        screen.blit(label, pos)

        if self.laps != []:
            laps = reversed(self.laps[-3:])  # last 3 laps
            for i, lap in enumerate(laps):
                last_label = font.render(f"Last: {lap:.2f}s", True, config.BLACK)
                screen.blit(
                    last_label,
                    (
                        pos[0],
                        pos[1] + label.get_height() + 4 + (last_label.get_height() * i),
                    ),
                )
