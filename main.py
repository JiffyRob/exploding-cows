import asyncio
import math
import random
from collections import namedtuple
from itertools import cycle

import pygame

AnimData = namedtuple("AnimData", ("frames", "delay"))


class AnimParticle:
    def __init__(
        self, pos, velocity, anim, is_alive=lambda self, dt: not self.anim_done
    ):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(velocity)

        self.frames = anim.frames
        self.delay = anim.delay / 1000
        self.image = next(self.frames)
        self.age = 0
        self.anim_done = False
        self.is_alive = is_alive

    def update(self, dt):
        self.pos += self.vel * dt
        self.age += dt
        if not self.anim_done and self.age >= self.delay:
            self.age = 0
            try:
                self.image = next(self.frames)
            except StopIteration:
                self.anim_done = True
        return self.is_alive(self, dt)


class ImageParticle:
    def __init__(self, pos, velocity, image, is_alive=lambda self, dt: True):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.image = image
        self.is_alive = is_alive

    def update(self, dt):
        self.pos += self.velocity * dt
        return self.is_alive(self, dt)


class RectParticle:
    cached_images = {}

    def __init__(self, pos, velocity, size, color, is_alive=lambda self, dt: True):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)

        self.size = tuple(size)
        self.color = color
        self.image = None
        self.is_alive = is_alive
        self.update_image()  # self.image set here

    def update(self, dt):
        self.pos += self.velocity * dt
        return self.is_alive(self, dt)

    def update_image(self):
        cache_lookup = (self.size, self.color)

        cached_image = self.cached_images.get(cache_lookup, None)

        if not cached_image:
            cached_image = pygame.Surface((self.size[0], 3 * self.size[1]))
            cached_image.fill(self.color)

            self.cached_images[cache_lookup] = cached_image

        self.image = cached_image


class CircleParticle:
    cached_images = {}

    def __init__(
        self,
        pos,
        velocity,
        radius,
        color,
        width=0,
        expansion=0,
        is_alive=lambda self: self.radius > 0,
    ):
        self.true_pos = pygame.Vector2(pos)
        self.pos = self.true_pos - (radius, radius)
        self.velocity = pygame.Vector2(velocity)
        self.radius = radius
        self.color = color
        self.image = None
        self.width = width
        self.expansion = expansion
        self.is_alive = is_alive
        self.update_image()  # self.image set here

    def update(self, dt):
        self.true_pos += self.velocity * dt
        if self.expansion:
            self.radius += self.expansion * dt
            self.update_image()
        self.pos = self.true_pos - (self.radius, self.radius)
        return self.is_alive(self, dt)

    def update_image(self):
        # use a rounded radius because sub-pixel doesn't happen and else caching will be almost useless
        radius = round(self.radius)

        cache_lookup = (radius, self.color, self.width)

        cached_image = self.cached_images.get(cache_lookup, None)

        if not cached_image:
            cached_image = pygame.Surface((radius * 2, radius * 2))
            cached_image.fill((0, 255, 255))
            cached_image.set_colorkey((0, 255, 255))
            pygame.draw.circle(
                cached_image, self.color, (radius, radius), radius, self.width
            )

            self.cached_images[cache_lookup] = cached_image

        self.image = cached_image


class ParticleManager:
    def __init__(self):
        self.particles = []

    def update(self, dt):
        self.particles = [
            particle for particle in self.particles if particle.update(dt)
        ]

    def add(self, particles):
        self.particles.extend(particles)

    def draw(self, surface):
        surface.fblits([(particle.image, particle.pos) for particle in self.particles])

    def __len__(self):
        return len(self.particles)


class DurationCallback:
    def __init__(self, duration, on_finish=lambda *args, **kwargs: None):
        self.duration = int(duration)
        self.on_finish = on_finish

    def __call__(self, particle, dt):
        self.duration = max(0, self.duration - dt)
        if not self.duration:
            self.on_finish(particle, dt)
            return 0
        return 1


def sprite_sheet(path, size=(16, 16)):
    # try to optimize the surface for drawing on the screen
    spritesheet = pygame.image.load(path)

    spritesheet.convert()
    spritesheet.set_colorkey("black")

    # creation of variables
    surf_list = []
    width, height = spritesheet.get_size()
    x = 0
    y = 0
    # surface grabbing loop
    while True:
        if x + size[0] > width:
            x = 0
            y += size[1]
        img_rect = pygame.Rect((x, y), size)
        try:
            subsurf = spritesheet.subsurface(img_rect)
        except ValueError:
            break
        surf_list.append(subsurf)
        x += size[0]
    return surf_list


