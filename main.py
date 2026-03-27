import pygame
import config
import racing_env.car as car_module
from utils import get_human_action
import json
import math
from racing_env.start_line import find_start_line
from racing_env.lap_timer import LapTimer
from racing_env.telemetry import LapTelemetry
from hud import HUD
from scipy.ndimage import distance_transform_edt

# simple init stuf

visual_mode = True

pygame.init()
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("rl-driver")
_rs = config.RENDER_SCALE
game_surface = pygame.Surface((config.WIDTH * _rs, config.HEIGHT * _rs))
clock = pygame.time.Clock()

# load track data

with open("track.json") as f:
    track_data = json.load(f)

internal_res = track_data["internal_res"]

world_w = track_data["world_w"]
world_h = track_data["world_h"]

_hex = track_data["background_color"].lstrip("#")
bg_color = tuple(int(_hex[i : i + 2], 16) for i in (0, 2, 4))

scale_x = world_w / track_data["painted_w"]
scale_y = world_h / track_data["painted_h"]

waypoints = [
    pygame.Vector2(p[0] * scale_x, p[1] * scale_y) for p in track_data["waypoints"]
]


mask = pygame.image.load("assets/track_mask.png").convert()
mask = pygame.transform.scale(mask, (world_w, world_h))


mask_arr = pygame.surfarray.array3d(mask)
on_track = mask_arr[:, :, 0] == 0

dist_in = distance_transform_edt(on_track)  # from inside
dist_out = distance_transform_edt(~on_track)  # from outside
signed_dist = dist_in - dist_out  # positive inside negative outside


def is_on_track(pos, margin=0):
    x, y = int(pos.x), int(pos.y)
    if not (0 <= x < world_w and 0 <= y < world_h):
        return False
    return signed_dist[x, y] > margin


# startline setup and also lap timer


