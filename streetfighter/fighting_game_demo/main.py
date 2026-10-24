import os
import sys
import math
import random
import pygame

# For machines without a display, uncomment/use SDL_VIDEODRIVER=dummy when testing.
pygame.init()

WIDTH, HEIGHT = 1200, 700
FPS = 60
GROUND_Y = 575
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Dr. Pombo vs Mr. Boombastic - Prototype')
CLOCK = pygame.time.Clock()

# ---------- Fonts ----------
FONT = pygame.font.SysFont('arial', 24, bold=True)
SMALL = pygame.font.SysFont('arial', 16, bold=True)
BIG = pygame.font.SysFont('arial', 64, bold=True)
MED = pygame.font.SysFont('arial', 34, bold=True)

WHITE = (245, 245, 250)
BLACK = (10, 10, 14)
NEON_BLUE = (65, 210, 255)
NEON_PINK = (255, 70, 180)
NEON_PURPLE = (150, 80, 255)
GOLD = (255, 205, 70)
HEALTH = (75, 230, 110)
DANGER = (240, 70, 70)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, 'assets')


def load_sprite(path, scale=2.6):
    img = pygame.image.load(path).convert_alpha()
    w, h = img.get_size()
    img = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
    return img


def load_dir(folder, prefix):
    out = []
    path = os.path.join(ASSET_DIR, folder)
    files = sorted(
        f for f in os.listdir(path)
        if f.lower().endswith('.png') and f.startswith(prefix)
    )
    for f in files:
        out.append(load_sprite(os.path.join(path, f)))
    return out