def randpos(length, outside=False):
    angle = random.random() * 2 * math.pi
    if outside:
        mult = 1
    if not outside:
        mult = random.random()
    return pygame.Vector2(
        math.cos(angle) * length * mult, math.sin(angle) * length * mult
    )


def randinrect(rect):
    return pygame.Vector2(
        random.uniform(rect.left, rect.right), random.uniform(rect.top, rect.bottom)
    )


def explosion(
    pos,
    manager,
    size=16,
    ring=True,
    soot=True,
    cloud=True,
    fireball=True,
):
    particles = []
    # flying ring
    if size > 5:
        particles.append(
            CircleParticle(
                pos,
                (0, 0),
                int(size / 2) + 1,
                "white",
                size // 2,
                256,
                DurationCallback(2.5),
            )
        )
    # soot balls
    for i in range(size**2 // 30):
        offset = randpos(size)
        while not offset:
            offset = randpos(size)
        particles.append(
            CircleParticle(
                pos + offset,
                offset.normalize() * (128 + (random.random() * 32 * size)),
                3,
                "black",
                is_alive=on_screen,
            )
        )
    # explosion cloud
    # don't ask how this works, I'm not entirely sure either
    spacing = int(size / 36) + 1
    layers = int(size / spacing) + 1
    shrink_speed = 10  # lower this to speed up the rate at which the explosion shrinks
    max_time = (layers * shrink_speed) + 20
    clouds = []
    for i in range(0, layers):
        radius = i * spacing
        for _ in range(int((radius**2 * math.pi) / (32**2)) + 1):
            offset = randpos(radius, True) + pygame.Vector2(-16, -16)
            clouds.append(
                AnimParticle(
                    pos + offset,
                    0,
                    AnimData(
                        iter(smoke_frames), max(50, max_time - (shrink_speed * i))
                    ),
                )
            )
    clouds.reverse()
    particles.extend(clouds)
    radius = 4
    for i in range(size // 4):
        offset = randpos(radius, True) + pygame.Vector2(-16, -16)
        particles.append(
            AnimParticle(pos + offset, 0, AnimData(iter(smoke_frames), 150))
        )
    # duh duh duh duh-duh duh -- FIREBALL!
    for _ in range(size**2 // 100):
        offset = randpos(size)
        particles.append(
            AnimParticle(
                pos + offset,
                offset.normalize() * size * 6,
                AnimData(cycle(fireball_frames), 250),
                DurationCallback(1),
            )
        )
    manager.add(particles)


def on_screen(particle, dt):
    return screen_rect.collidepoint(particle.pos)


def explosion_callback(particle, dt):
    global COWS
    explosion(particle.pos, manager, size)
    COWS -= 1


def new_cow(manager, time=None):
    global COWS
    if time is None:
        time = random.random() * 1000
    manager.add(
        [
            ImageParticle(
                randinrect(screen_rect),
                0,
                cow_frames[0],
                DurationCallback(
                    time,
                    explosion_callback,
                ),
            )
        ]
    )
    COWS += 1


pygame.init()
font = pygame.font.SysFont(None, 16)

manager = ParticleManager()

screen = pygame.display.set_mode((800, 600), pygame.SCALED)
screen_rect = screen.get_rect().inflate(-50, -50)
size_rect = pygame.Rect(0, 0, 20, 30)
running = True
clock = pygame.time.Clock()
colors = list(pygame.color.THECOLORS.values())
cow_frames = (
    pygame.image.load("cow1.png").convert(),
    pygame.image.load("cow2.png").convert(),
)
fireball_frames = sprite_sheet("fireball.png")
smoke_frames = sprite_sheet("smoke.png", (32, 32))


for img in cow_frames:
    img.set_colorkey("black")


size = 2
COWS = 0


async def main():
    global size
    global COWS
    running = True
    fps = 0
    base_size = float(size)
    while running:
        screen.fill("gray")
        manager.draw(screen)
        screen.blit(font.render(f"{COWS=}", False, "black"), (5, 5))
        pygame.display.flip()
        await asyncio.sleep(0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not event.touch:
                    explosion(event.pos, manager, size)
                print(size)
            if event.type == pygame.FINGERMOTION:
                explosion((event.x, event.y), manager, size)
                explosion(pygame.Vector2(event.x, event.y) + (event.dx, event.dy))
        size = round(base_size)
        dt = clock.tick() / 1000
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            base_size += 10 * dt
        if keys[pygame.K_DOWN]:
            base_size -= 10 * dt
        size = round(base_size)
        fps = clock.get_fps()
        if fps > 60:
            for _ in range(5):
                new_cow(manager)
        manager.update(dt)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
