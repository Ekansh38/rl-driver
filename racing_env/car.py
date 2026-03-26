import pygame
import math
import config


class Car:
    def __init__(self, x, y, angle):
        rs = config.RENDER_SCALE
        self._base_surface = pygame.image.load(config.CAR_IMAGE_PATH).convert_alpha()
        self._base_surface = pygame.transform.scale(self._base_surface, (40 * rs, 40 * rs))

        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.angle = angle  # degrees — 0 means car facing up

        # tuning
        self.acceleration_force = 200
        self.brake_force = 250
        self.max_speed = 400
        self.turn_speed = 325
        self.side_friction = 0.8
        self.turn_falloff = 3.0
        self.track_margin = 0
        self.bounce = 0.4

    def get_forward_vector(self):
        rad = math.radians(self.angle)
        return pygame.Vector2(-math.sin(rad), -math.cos(rad))

    def get_right_vector(self):
        rad = math.radians(self.angle)
        return pygame.Vector2(-math.cos(rad), math.sin(rad))

    def update(self, dt, keys):
        forward = self.get_forward_vector()

        if keys["up"]:
            self.velocity += forward * self.acceleration_force * dt
        if keys["down"]:
            self.velocity -= forward * self.brake_force * dt

        if self.velocity.length() > 0:
            self.velocity *= 1 - (0.5 * dt)
        # Clamp speed
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

        speed = self.velocity.length()
        speed_ratio = speed / self.max_speed
        turn_grip = (speed_ratio / (speed_ratio + 0.1)) * (
            1.0 / (1.0 + (speed_ratio * self.turn_falloff) ** 2)
        )

        if keys["right"]:
            self.angle -= self.turn_speed * dt * turn_grip
        if keys["left"]:
            self.angle += self.turn_speed * dt * turn_grip

        right_vec = self.get_right_vector()
        lateral = right_vec * self.velocity.dot(right_vec)
        self.velocity -= lateral * self.side_friction

        self.position += self.velocity * dt

    def draw(self, screen, camera):
        rs = config.RENDER_SCALE
        zoom = camera.zoom
        size = int(40 * rs * zoom)
        surf = pygame.transform.scale(self._base_surface, (size, size))
        rotated = pygame.transform.rotate(surf, self.angle)
        if camera.follow:
            # camera tracks car — car always at viewport center
            cx = config.WIDTH * rs // 2
            cy = config.HEIGHT * rs // 2
        else:
            # fixed camera — car moves across the screen at world position
            cx = int(config.WIDTH * rs // 2 + (self.position.x - config.WIDTH / 2) * zoom * rs)
            cy = int(config.HEIGHT * rs // 2 + (self.position.y - config.HEIGHT / 2) * zoom * rs)
        rect = rotated.get_rect(center=(cx, cy))
        screen.blit(rotated, rect.topleft)
