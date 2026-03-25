import pygame
# ENV SETTINGS
WIDTH = 1280
HEIGHT = 720
FPS = 90
RENDER_SCALE = 1  # 1 = native 1280x720 

# COLORS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

# OTHER

TRACK = 0
GRASS = 1

CAR_IMAGE_PATH = "assets/car.png"

# Controls  

CONTROLS = {
    "arrows": {
        "up":    pygame.K_UP,
        "down":  pygame.K_DOWN,
        "left":  pygame.K_LEFT,
        "right": pygame.K_RIGHT,
        "brake": pygame.K_DOWN,
    },
    "wasd": {
        "up":    pygame.K_w,
        "down":  pygame.K_s,
        "left":  pygame.K_a,
        "right": pygame.K_d,
        "brake": pygame.K_s or pygame.K_LSHIFT,
    },
}

ACTIVE_CONTROLS = ["arrows", "wasd"]

