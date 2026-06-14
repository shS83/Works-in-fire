import math
import random
import sys
from dataclasses import dataclass
from collections import deque
import pygame


WIDTH = 1280
HEIGHT = 720
FPS = 120

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
        self.fragment_shape = random.choice(("dot", "dot", "dot", "dash", "tri"))
        self.rotation = random.random() * math.tau
        self.spin = random.uniform(-9.0, 9.0)
        self.white_hot = random.random() < 0.14

    def update(self, dt):
        self.trail.append(self.pos.copy())

        drag_factor = self.drag ** (dt * 60)
        self.vel *= drag_factor
        self.vel += GRAVITY * self.gravity_scale * dt
        self.pos += self.vel * dt
        self.rotation += self.spin * dt

        self.life -= dt
        if self.life <= 0:
            self.dead = True

    @property
    def age_ratio(self):
        return clamp(1.0 - self.life / self.max_life, 0.0, 1.0)

    @property
    def brightness(self):
        t = self.life / self.max_life
        return clamp(t ** 1.35, 0.0, 1.0)

    def current_color(self):
        t = self.age_ratio
        hot, main, ember = self.palette

        if t < 0.18:
            return lerp_color(hot, main, t / 0.18)

        color = lerp_color(main, ember, (t - 0.18) / 0.82)
        if self.white_hot and t < 0.72:
            return lerp_color(color, (255, 252, 230), 0.38 * (1.0 - t))
        return color

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
        for _ in range(preset.particle_count):
            angle = random.random() * math.tau
            radius_bias = random.random() ** 0.38
            speed = lerp(preset.speed_min, preset.speed_max, radius_bias)

            vertical_squash = random.uniform(0.72, 1.12)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle) * vertical_squash) * speed

            vel += pygame.Vector2(random.uniform(-34, 34), random.uniform(-34, 34))

            self.particles.append(
                Particle(
                    origin,
                    vel,
                    palette,
                    random.uniform(preset.life_min, preset.life_max),
                    random.uniform(0.45, 1.15),
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
                    random.uniform(0.45, 1.05),
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
                    random.uniform(0.35, 0.9),
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
        self.trail_layer.fill((245, 245, 245, 176), special_flags=pygame.BLEND_RGBA_MULT)
        self.smoke_layer.fill((252, 252, 252, 214), special_flags=pygame.BLEND_RGBA_MULT)
        self.glow_layer.fill((238, 238, 238, 150), special_flags=pygame.BLEND_RGBA_MULT)
        self.spark_layer.fill((0, 0, 0, 0))

    def draw_shells(self, shells):
        for shell in shells:
            pygame.draw.circle(self.trail_layer, (*shell.palette[1], 105), shell.pos, 1)
            pygame.draw.circle(self.spark_layer, (255, 245, 210), shell.pos, 1)
            pygame.draw.circle(self.spark_layer, (*shell.palette[1], 40), shell.pos, 2)

    def draw_smoke(self, smoke_particles):
        for smoke in smoke_particles:
            if smoke.alpha <= 0:
                continue

            color = (95, 95, 100, smoke.alpha)
            pygame.draw.circle(self.smoke_layer, color, smoke.pos, int(smoke.size))

    def draw_fragment(self, surface, particle, color, alpha):
        x = int(particle.pos.x)
        y = int(particle.pos.y)
        size = max(1, int(round(particle.size)))

        if particle.fragment_shape == "dash":
            length = max(1.5, particle.size * 2.8)
            dx = math.cos(particle.rotation) * length
            dy = math.sin(particle.rotation) * length
            pygame.draw.line(
                surface,
                (*color, alpha),
                (int(x - dx), int(y - dy)),
                (int(x + dx), int(y + dy)),
                1,
            )
            return

        if particle.fragment_shape == "tri":
            radius = max(1.0, particle.size * 1.7)
            points = []
            for i in range(3):
                angle = particle.rotation + i * math.tau / 3
                points.append((int(x + math.cos(angle) * radius), int(y + math.sin(angle) * radius)))
            pygame.draw.polygon(surface, (*color, alpha), points)
            return

        pygame.draw.circle(surface, (*color, alpha), (x, y), size)

    def draw_particles(self, particles):
        for p in particles:
            if not p.visible_this_frame():
                continue

            color = p.current_color()
            brightness = p.brightness
            alpha = int(255 * brightness)

            self.draw_fragment(self.trail_layer, p, color, int(alpha * 0.78))

            glow_pos = (int(p.pos.x / 2), int(p.pos.y / 2))
            glow_radius = int((1.5 + p.size * 2.5) * brightness)
            if glow_radius > 1:
                pygame.draw.circle(
                    self.glow_layer,
                    (*color, int(28 * brightness)),
                    glow_pos,
                    glow_radius,
                )

            if brightness > 0.05:
                self.draw_fragment(self.spark_layer, p, color, min(255, int(alpha * 1.05)))

            if brightness > 0.68:
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
