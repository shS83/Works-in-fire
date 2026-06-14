import math
import random
import sys
from dataclasses import dataclass
from collections import deque
import pygame


WIDTH = 1280
HEIGHT = 720
FPS = 60

GRAVITY = pygame.Vector2(0, 120)
BACKGROUND_TOP = (5, 8, 18)
BACKGROUND_BOTTOM = (18, 18, 32)


def clamp(value, low, high):
    return max(low, min(high, value))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(a, b, t):
    return (
        int(lerp(a[0], b[0], t)),
        int(lerp(a[1], b[1], t)),
        int(lerp(a[2], b[2], t)),
    )


def random_color_palette():
    palettes = [
        [(255, 245, 210), (255, 180, 70), (255, 95, 35)],
        [(255, 245, 230), (255, 70, 70), (180, 20, 40)],
        [(230, 255, 240), (80, 255, 140), (20, 160, 90)],
        [(230, 245, 255), (90, 170, 255), (80, 90, 255)],
        [(255, 235, 255), (210, 90, 255), (120, 50, 220)],
        [(255, 255, 245), (255, 255, 180), (255, 210, 90)],
    ]
    return random.choice(palettes)


@dataclass
class ExplosionPreset:
    name: str
    particle_count: int
    speed_min: float
    speed_max: float
    life_min: float
    life_max: float
    drag: float
    gravity_scale: float
    trail_length: int
    smoke_amount: float
    shape: str = "sphere"
    crackle: bool = False
    strobe: bool = False


PRESETS = [
    ExplosionPreset(
        name="Peony",
        particle_count=420,
        speed_min=120,
        speed_max=330,
        life_min=1.4,
        life_max=2.4,
        drag=0.985,
        gravity_scale=0.9,
        trail_length=3,
        smoke_amount=0.35,
    ),
    ExplosionPreset(
        name="Chrysanthemum",
        particle_count=700,
        speed_min=150,
        speed_max=420,
        life_min=1.8,
        life_max=3.0,
        drag=0.978,
        gravity_scale=0.85,
        trail_length=6,
        smoke_amount=0.55,
    ),
    ExplosionPreset(
        name="Golden Willow",
        particle_count=520,
        speed_min=80,
        speed_max=300,
        life_min=2.6,
        life_max=4.2,
        drag=0.965,
        gravity_scale=1.25,
        trail_length=10,
        smoke_amount=0.8,
    ),
    ExplosionPreset(
        name="Ring",
        particle_count=360,
        speed_min=220,
        speed_max=280,
        life_min=1.8,
        life_max=2.7,
        drag=0.982,
        gravity_scale=0.75,
        trail_length=8,
        smoke_amount=0.45,
        shape="ring",
    ),
    ExplosionPreset(
        name="Crackle",
        particle_count=320,
        speed_min=120,
        speed_max=300,
        life_min=1.2,
        life_max=2.0,
        drag=0.98,
        gravity_scale=0.9,
        trail_length=6,
        smoke_amount=0.4,
        crackle=True,
    ),
    ExplosionPreset(
        name="Strobe",
        particle_count=380,
        speed_min=110,
        speed_max=320,
        life_min=1.8,
        life_max=3.0,
        drag=0.982,
        gravity_scale=0.8,
        trail_length=10,
        smoke_amount=0.35,
        strobe=True,
    ),
]


class Particle:
    def __init__(
        self,
        position,
        velocity,
        palette,
        life,
        size,
        drag,
        gravity_scale,
        trail_length,
        crackle=False,
        strobe=False,
    ):
        self.pos = pygame.Vector2(position)
        self.vel = pygame.Vector2(velocity)
        self.palette = palette
        self.life = life
        self.max_life = life
        self.size = size
        self.drag = drag
        self.gravity_scale = gravity_scale
        self.trail = deque(maxlen=trail_length)
        self.crackle = crackle
        self.has_crackled = False
        self.strobe = strobe
        self.dead = False
        self.phase = random.random() * 10

    def update(self, dt):
        self.trail.append(self.pos.copy())

        drag_factor = self.drag ** (dt * 60)
        self.vel *= drag_factor
        self.vel += GRAVITY * self.gravity_scale * dt
        self.pos += self.vel * dt

        self.life -= dt
        if self.life <= 0:
            self.dead = True

    @property
    def age_ratio(self):
        return clamp(1.0 - self.life / self.max_life, 0.0, 1.0)

    @property
    def brightness(self):
        t = self.life / self.max_life
        return clamp(t * t, 0.0, 1.0)

    def current_color(self):
        t = self.age_ratio
        hot, main, ember = self.palette

        if t < 0.18:
            return lerp_color(hot, main, t / 0.18)

        return lerp_color(main, ember, (t - 0.18) / 0.82)

    def visible_this_frame(self):
        if not self.strobe:
            return True
        return math.sin(pygame.time.get_ticks() * 0.04 + self.phase) > -0.15


