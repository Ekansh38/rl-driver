import pygame
import math
import config


class Car:
    def __init__(self, x, y, angle):
        rs = config.RENDER_SCALE
        self._base_surface = pygame.image.load(config.CAR_IMAGE_PATH).convert_alpha()
        self._base_surface = pygame.transform.scale(
            self._base_surface, (40 * rs, 40 * rs)
        )

        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.angle = angle

        # tuning
        for attr, val in config.CAR_DEFAULTS.items():
            setattr(self, attr, val) # FIRE FUNCTION, that makes it SO EASY

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

        speed = self.velocity.length()
        if speed > 0:
            self.velocity *= 1 - (0.5 * dt)
            if speed > self.max_speed:
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

    def draw(self, screen, camera, world_w, world_h):
        rs = config.RENDER_SCALE
        zoom = camera.zoom
        size = int(40 * rs * zoom)
        surf = pygame.transform.scale(self._base_surface, (size, size))
        angle = self.angle
        if camera.follow == 2:
            angle = 0
        rotated = pygame.transform.rotate(surf, angle)

        if camera.follow > 0:
            cx = config.WIDTH * rs // 2
            cy = config.HEIGHT * rs // 2
        else:
            cx = int(
                config.WIDTH * rs // 2 + (self.position.x - world_w / 2) * zoom * rs
            )
            cy = int(
                config.HEIGHT * rs // 2 + (self.position.y - world_h / 2) * zoom * rs
            )

        rect = rotated.get_rect(center=(cx, cy))
        screen.blit(rotated, rect.topleft)
