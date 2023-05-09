# code for creating explosions from dafluffypotato's explont
# https://dafluffypotato.itch.io/explont, explont.py, lines 790-807
for i in range(16):
    angle = random.random() * math.pi * 0.5 + math.pi * 5 / 4
    speed = random.random() * 2 + 1
    gd.circle_particles.append(
        [
            "fire_base",
            [gd.player.center[0], gd.player.pos[1] + gd.player.rect.height],
            [math.cos(angle) * speed, math.sin(angle) * speed],
            (245, 237, 186),
            2,
            0.005,
            random.random() * 0.7,
        ]
    )
for i in range(30):
    gd.circle_particles.append(
        [
            "fire",
            [
                gd.player.pos[0] + gd.player.rect.width * random.random(),
                gd.player.pos[1] + gd.player.rect.height * random.random(),
            ],
            [random.random() * 4 - 2, random.random() * 4 - 3],
            (0, 0, 0),
            random.random() * 24 + 2,
            random.random() * 0.3 + 0.3,
            random.random() * 0.8,
        ]
    )
for i in range(36):
    c = random.choice(
        [
            (100, 125, 52),
            (192, 199, 65),
            (157, 48, 59),
            (157, 48, 59),
            (157, 48, 59),
            (157, 48, 59),
            (62, 33, 55),
            (62, 33, 55),
        ]
    )
    gd.circle_particles.append(
        [
            "flesh",
            [
                gd.player.pos[0] + gd.player.rect.width * random.random(),
                gd.player.pos[1] + gd.player.rect.height * random.random(),
            ],
            [random.random() * 2 - 1, random.random() * 3 - 2],
            c,
            random.random() * 3.5 + 1,
            0.001,
            0,
        ]
    )
for i in range(30):
    a = random.random() * math.pi * 2
    s = random.random() + 0.5
    if random.random() < 0.2:
        s *= 3
    gd.sparks.append(
        [
            gd.player.center,
            a,
            s * 5.5,
            3,
            0.05 + random.random() * 0.05,
            0.88 + random.random() * 0.05,
            10 + random.random() * 6,
            0.99,
        ]
    )
gd.circles.append([gd.player.center, 10, 1, 10, 0.15, 0.9, (247, 237, 186)])
gd.circles.append([gd.player.center, 7, 1, 6, 0.1, 0.87, (247, 237, 186)])
gd.game_over = 1
