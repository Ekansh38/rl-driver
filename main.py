import pygame
import config
import racing_env.car as car
from utils import get_human_action
import json
import math
from racing_env.start_line import find_start_line
from racing_env.lap_timer import LapTimer
from racing_env.telemetry import LapTelemetry
from hud import HUD

# simple init stuf

visual_mode = True

pygame.init()
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
pygame.display.set_caption("rl-driver")
clock = pygame.time.Clock()

# load waypoints

track_img = pygame.image.load("assets/waypoint_layer.png").convert()
track_img = pygame.transform.scale(track_img, (config.WIDTH, config.HEIGHT))

with open("track.json") as f:
    track_data = json.load(f)

waypoints = [pygame.Vector2(p) for p in track_data["waypoints"]]
track_width = track_data["track_width"]

# scale waypoints from 160x90 to 1280x720
scale_x = config.WIDTH / 160
scale_y = config.HEIGHT / 90
waypoints = [pygame.Vector2(wp.x * scale_x, wp.y * scale_y) for wp in waypoints]
track_width_scaled = track_width * scale_x

def is_on_track(pos, margin=0):
    return any(
        max(abs(pos.x - wp.x), abs(pos.y - wp.y)) + margin < track_width_scaled
        for wp in waypoints
    )


# startline setup and also lap timer

def get_forward_normal(line_center, waypoints):
    # returns forward direction vector
    dists = [(line_center.distance_to(wp), i) for i, wp in enumerate(waypoints)]
    dists.sort()
    idx = dists[0][1]
    prev_wp = waypoints[(idx - 1) % len(waypoints)]
    next_wp = waypoints[(idx + 1) % len(waypoints)]
    direction = next_wp - prev_wp
    if direction.length() > 0:
        direction = direction.normalize()
    return direction


track_img = pygame.image.load("assets/bg.png").convert()

raw = find_start_line("assets/waypoint_layer.png")
start_center = pygame.Vector2(raw.x * scale_x, raw.y * scale_y) if raw else None
if start_center:
    forward_normal = get_forward_normal(start_center, waypoints)
    lap_timer = LapTimer(start_center, forward_normal, proximity_threshold=track_width_scaled)
else:
    lap_timer = None

hud = HUD()
telemetry = LapTelemetry()
prev_lap_count = 0

car = car.Car(1100, 600)

running = True
while running:
    if visual_mode:
        dt = clock.get_time() / 1000
    else:
        dt = 1/60

    clock.tick(config.FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if not visual_mode:
            continue

        if event.type == pygame.KEYDOWN:
            hud.handle_keydown(event.key)
        if event.type == pygame.MOUSEBUTTONDOWN:
            hud.handle_mousedown(event.pos, car)
        if event.type == pygame.MOUSEMOTION:
            hud.handle_mousemotion(event.pos, car)
        if event.type == pygame.MOUSEBUTTONUP:
            hud.handle_mouseup()
    screen.fill(config.BLACK)

    if visual_mode:
        keys = get_human_action(pygame.key.get_pressed())
    else:
        keys = {"up": False, "down": False, "left": False, "right": False, "brake": False} # dummy

    car.update(dt, keys)

    # record telemetry
    if lap_timer and lap_timer.state == "timing":
        telemetry.record(car.velocity.length(), keys['up'], keys['brake'] or keys['down'])
    if lap_timer and len(lap_timer.laps) > prev_lap_count:
        telemetry.finish_lap()
        prev_lap_count = len(lap_timer.laps)

    # bounce of walls
    if not is_on_track(car.position, car.track_margin):
        car.position -= car.velocity * dt
        if visual_mode:
            car.velocity *= -car.bounce
        else:
            car.velocity *= 0

    blocked_by_line = False
    if lap_timer and lap_timer.state == "timing":
        if car.position.distance_to(lap_timer.center) < lap_timer.proximity * 2:
            backward_vel = car.velocity.dot(lap_timer.normal)
            if backward_vel > 0:
                car.velocity -= lap_timer.normal * backward_vel
                blocked_by_line = True

    screen.blit(track_img, (0, 0))

#    for wp in waypoints:
#        wp_size = math.ceil(max(scale_x, scale_y) * math.sqrt(2))
#        surf = pygame.Surface((wp_size, wp_size))
#        surf.fill(config.BLUE)
#        screen.blit(surf, (wp.x - wp_size // 2, wp.y - wp_size // 2))


    if visual_mode:
        car.draw(screen)

        if lap_timer:
            lap_timer.update(car.position, car.velocity, dt)
            hud.draw(screen, car, lap_timer, telemetry)

        if blocked_by_line:
            # temporary pannel in midle
            panel_w = 500
            panel_h = 100
            surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            surf.fill((0, 0, 0, 220))
            screen.blit(surf, (config.WIDTH//2-(panel_w//2), config.HEIGHT//2-(panel_h//2), panel_w, panel_h))

            msg = hud.font.render("can't go backwards past start line", True, (255, 0, 0))
            screen.blit(msg, (config.WIDTH // 2 - msg.get_width() // 2, config.HEIGHT // 2 - msg.get_height() // 2))
    else:
        if lap_timer:
            lap_timer.update(car.position, car.velocity, dt)

    # push buffer to screen
    pygame.display.flip()       
pygame.quit()