# ---------- Character ----------
class Fighter:
    def __init__(self, name, folder, x, facing, color, controls, stats):
        self.name = name
        self.folder = folder
        self.x = float(x)
        self.y = float(GROUND_Y - 175)
        self.start_x = float(x)
        self.facing = facing
        self.color = color
        self.controls = controls
        self.stats = stats

        self.idle = load_dir(folder, 'idle_')
        self.punch_frames = load_dir(folder, 'punch_')
        self.kick_frames = load_dir(folder, 'kick_')
        if not self.idle:
            raise RuntimeError(f'Nenhum sprite idle encontrado para {folder}')

        self.vy = 0.0
        self.speed = stats['speed']
        self.jump = stats['jump']
        self.health = stats['health']
        self.max_health = stats['health']
        self.meter = 0

        self.state = 'idle'
        self.attack_timer = 0
        self.attack_kind = None
        self.has_hit = False
        self.blocking = False
        self.hitstun = 0
        self.flash = 0

        self.anim_t = 0
        self.anim_index = 0

    def rect(self):
        # approximate hurt box based on sprite
        return pygame.Rect(int(self.x - 40), int(self.y + 20), 80, 155)

    def attack_rect(self):
        if self.state not in ('punch', 'kick'):
            return pygame.Rect(0, 0, 0, 0)
        body = self.rect()
        reach = 90 if self.attack_kind == 'punch' else 120
        h = 45 if self.attack_kind == 'punch' else 60
        y = body.y + (40 if self.attack_kind == 'punch' else 85)
        if self.facing == 1:
            return pygame.Rect(body.right - 5, y, reach, h)
        return pygame.Rect(body.left - reach + 5, y, reach, h)

    def reset(self):
        self.x = self.start_x
        self.y = GROUND_Y - 175
        self.vy = 0
        self.health = self.max_health
        self.meter = 0
        self.state = 'idle'
        self.attack_timer = 0
        self.attack_kind = None
        self.has_hit = False
        self.blocking = False
        self.hitstun = 0
        self.flash = 0

    def try_jump(self):
        if self.y >= GROUND_Y - 175 - 0.5 and self.hitstun <= 0 and self.state == 'idle':
            self.vy = -self.jump

    def try_attack(self, kind):
        if self.hitstun > 0 or self.blocking or self.state != 'idle':
            return
        self.attack_kind = kind
        self.state = kind
        self.attack_timer = 22 if kind == 'punch' else 28
        self.has_hit = False

    def special(self):
        if self.hitstun > 0 or self.blocking or self.state != 'idle' or self.meter < 100:
            return False
        self.meter = 0
        self.state = 'special'
        self.attack_timer = 36
        self.has_hit = False
        return True

    def input(self, keys):
        self.blocking = False
        if self.hitstun > 0 or self.state != 'idle':
            return
        if keys[self.controls['block']]:
            self.blocking = True
            return
        move = 0
        if keys[self.controls['left']]: move -= 1
        if keys[self.controls['right']]: move += 1
        self.x += move * self.speed
        if move != 0:
            self.facing = 1 if move > 0 else -1

    def update(self):
        if self.flash > 0:
            self.flash -= 1
        if self.hitstun > 0:
            self.hitstun -= 1

        # gravity / jump
        if self.y < GROUND_Y - 175 or self.vy < 0:
            self.vy += 0.85
            self.y += self.vy
            if self.y >= GROUND_Y - 175:
                self.y = GROUND_Y - 175
                self.vy = 0

        # attack animation/state
        if self.state in ('punch', 'kick'):
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.state = 'idle'
                self.attack_kind = None
                self.has_hit = False
        elif self.state == 'special':
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.state = 'idle'
                self.has_hit = False

        self.x = max(60, min(WIDTH - 60, self.x))

        # animation clock
        self.anim_t += 1
        if self.anim_t >= 7:
            self.anim_t = 0
            self.anim_index += 1

    def take_hit(self, damage, push, attacker_facing):
        if self.blocking:
            damage = max(1, int(damage * 0.18))
            push *= 0.25
        self.health = max(0, self.health - damage)
        self.meter = min(100, self.meter + 12)
        self.hitstun = 14 if damage < 100 else 22
        self.flash = 7
        self.x += push * attacker_facing

    def current_sprite(self):
        if self.state == 'punch' and self.punch_frames:
            idx = min(1, len(self.punch_frames) - 1) if self.attack_timer > 10 else min(0, len(self.punch_frames)-1)
            return self.punch_frames[idx]
        if self.state == 'kick' and self.kick_frames:
            idx = min(1, len(self.kick_frames) - 1) if self.attack_timer > 13 else min(0, len(self.kick_frames)-1)
            return self.kick_frames[idx]
        return self.idle[self.anim_index % len(self.idle)]

    def draw(self, surf, debug=False):
        img = self.current_sprite()
        if self.facing == -1:
            img = pygame.transform.flip(img, True, False)
        if self.flash % 2 == 1:
            # cheap hit flash without modifying source asset
            flash = img.copy()
            flash.fill((255, 255, 255, 180), special_flags=pygame.BLEND_RGBA_MULT)
            img = flash
        r = img.get_rect(midbottom=(int(self.x), GROUND_Y))
        surf.blit(img, r)

        if self.state == 'special':
            self.draw_special(surf)
        elif self.blocking:
            pygame.draw.arc(surf, (255, 245, 180), self.rect().inflate(55, 25), math.pi * 0.9, math.pi * 1.9, 5)

        if debug:
            pygame.draw.rect(surf, (90, 150, 255), self.rect(), 1)
            if self.state in ('punch', 'kick'):
                pygame.draw.rect(surf, (255, 90, 90), self.attack_rect(), 1)

    def draw_special(self, surf):
        pulse = int(14 + 8 * math.sin(pygame.time.get_ticks() * 0.02))
        center = (int(self.x + self.facing * 100), int(self.y + 95))
        if self.name == 'DR. POMBO':
            for i in range(3):
                pygame.draw.circle(surf, NEON_BLUE, (center[0] + self.facing * i * 26, center[1]), pulse - i * 3, 3)
            pygame.draw.circle(surf, WHITE, center, pulse // 2, 3)
        else:
            for i in range(3):
                pygame.draw.arc(surf, GOLD, pygame.Rect(center[0] - 35 - i * 8, center[1] - 35 - i * 8, 70 + i * 16, 70 + i * 16), -0.9, 0.9, 5)


# ---------- Stage ----------
def draw_stage(surf, t):
    # sky gradient-ish bands
    for y in range(HEIGHT):
        f = y / HEIGHT
        c = (int(18 + 28 * f), int(14 + 12 * f), int(42 + 50 * f))
        pygame.draw.line(surf, c, (0, y), (WIDTH, y))

    # giant moon / neon circle
    pygame.draw.circle(surf, (82, 52, 130), (950, 150), 92)
    pygame.draw.circle(surf, (120, 70, 170), (950, 150), 92, 4)
    pygame.draw.circle(surf, (175, 105, 220), (950, 150), 74, 2)

    # distant skyline
    rng = random.Random(1234)
    x = 0
    while x < WIDTH:
        w = rng.randint(55, 110)
        h = rng.randint(90, 250)
        y = GROUND_Y - 35 - h
        pygame.draw.rect(surf, (20, 21, 38), (x, y, w, h))
        # lit windows
        for wy in range(y + 18, y + h - 10, 26):
            for wx in range(x + 10, x + w - 6, 20):
                if rng.random() < 0.42:
                    c = NEON_PINK if rng.random() < 0.35 else NEON_BLUE
                    pygame.draw.rect(surf, c, (wx, wy, 6, 10))
        x += w + 5

    # central holographic sign
    sign = pygame.Rect(450, 115, 300, 92)
    pygame.draw.rect(surf, (15, 15, 30), sign, border_radius=12)
    pygame.draw.rect(surf, NEON_PURPLE, sign, 3, border_radius=12)
    title = MED.render('NIGHT CITY // FIGHT', True, WHITE)
    surf.blit(title, title.get_rect(center=sign.center))

    # floor
    pygame.draw.rect(surf, (8, 8, 15), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    pygame.draw.line(surf, NEON_BLUE, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
    # perspective grid
    for i in range(-12, 13):
        bx = WIDTH // 2 + i * 110
        pygame.draw.line(surf, (38, 60, 90), (WIDTH // 2, GROUND_Y), (bx, HEIGHT), 1)
    for j in range(1, 8):
        yy = GROUND_Y + j * j * 3 + 10
        pygame.draw.line(surf, (38, 60, 90), (0, yy), (WIDTH, yy), 1)

    # moving light streaks
    for i in range(8):
        xx = int((t * (40 + i * 7) + i * 160) % (WIDTH + 250)) - 250
        pygame.draw.line(surf, (60, 100, 180), (xx, 330 + i * 24), (xx + 110, 330 + i * 24), 2)


def draw_bar(surf, x, y, w, h, value, maximum, reverse=False, fill=HEALTH):
    pygame.draw.rect(surf, (10, 10, 15), (x, y, w, h), border_radius=8)
    ratio = 0 if maximum <= 0 else max(0, min(1, value / maximum))
    fw = int(w * ratio)
    if reverse:
        pygame.draw.rect(surf, fill, (x + w - fw, y, fw, h), border_radius=8)
    else:
        pygame.draw.rect(surf, fill, (x, y, fw, h), border_radius=8)
    pygame.draw.rect(surf, WHITE, (x, y, w, h), 2, border_radius=8)


def collision_resolve(a, b):
    ar, br = a.rect(), b.rect()
    if ar.colliderect(br):
        overlap = ar.clip(br).width
        if ar.centerx < br.centerx:
            a.x -= overlap / 2
            b.x += overlap / 2
        else:
            a.x += overlap / 2
            b.x -= overlap / 2


def process_attack(attacker, defender):
    if attacker.state == 'special':
        # special is active in middle frames
        if not (12 <= attacker.attack_timer <= 29) or attacker.has_hit:
            return
        hitbox = pygame.Rect(int(attacker.x + attacker.facing * 35 - (0 if attacker.facing == 1 else 140)), int(attacker.y + 70), 140, 90)
        damage = 160
        push = 14
    elif attacker.state in ('punch', 'kick'):
        active = 8 <= attacker.attack_timer <= 16 if attacker.state == 'punch' else 10 <= attacker.attack_timer <= 20
        if not active or attacker.has_hit:
            return
        hitbox = attacker.attack_rect()
        damage = 55 if attacker.state == 'punch' else 85
        push = 7 if attacker.state == 'punch' else 11
    else:
        return

    if hitbox.colliderect(defender.rect()):
        defender.take_hit(damage, push, attacker.facing)
        attacker.has_hit = True
        attacker.meter = min(100, attacker.meter + 8)


def draw_hud(surf, p1, p2, time_left, round_no):
    draw_bar(surf, 50, 30, 460, 34, p1.health, p1.max_health)
    draw_bar(surf, WIDTH - 510, 30, 460, 34, p2.health, p2.max_health, reverse=True)
    # meters
    draw_bar(surf, 50, 73, 330, 12, p1.meter, 100, fill=NEON_BLUE)
    draw_bar(surf, WIDTH - 380, 73, 330, 12, p2.meter, 100, reverse=True, fill=GOLD)

    t = BIG.render(str(max(0, int(time_left))).zfill(2), True, WHITE)
    surf.blit(t, t.get_rect(center=(WIDTH // 2, 50)))

    n1 = FONT.render(p1.name, True, WHITE)
    n2 = FONT.render(p2.name, True, WHITE)
    surf.blit(n1, (50, 5))
    surf.blit(n2, (WIDTH - 50 - n2.get_width(), 5))

    r = SMALL.render(f'ROUND {round_no}', True, (220, 220, 235))
    surf.blit(r, r.get_rect(center=(WIDTH // 2, 102)))


def draw_controls(surf):
    text = 'P1: A/D andar  W pular  S defender  J soco  K chute  L especial      |      P2: ←/→ ↑ ↓ NUM1 NUM2 NUM3'
    s = SMALL.render(text, True, (185, 185, 210))
    surf.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT - 25))


p1 = Fighter(
    'DR. POMBO', 'dr_pombo', 300, 1, NEON_BLUE,
    {'left': pygame.K_a, 'right': pygame.K_d, 'block': pygame.K_s},
    {'health': 1000, 'speed': 5.3, 'jump': 15.5}
)
p2 = Fighter(
    'MR. BOOMBASTIC', 'mr_boombastic', 900, -1, GOLD,
    {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'block': pygame.K_DOWN},
    {'health': 1200, 'speed': 4.4, 'jump': 14.2}
)

round_no = 1
time_left = 60.0
state = 'fight'
state_timer = 0
winner = ''

running = True
tick = 0
while running:
    dt = CLOCK.tick(FPS) / 1000.0
    tick += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if state == 'fight':
                if event.key == pygame.K_w: p1.try_jump()
                if event.key == pygame.K_j: p1.try_attack('punch')
                if event.key == pygame.K_k: p1.try_attack('kick')
                if event.key == pygame.K_l: p1.special()
                if event.key == pygame.K_UP: p2.try_jump()
                if event.key == pygame.K_KP1: p2.try_attack('punch')
                if event.key == pygame.K_KP2: p2.try_attack('kick')
                if event.key == pygame.K_KP3: p2.special()
            elif state == 'winner' and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                p1.reset(); p2.reset(); round_no = 1; time_left = 60.0; state = 'fight'; winner = ''

    if state == 'fight':
        keys = pygame.key.get_pressed()
        p1.input(keys)
        p2.input(keys)
        p1.update(); p2.update()
        collision_resolve(p1, p2)
        process_attack(p1, p2)
        process_attack(p2, p1)
        time_left -= dt

        if p1.health <= 0 or p2.health <= 0 or time_left <= 0:
            if p1.health > p2.health:
                winner = p1.name + ' VENCEU'
            elif p2.health > p1.health:
                winner = p2.name + ' VENCEU'
            else:
                winner = 'EMPATE'
            state = 'winner'
            state_timer = 0

    elif state == 'winner':
        state_timer += dt

    # ---------- Draw ----------
    draw_stage(SCREEN, tick)
    p1.draw(SCREEN)
    p2.draw(SCREEN)
    draw_hud(SCREEN, p1, p2, time_left, round_no)
    draw_controls(SCREEN)

    if state == 'winner':
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        SCREEN.blit(overlay, (0, 0))
        glow = BIG.render(winner, True, WHITE)
        SCREEN.blit(glow, glow.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        sub = FONT.render('ENTER / ESPAÇO para reiniciar', True, (205, 205, 230))
        SCREEN.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55)))

    pygame.display.flip()

pygame.quit()
sys.exit()