class SmokeParticle:
    def __init__(self, position, velocity, size, life):
        self.pos = pygame.Vector2(position)
        self.vel = pygame.Vector2(velocity)
        self.size = size
        self.start_size = size
        self.life = life
        self.max_life = life
        self.dead = False

    def update(self, dt, wind):
        self.vel += pygame.Vector2(wind * 10, -8) * dt
        self.vel *= 0.992 ** (dt * 60)
        self.pos += self.vel * dt
        self.size += 18 * dt
        self.life -= dt

        if self.life <= 0:
            self.dead = True

    @property
    def alpha(self):
        t = self.life / self.max_life
        return int(55 * clamp(t, 0.0, 1.0))


class Shell:
    def __init__(self, x, target_y, preset, palette):
        self.pos = pygame.Vector2(x, HEIGHT + 20)
        self.vel = pygame.Vector2(random.uniform(-25, 25), random.uniform(-650, -520))
        self.target_y = target_y
        self.preset = preset
        self.palette = palette
        self.trail = deque(maxlen=24)
        self.dead = False

    def update(self, dt):
        self.trail.append(self.pos.copy())
        self.vel += GRAVITY * 0.42 * dt
        self.pos += self.vel * dt

        if self.vel.y >= 0 or self.pos.y <= self.target_y:
            self.dead = True
            return True

        return False


