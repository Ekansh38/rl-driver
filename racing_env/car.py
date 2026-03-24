import pygame
import math
import config

class Car:
    def __init__(self, x, y):
        self.surface = pygame.image.load(config.CAR_IMAGE_PATH).convert_alpha()
        self.surface = pygame.transform.scale(self.surface, (40, 40))

        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.angle = 0  # degrees — 0 means car facing up

        # tuning
        self.acceleration_force = 200
        self.brake_force = 250
        self.max_speed = 400
        self.turn_speed = 325
        self.side_friction = 0.8
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
        turn_grip = (speed_ratio / (speed_ratio + 0.1)) * (1.0 / (1.0 + (speed_ratio * 3) ** 2))



        if keys["right"]:
            self.angle -= self.turn_speed * dt * turn_grip 
        if keys["left"]:
            self.angle += self.turn_speed * dt * turn_grip  


        right_vec = self.get_right_vector()
        lateral = right_vec * self.velocity.dot(right_vec)
        self.velocity -= lateral * self.side_friction

        self.position += self.velocity * dt

    def draw(self, screen):
        rotated = pygame.transform.rotate(self.surface, self.angle)
        rect = rotated.get_rect(center=self.position)
        screen.blit(rotated, rect.topleft)
