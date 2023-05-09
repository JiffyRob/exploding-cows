import itertools

import pygame


class Animation:
    def __init__(self, images, length=250, mirror_x=False, mirror_y=False):
        self.lengths = length
        if isinstance(length, int):
            self.lengths = [length for _ in images]
        self.images = [
            pygame.transform.flip(image, mirror_x, mirror_y).convert_alpha()
            for image in images
        ]
        self.index = 0
        self.last_start_time = 0

    def __len__(self):
        return len(self.images)

    def increment(self):
        self.index += 1
        self.index %= len(self.images)
        self.last_start_time = pygame.time.get_ticks()

    def reset(self):
        self.index = 0
        self.last_start_time = pygame.time.get_ticks()

    def image(self):
        now = pygame.time.get_ticks()
        if now - self.last_start_time > self.lengths[self.index]:
            self.increment()
        return self.images[self.index]

    def done(self):
        return False


class PingPongAnimation(Animation):
    def __init__(self, images, length=250):
        super().__init__(images, length)
        self.direction = 1

    def reset(self):
        super().reset()
        self.direction = 1

    def increment(self):
        self.index += self.direction
        if not (0 <= self.index < len(self.images)):
            self.direction *= -1
            self.index += self.direction * 2
        self.last_start_time = pygame.time.get_ticks()


class OnceAnimation(Animation):
    def __init__(self, images, length=250):
        super().__init__(images, length)
        self.hit_end = False

    def reset(self):
        super().reset()
        self.hit_end = False

    def increment(self):
        self.index = self.index + 1
        max_index = len(self.images) - 1
        if self.index > max_index:
            self.hit_end = True
            self.index = max_index
        self.last_start_time = pygame.time.get_ticks()

    def done(self):
        return self.hit_end


class MultiAnimation:
    def __init__(self, animations, positions=None, size=None):
        self.animations = list(animations)
        self.positions = positions
        if self.positions is None:
            self.positions = [(0, 0) for i in self.animations]
        self.size = size
        if self.size is None:
            width = 0
            height = 0
            for animation in self.animations:
                size = animation.image().get_size()
                width = max(width, size[0])
                height = max(height, size[1])
            self.size = width, height

    def __len__(self):
        return len(self.animations)

    def reset(self):
        for anim in self.animations:
            anim.reset()

    def increment(self):
        pass

    def image(self):
        surface = pygame.Surface(self.size).convert_alpha()
        surface.fill((0, 0, 0, 0))
        for anim, pos in zip(self.animations, self.positions):
            surface.blit(anim.image(), pos)
        return surface

    def done(self):
        for anim in self.animations:
            if not anim.done():
                return False
        return True