class FireworkManager:
    def __init__(self):
        self.shells = []
        self.particles = []
        self.smoke = []
        self.launch_timer = 0.0
        self.wind = 0.0
        self.shake = 0.0

    def launch_random(self):
        x = random.randint(120, WIDTH - 120)
        target_y = random.randint(90, 330)
        preset = random.choice(PRESETS)
        palette = random_color_palette()
        self.shells.append(Shell(x, target_y, preset, palette))

    def explode(self, shell):
        preset = shell.preset
        palette = shell.palette
        origin = shell.pos.copy()

        if preset.shape == "ring":
            self.spawn_ring(origin, preset, palette)
        else:
            self.spawn_sphere(origin, preset, palette)

        smoke_count = int(18 + preset.smoke_amount * 45)
        for _ in range(smoke_count):
            velocity = pygame.Vector2(random.uniform(-50, 50), random.uniform(-30, 35))
            self.smoke.append(
                SmokeParticle(
                    origin + pygame.Vector2(random.uniform(-12, 12), random.uniform(-12, 12)),
                    velocity,
                    random.uniform(18, 45),
                    random.uniform(1.8, 3.8),
                )
            )

        self.shake = max(self.shake, min(10.0, preset.particle_count / 90))

    def spawn_sphere(self, origin, preset, palette):
        golden_angle = math.pi * (3 - math.sqrt(5))

        for i in range(preset.particle_count):
            angle = i * golden_angle + random.uniform(-0.04, 0.04)
            radius_bias = math.sqrt(random.random())
            speed = lerp(preset.speed_min, preset.speed_max, radius_bias)

            vertical_squash = random.uniform(0.78, 1.08)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle) * vertical_squash) * speed

            vel += pygame.Vector2(random.uniform(-20, 20), random.uniform(-20, 20))

            self.particles.append(
                Particle(
                    origin,
                    vel,
                    palette,
                    random.uniform(preset.life_min, preset.life_max),
                    random.uniform(0.7, 1.8),
                    preset.drag + random.uniform(-0.004, 0.004),
                    preset.gravity_scale,
                    preset.trail_length,
                    crackle=preset.crackle,
                    strobe=preset.strobe,
                )
            )

    def spawn_ring(self, origin, preset, palette):
        count = preset.particle_count

        for i in range(count):
            angle = math.tau * i / count
            speed = random.uniform(preset.speed_min, preset.speed_max)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle) * 0.72) * speed
            vel += pygame.Vector2(random.uniform(-8, 8), random.uniform(-8, 8))

            self.particles.append(
                Particle(
                    origin,
                    vel,
                    palette,
                    random.uniform(preset.life_min, preset.life_max),
                    random.uniform(0.6, 1.5),
                    preset.drag,
                    preset.gravity_scale,
                    preset.trail_length,
                )
            )

    def spawn_crackle(self, particle):
        count = random.randint(8, 16)
        palette = [(255, 255, 235), (255, 230, 130), (255, 130, 50)]

        for _ in range(count):
            angle = random.random() * math.tau
            speed = random.uniform(40, 150)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            vel += particle.vel * 0.2

            self.particles.append(
                Particle(
                    particle.pos,
                    vel,
                    palette,
                    random.uniform(0.35, 0.8),
                    random.uniform(0.5, 1.2),
                    0.94,
                    0.6,
                    8,
                )
            )

    def update(self, dt):
        self.wind = math.sin(pygame.time.get_ticks() * 0.00018) * 1.8

        self.launch_timer -= dt
        if self.launch_timer <= 0:
            launches = 1 if random.random() < 0.82 else random.randint(2, 4)
            for _ in range(launches):
                self.launch_random()
            self.launch_timer = random.uniform(0.45, 1.6)

        for shell in self.shells[:]:
            exploded = shell.update(dt)
            if exploded:
                self.explode(shell)
                self.shells.remove(shell)

        for particle in self.particles[:]:
            particle.update(dt)

            if (
                particle.crackle
                and not particle.has_crackled
                and particle.age_ratio > random.uniform(0.58, 0.82)
            ):
                particle.has_crackled = True
                self.spawn_crackle(particle)

            if particle.dead:
                self.particles.remove(particle)

        for smoke in self.smoke[:]:
            smoke.update(dt, self.wind)
            if smoke.dead:
                self.smoke.remove(smoke)

        self.shake = max(0.0, self.shake - dt * 18)


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.trail_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.glow_layer = pygame.Surface((WIDTH // 2, HEIGHT // 2), pygame.SRCALPHA)
        self.smoke_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.spark_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    def draw_background(self, offset):
        self.screen.fill((0, 0, 0))

        # Optional very subtle ground silhouette.
        pygame.draw.rect(
            self.screen,
            (3, 3, 5),
            (0 + offset[0], HEIGHT - 42 + offset[1], WIDTH, 42),
        )

    def fade_layers(self):
        self.trail_layer.fill((0, 0, 0, 0))
        self.smoke_layer.fill((0, 0, 0, 0))
        self.glow_layer.fill((0, 0, 0, 0))
        self.spark_layer.fill((0, 0, 0, 0))

    def draw_shells(self, shells):
        for shell in shells:
            points = list(shell.trail)
            for i in range(1, len(points)):
                t = i / len(points)
                alpha = int(180 * t)
                color = (*shell.palette[1], alpha)
                pygame.draw.line(self.trail_layer, color, points[i - 1], points[i], max(1, int(3 * t)))

            pygame.draw.circle(self.spark_layer, (255, 245, 210), shell.pos, 1)
            pygame.draw.circle(self.spark_layer, (*shell.palette[1], 80), shell.pos, 3)

    def draw_smoke(self, smoke_particles):
        for smoke in smoke_particles:
            if smoke.alpha <= 0:
                continue

            color = (95, 95, 100, smoke.alpha)
            pygame.draw.circle(self.smoke_layer, color, smoke.pos, int(smoke.size))

    def draw_particles(self, particles):
        for p in particles:
            if not p.visible_this_frame():
                continue

            color = p.current_color()
            brightness = p.brightness
            alpha = int(255 * brightness)

            trail_points = list(p.trail)
            if len(trail_points) > 1:
                for i in range(1, len(trail_points)):
                    t = i / len(trail_points)
                    trail_alpha = int(alpha * t * 0.55)
                    width = max(1, int(p.size * t))
                    pygame.draw.line(
                        self.trail_layer,
                        (*color, trail_alpha),
                        trail_points[i - 1],
                        trail_points[i],
                        width,
                    )

            glow_pos = (int(p.pos.x / 2), int(p.pos.y / 2))
            glow_radius = int((8 + p.size * 6) * brightness)
            if glow_radius > 1:
                pygame.draw.circle(
                    self.glow_layer,
                    (*color, int(80 * brightness)),
                    glow_pos,
                    glow_radius,
                )

            core_radius = max(1, int(p.size * brightness))
            pygame.draw.circle(self.spark_layer, (*color, alpha), p.pos, core_radius)

            if brightness > 0.55:
                pygame.draw.circle(self.spark_layer, (255, 250, 230, int(180 * brightness)), p.pos, 1)

    def composite(self, offset):
        scaled_glow = pygame.transform.smoothscale(self.glow_layer, (WIDTH, HEIGHT))

        self.screen.blit(self.smoke_layer, offset)
        self.screen.blit(scaled_glow, offset, special_flags=pygame.BLEND_ADD)
        self.screen.blit(self.trail_layer, offset, special_flags=pygame.BLEND_ADD)
        self.screen.blit(self.spark_layer, offset, special_flags=pygame.BLEND_ADD)


def main():
    pygame.init()
    pygame.display.set_caption("State-of-the-Art Fireworks Base")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    manager = FireworkManager()
    renderer = Renderer(screen)

    paused = False
    running = True

    while running:
        dt = clock.tick(FPS) / 1000
        dt = min(dt, 1 / 30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    manager.launch_random()
                elif event.key == pygame.K_p:
                    paused = not paused

            if event.type == pygame.MOUSEBUTTONDOWN:
                preset = random.choice(PRESETS)
                palette = random_color_palette()
                fake_shell = Shell(event.pos[0], event.pos[1], preset, palette)
                fake_shell.pos = pygame.Vector2(event.pos)
                manager.explode(fake_shell)

        if not paused:
            manager.update(dt)

        shake = manager.shake
        offset = (
            int(random.uniform(-shake, shake)),
            int(random.uniform(-shake, shake)),
        )

        renderer.fade_layers()
        renderer.draw_background(offset)
        renderer.draw_smoke(manager.smoke)
        renderer.draw_shells(manager.shells)
        renderer.draw_particles(manager.particles)
        renderer.composite(offset)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()