def get_forward_normal(line_center, waypoints):
    nearest_idx = min(
        range(len(waypoints)), key=lambda i: line_center.distance_to(waypoints[i])
    )
    step = max(1, len(waypoints) // 20)
    prev_wp = waypoints[(nearest_idx - step) % len(waypoints)]
    next_wp = waypoints[(nearest_idx + step) % len(waypoints)]
    direction = next_wp - prev_wp
    if direction.length() > 0:
        direction = direction.normalize()
    return direction


track_img = pygame.image.load("assets/bg.png").convert()
track_img = pygame.transform.scale(track_img, (world_w * _rs, world_h * _rs))

raw = find_start_line("assets/track_data.png")
start_center = pygame.Vector2(raw.x * scale_x, raw.y * scale_y) if raw else None
if start_center:
    forward_normal = get_forward_normal(start_center, waypoints)
    proximity = float(signed_dist[int(start_center.x), int(start_center.y)])
    lap_timer = LapTimer(start_center, forward_normal, proximity_threshold=proximity)
else:
    lap_timer = None

hud = HUD()
telemetry = LapTelemetry()
prev_lap_count = 0
telemetry_accum = 0.0
TELEMETRY_INTERVAL = 1 / 60


def screen_to_game(pos):
    sw, sh = screen.get_size()
    rs = config.RENDER_SCALE
    return (pos[0] * config.WIDTH * rs // sw, pos[1] * config.HEIGHT * rs // sh)


class Camera:
    def __init__(self):
        self.zoom = 1.0
        self.follow = 0 # 0=static,1=follow,2=follow+angle

        if world_w > config.WIDTH or world_h > config.HEIGHT: # if the world is larger than the screen
            self.follow = 1


camera = Camera()
car_spawn = pygame.Vector2(
    track_data["spawn_x"] * scale_x, track_data["spawn_y"] * scale_y
)
start_angle = track_data["spawn_angle"]
car = car_module.Car(car_spawn.x, car_spawn.y, start_angle)

running = True
paused = False
paused_mode = False
while running:
    if visual_mode:
        dt = clock.get_time() / 1000
    else:
        dt = 1 / 60

    clock.tick(config.FPS if visual_mode else 0)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if not visual_mode:
            continue

        if event.type == pygame.KEYDOWN:
            was_paused = paused

            if event.key == pygame.K_SPACE:
                paused_mode = not paused_mode

            if event.key == pygame.K_f:
                if camera.follow == 2:
                    camera.follow = 0
                else:
                    camera.follow += 1

            if event.key == pygame.K_r:
                # RESET
                car.position = pygame.Vector2(car_spawn)
                car.velocity = pygame.Vector2(0, 0)
                car.angle = start_angle
                if lap_timer:
                    lap_timer.reset()
                paused_mode = False
                telemetry._current = []

            # HUD handles graph_open toggle on G
            hud.handle_keydown(event.key)

            paused = paused_mode or hud.graph_open or hud.params_open
            if lap_timer:
                if paused and not was_paused:
                    lap_timer.pause()
                elif not paused and was_paused:
                    lap_timer.unpause()

        if event.type == pygame.MOUSEBUTTONDOWN:
            was_paused = paused
            hud.handle_mousedown(screen_to_game(event.pos), car, camera)
            paused = paused_mode or hud.graph_open or hud.params_open
            if lap_timer:
                if paused and not was_paused:
                    lap_timer.pause()
                elif not paused and was_paused:
                    lap_timer.unpause()
        if event.type == pygame.MOUSEMOTION:
            hud.handle_mousemotion(screen_to_game(event.pos))
        if event.type == pygame.MOUSEBUTTONUP:
            hud.handle_mouseup()
    game_surface.fill(bg_color)

    if visual_mode:
        keys = get_human_action(pygame.key.get_pressed())
    else:
        keys = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "brake": False,
        }  # dummy

    blocked_by_line = False
    if not paused:
        car.update(dt, keys)

        # record telemetry at ~60 samples/sec regardless of FPS
        telemetry_accum += dt
        if lap_timer and lap_timer.state == "timing" and telemetry_accum >= TELEMETRY_INTERVAL:
            telemetry.record(
                car.velocity.length(), keys["up"], keys["brake"] or keys["down"]
            )
        if telemetry_accum >= TELEMETRY_INTERVAL:
            telemetry_accum -= TELEMETRY_INTERVAL
        if lap_timer and len(lap_timer.laps) > prev_lap_count:
            telemetry.finish_lap()
            prev_lap_count = len(lap_timer.laps)

        # bounce off walls
        if not is_on_track(car.position, car.track_margin):
            car.position -= car.velocity * dt
            if visual_mode:
                car.velocity *= -car.bounce
            else:
                car.velocity *= 0

        if lap_timer and lap_timer.state == "timing":
            if car.position.distance_to(lap_timer.center) < lap_timer.proximity * 2:
                backward_vel = car.velocity.dot(lap_timer.normal)
                if backward_vel > 0:
                    car.velocity -= lap_timer.normal * backward_vel
                    blocked_by_line = True

    # camera-aware track draw
    rs = config.RENDER_SCALE
    zoom = camera.zoom
    tw = int(world_w * zoom * rs)
    th = int(world_h * zoom * rs)

    scaled_track = pygame.transform.smoothscale(track_img, (tw, th))
    screen_width = config.WIDTH * rs
    screen_height = config.HEIGHT * rs
    if camera.follow > 0:
        # track offset so car stays at viewport center
        blit_x = screen_width // 2 - int(car.position.x * zoom * rs)
        blit_y = screen_height // 2 - int(car.position.y * zoom * rs)
        rect = (blit_x, blit_y)
    else:
        blit_x = config.WIDTH * rs // 2 - tw // 2
        blit_y = config.HEIGHT * rs // 2 - th // 2
        rect = (blit_x, blit_y)
    if camera.follow == 2:
        screen_center = pygame.Vector2(screen_width // 2, screen_height //2)
        track_center_world = (world_w//2, world_h//2)

        car_to_track_vector = (track_center_world - car.position) * zoom * rs

        rotated_vector = car_to_track_vector.rotate(car.angle)
        scaled_track = pygame.transform.rotozoom(scaled_track, -car.angle, 1)

        rect = scaled_track.get_rect(center=screen_center + rotated_vector)

    game_surface.blit(scaled_track, rect)

    #    for wp in waypoints:
    #        wp_size = math.ceil(max(scale_x, scale_y) * math.sqrt(2))
    #        surf = pygame.Surface((wp_size, wp_size))
    #        surf.fill(config.BLUE)
    #        game_surface.blit(surf, (wp.x - wp_size // 2, wp.y - wp_size // 2))

    if visual_mode:
        car.draw(game_surface, camera, world_w, world_h)

        if paused_mode:
            rs = config.RENDER_SCALE
            panel_w = config.WIDTH * rs
            panel_h = config.HEIGHT * rs
            surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            surf.fill((0, 0, 0, 200))
            game_surface.blit(surf, (0, 0))

            msg = hud.font.render("PAUSED", True, (255, 255, 255))
            game_surface.blit(
                msg, (panel_w // 2 - msg.get_width() // 2, panel_h - 42 * rs)
            )

        if lap_timer:
            if not paused:
                lap_timer.update(car.position, car.velocity, dt)
            hud.draw(
                game_surface,
                car,
                lap_timer,
                telemetry,
                fps=clock.get_fps(),
                camera=camera,
            )

        if blocked_by_line:
            # temporary pannel in midle
            rs = config.RENDER_SCALE
            panel_w = 500 * rs
            panel_h = 100 * rs
            cx = config.WIDTH * rs // 2
            cy = config.HEIGHT * rs // 2
            surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            surf.fill((0, 0, 0, 220))
            game_surface.blit(surf, (cx - panel_w // 2, cy - panel_h // 2))

            msg = hud.font.render(
                "can't go backwards past start line", True, (255, 0, 0)
            )
            game_surface.blit(
                msg,
                (cx - msg.get_width() // 2, cy - msg.get_height() // 2),
            )
    else:
        if lap_timer:
            lap_timer.update(car.position, car.velocity, dt)

    # scale game surface to actual window size and push to screen
    scaled = pygame.transform.smoothscale(game_surface, screen.get_size())
    screen.blit(scaled, (0, 0))
    pygame.display.flip()
pygame.quit()
