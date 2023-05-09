import pygame
import random

import animation


class AnimParticle:
    def __init__(self, pos, velocity, anim, is_alive=lambda self: True):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(velocity)

        self.anim = anim
        self.is_alive = is_alive

    def update(self, dt):
        self.pos += self.vel * dt
        return self.is_alive(self)

    @property
    def image(self):
        return self.anim.image()


class ImageParticle:
    def __init__(self, pos, velocity, image, is_alive=lambda self: True):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.image = image
        self.is_alive = is_alive

    def update(self, dt):
        self.pos += self.velocity * dt
        return self.is_alive(self)


class RectParticle:
    cached_images = {}

    def __init__(self, pos, velocity, size, color, is_alive=lambda self: True):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)

        self.size = tuple(size)
        self.color = color
        self.image = None
        self.is_alive = is_alive
        self.update_image()  # self.image set here

    def update(self, dt):
        self.pos += self.velocity * dt
        return self.is_alive(self)

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
        return self.is_alive(self)

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


def explosion(
    pos, manager, size=(16, 16), ring=True, soot=True, cloud=True, fireball=True
):
    particles = []
    # flying rings
    for i in range(size // 8):
        particles.append(CircleParticle(pos, (0, 0), 1 + (10 * i), "white", 5, 32))
    # soot balls
    offset_rect = pygame.Rect(-size / 2, -size / 2, size, size)
    for i in range(size // 3):
        offset = randpos(offset_rect)
        while not offset:
            offset = randpos(offset_rect)
        particles.append(
            CircleParticle(pos + offset, offset.normalize() * 32, 3, "black")
        )
    # explosion cloud
    for i in range((size // 8) + 1):
        particles.append(
            AnimParticle(
                pos + randpos(offset_rect) + pygame.Vector2(-16, -16),
                (0, 0),
                animation.Animation(smoke_frames, 150),
            )
        )
    # fireballs
    for i in range((size // 16) + 4):
        offset = randpos(offset_rect)
        while not offset:
            offset = randpos(offset_rect)
        particles.append(
            AnimParticle(
                pos + offset + pygame.Vector2(-8, -8),
                offset.normalize() * 12,
                animation.Animation(fireball_frames),
            )
        )

    manager.add(particles)


def randpos(rect):
    return pygame.Vector2(
        random.randint(rect.left, rect.right), random.randint(rect.top, rect.bottom)
    )


manager = ParticleManager()

screen = pygame.display.set_mode((800, 600), pygame.SCALED)
screen_rect = screen.get_rect().inflate(-50, -50)
veloc_rect = pygame.Rect(-50, -50, 100, 100)
size_rect = pygame.Rect(0, 0, 20, 30)
running = True
clock = pygame.time.Clock()
colors = list(pygame.color.THECOLORS.values())
images = (
    pygame.image.load("cow1.png").convert(),
    pygame.image.load("cow2.png").convert(),
)
fireball_frames = sprite_sheet("fireball.png")
smoke_frames = sprite_sheet("smoke.png", (32, 32))


for img in images:
    img.set_colorkey("black")

manager.add(
    [
        ImageParticle(randpos(screen_rect), randpos(veloc_rect), images[0])
        for _ in range(0)
    ]
)
size = 16
while running:
    screen.fill("gray")
    manager.draw(screen)
    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                explosion(event.pos, manager, size)
            if event.button == 4:
                size += 1
            if event.button == 5:
                size -= 1
            print(size)
    dt = clock.tick() / 1000
    manager.update(dt)
    pygame.display.set_caption(f"{round(clock.get_fps())} {len(manager)}")

pygame.quit()
