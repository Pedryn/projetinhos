import pygame
import sys

# =========================================================
# CONFIGURAÇÕES
# =========================================================

pygame.init()

WIDTH = 1100
HEIGHT = 650
FPS = 60

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Projeto Fighting Game")

CLOCK = pygame.time.Clock()

# Cores
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (210, 50, 50)
GREEN = (50, 200, 80)
BLUE = (60, 120, 220)
YELLOW = (240, 210, 70)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 40)
GROUND_COLOR = (70, 120, 70)

FONT = pygame.font.SysFont("arial", 26, bold=True)
BIG_FONT = pygame.font.SysFont("arial", 64, bold=True)
SMALL_FONT = pygame.font.SysFont("arial", 20)

GROUND_Y = 540


# =========================================================
# CLASSE DO LUTADOR
# =========================================================

class Fighter:
    def __init__(
        self,
        x,
        y,
        color,
        name,
        controls,
        facing=1
    ):
        self.x = x
        self.y = y

        self.start_x = x
        self.start_y = y

        self.width = 70
        self.height = 150

        self.color = color
        self.name = name

        # 1 = direita
        # -1 = esquerda
        self.facing = facing

        # Física
        self.speed = 5
        self.jump_power = 15
        self.gravity = 0.8

        self.velocity_x = 0
        self.velocity_y = 0

        self.on_ground = True
        self.crouching = False
        self.blocking = False

        # Vida
        self.max_health = 1000
        self.health = self.max_health

        # Combate
        self.attack_type = None
        self.attack_timer = 0
        self.attack_cooldown = 0

        self.hitbox_active = False
        self.has_hit = False

        self.hitstun = 0
        self.knockback = 0

        # Controles
        self.controls = controls

        # Estado
        self.alive = True

    # -----------------------------------------------------
    # RESET
    # -----------------------------------------------------

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y

        self.velocity_x = 0
        self.velocity_y = 0

        self.health = self.max_health

        self.on_ground = True
        self.crouching = False
        self.blocking = False

        self.attack_type = None
        self.attack_timer = 0
        self.attack_cooldown = 0

        self.hitbox_active = False
        self.has_hit = False

        self.hitstun = 0
        self.knockback = 0

        self.alive = True

    # -----------------------------------------------------
    # RETÂNGULO DO CORPO
    # -----------------------------------------------------

    def get_rect(self):

        height = self.height

        if self.crouching:
            height = 100

        return pygame.Rect(
            int(self.x),
            int(self.y + self.height - height),
            self.width,
            height
        )

    # -----------------------------------------------------
    # HITBOX DO ATAQUE
    # -----------------------------------------------------

    def get_attack_rect(self):

        body = self.get_rect()

        if not self.hitbox_active:
            return pygame.Rect(0, 0, 0, 0)

        attack_width = 65

        if self.attack_type == "punch":
            attack_height = 45
            y_offset = 50

        elif self.attack_type == "kick":
            attack_height = 60
            y_offset = 75

        else:
            return pygame.Rect(0, 0, 0, 0)

        if self.facing == 1:

            return pygame.Rect(
                body.right,
                body.y + y_offset,
                attack_width,
                attack_height
            )

        return pygame.Rect(
            body.left - attack_width,
            body.y + y_offset,
            attack_width,
            attack_height
        )

    # -----------------------------------------------------
    # ATAQUE
    # -----------------------------------------------------

    def attack(self, attack_type):

        if self.attack_cooldown > 0:
            return

        if self.hitstun > 0:
            return

        if self.attack_type is not None:
            return

        self.attack_type = attack_type
        self.has_hit = False

        if attack_type == "punch":
            self.attack_timer = 18

        elif attack_type == "kick":
            self.attack_timer = 25

    # -----------------------------------------------------
    # PULO
    # -----------------------------------------------------

    def jump(self):

        if self.on_ground and self.hitstun <= 0:

            self.velocity_y = -self.jump_power
            self.on_ground = False

    # -----------------------------------------------------
    # RECEBER DANO
    # -----------------------------------------------------

    def take_damage(self, damage, knockback):

        if not self.alive:
            return

        if self.blocking:
            damage = int(damage * 0.2)
            knockback *= 0.3

        self.health -= damage

        if self.health <= 0:

            self.health = 0
            self.alive = False

        self.hitstun = 15
        self.knockback = knockback

    # -----------------------------------------------------
    # CONTROLE
    # -----------------------------------------------------

    def handle_input(self, keys):

        if self.hitstun > 0:
            return

        if self.attack_type is not None:
            return

        self.crouching = keys[self.controls["down"]]

        self.blocking = keys[self.controls["block"]]

        move = 0

        if keys[self.controls["left"]]:
            move -= 1

        if keys[self.controls["right"]]:
            move += 1

        self.velocity_x = move * self.speed

        if move != 0:
            self.facing = 1 if move > 0 else -1

    # -----------------------------------------------------
    # ATUALIZAÇÃO
    # -----------------------------------------------------

    def update(self):

        # ----------------------------------------------
        # HITSTUN
        # ----------------------------------------------

        if self.hitstun > 0:
            self.hitstun -= 1

        # ----------------------------------------------
        # KNOCKBACK
        # ----------------------------------------------

        if self.knockback != 0:

            self.x += self.knockback

            if self.knockback > 0:
                self.knockback -= 0.7
                if self.knockback < 0:
                    self.knockback = 0

            else:
                self.knockback += 0.7
                if self.knockback > 0:
                    self.knockback = 0

        # ----------------------------------------------
        # MOVIMENTO
        # ----------------------------------------------

        self.x += self.velocity_x

        # ----------------------------------------------
        # GRAVIDADE
        # ----------------------------------------------

        if not self.on_ground:

            self.velocity_y += self.gravity
            self.y += self.velocity_y

            if self.y >= GROUND_Y - self.height:

                self.y = GROUND_Y - self.height
                self.velocity_y = 0
                self.on_ground = True

        # ----------------------------------------------
        # LIMITES DA ARENA
        # ----------------------------------------------

        if self.x < 40:
            self.x = 40

        if self.x + self.width > WIDTH - 40:
            self.x = WIDTH - 40 - self.width

        # ----------------------------------------------
        # ATAQUE
        # ----------------------------------------------

        if self.attack_type is not None:

            self.attack_timer -= 1

            # Janela onde o golpe causa dano

            if self.attack_type == "punch":

                self.hitbox_active = 8 <= self.attack_timer <= 14

            elif self.attack_type == "kick":

                self.hitbox_active = 10 <= self.attack_timer <= 18

            if self.attack_timer <= 0:

                self.attack_type = None
                self.hitbox_active = False
                self.attack_cooldown = 10

        else:

            self.hitbox_active = False

        # ----------------------------------------------
        # COOLDOWN
        # ----------------------------------------------

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    # -----------------------------------------------------
    # DESENHAR
    # -----------------------------------------------------

    def draw(self, surface):

        body = self.get_rect()

        # sombra
        shadow = pygame.Rect(
            int(self.x - 10),
            GROUND_Y + 2,
            self.width + 20,
            10
        )

        pygame.draw.ellipse(
            surface,
            (35, 35, 35),
            shadow
        )

        # corpo
        pygame.draw.rect(
            surface,
            self.color,
            body,
            border_radius=10
        )

        # cabeça
        head_size = 38

        head_x = int(self.x + self.width / 2 - head_size / 2)
        head_y = int(self.y - 28)

        pygame.draw.circle(
            surface,
            (230, 190, 150),
            (
                head_x + head_size // 2,
                head_y + head_size // 2
            ),
            head_size // 2
        )

        # olhos
        eye_x = (
            head_x + 24
            if self.facing == 1
            else head_x + 10
        )

        pygame.draw.circle(
            surface,
            BLACK,
            (eye_x, head_y + 13),
            3
        )

        # ----------------------------------------------
        # BRAÇOS
        # ----------------------------------------------

        if self.attack_type == "punch":

            if self.facing == 1:

                pygame.draw.line(
                    surface,
                    (230, 190, 150),
                    (body.centerx, body.y + 55),
                    (body.right + 55, body.y + 55),
                    12
                )

            else:

                pygame.draw.line(
                    surface,
                    (230, 190, 150),
                    (body.centerx, body.y + 55),
                    (body.left - 55, body.y + 55),
                    12
                )

        elif self.attack_type == "kick":

            pygame.draw.line(
                surface,
                (230, 190, 150),
                (body.centerx, body.bottom - 35),
                (
                    body.centerx + self.facing * 55,
                    body.bottom - 10
                ),
                14
            )

        else:

            pygame.draw.line(
                surface,
                (230, 190, 150),
                (body.centerx - 12, body.y + 55),
                (body.left - 18, body.y + 85),
                10
            )

            pygame.draw.line(
                surface,
                (230, 190, 150),
                (body.centerx + 12, body.y + 55),
                (body.right + 18, body.y + 85),
                10
            )

        # ----------------------------------------------
        # PERNAS
        # ----------------------------------------------

        pygame.draw.line(
            surface,
            BLACK,
            (body.centerx - 15, body.bottom),
            (body.centerx - 20, GROUND_Y),
            15
        )

        pygame.draw.line(
            surface,
            BLACK,
            (body.centerx + 15, body.bottom),
            (body.centerx + 20, GROUND_Y),
            15
        )

        # ----------------------------------------------
        # BLOQUEIO
        # ----------------------------------------------

        if self.blocking:

            pygame.draw.circle(
                surface,
                YELLOW,
                body.center,
                55,
                4
            )

        # ----------------------------------------------
        # HITBOX
        # ----------------------------------------------

        if self.hitbox_active:

            attack_rect = self.get_attack_rect()

            pygame.draw.rect(
                surface,
                (255, 100, 100),
                attack_rect,
                2
            )


# =========================================================
# FUNÇÕES
# =========================================================

def draw_background():

    SCREEN.fill((35, 45, 70))

    # céu
    pygame.draw.rect(
        SCREEN,
        (55, 75, 110),
        (0, 0, WIDTH, 300)
    )

    # prédios
    for x in range(0, WIDTH, 120):

        height = 100 + ((x * 7) % 160)

        pygame.draw.rect(
            SCREEN,
            (45, 55, 75),
            (
                x,
                300 - height,
                100,
                height
            )
        )

        # janelas
        for wy in range(300 - height + 20, 280, 30):

            for wx in range(x + 15, x + 90, 25):

                pygame.draw.rect(
                    SCREEN,
                    YELLOW,
                    (wx, wy, 10, 12)
                )

    # chão
    pygame.draw.rect(
        SCREEN,
        GROUND_COLOR,
        (
            0,
            GROUND_Y,
            WIDTH,
            HEIGHT - GROUND_Y
        )
    )

    # linha do chão
    pygame.draw.line(
        SCREEN,
        WHITE,
        (0, GROUND_Y),
        (WIDTH, GROUND_Y),
        3
    )


def draw_health_bar(
    x,
    y,
    width,
    height,
    current,
    maximum,
    flip=False
):

    # fundo
    pygame.draw.rect(
        SCREEN,
        BLACK,
        (x, y, width, height)
    )

    ratio = max(0, current / maximum)

    health_width = int(width * ratio)

    if flip:

        pygame.draw.rect(
            SCREEN,
            RED,
            (
                x + width - health_width,
                y,
                health_width,
                height
            )
        )

    else:

        pygame.draw.rect(
            SCREEN,
            RED,
            (
                x,
                y,
                health_width,
                height
            )
        )

    pygame.draw.rect(
        SCREEN,
        WHITE,
        (x, y, width, height),
        3
    )


def draw_hud(player1, player2, timer):

    # nomes
    text1 = FONT.render(
        player1.name,
        True,
        WHITE
    )

    text2 = FONT.render(
        player2.name,
        True,
        WHITE
    )

    SCREEN.blit(
        text1,
        (50, 25)
    )

    SCREEN.blit(
        text2,
        (
            WIDTH - 50 - text2.get_width(),
            25
        )
    )

    # barras
    draw_health_bar(
        50,
        65,
        380,
        35,
        player1.health,
        player1.max_health
    )

    draw_health_bar(
        WIDTH - 430,
        65,
        380,
        35,
        player2.health,
        player2.max_health,
        flip=True
    )

    # timer
    timer_text = BIG_FONT.render(
        str(timer).zfill(2),
        True,
        WHITE
    )

    SCREEN.blit(
        timer_text,
        (
            WIDTH // 2 - timer_text.get_width() // 2,
            25
        )
    )


def draw_center_text(text, size=64):

    font = pygame.font.SysFont(
        "arial",
        size,
        bold=True
    )

    rendered = font.render(
        text,
        True,
        WHITE
    )

    SCREEN.blit(
        rendered,
        (
            WIDTH // 2 - rendered.get_width() // 2,
            HEIGHT // 2 - rendered.get_height() // 2
        )
    )


def separate_players(player1, player2):

    rect1 = player1.get_rect()
    rect2 = player2.get_rect()

    if rect1.colliderect(rect2):

        overlap = rect1.clip(rect2).width

        if rect1.centerx < rect2.centerx:

            player1.x -= overlap / 2
            player2.x += overlap / 2

        else:

            player1.x += overlap / 2
            player2.x -= overlap / 2


def process_attack(attacker, defender):

    if not attacker.hitbox_active:
        return

    if attacker.has_hit:
        return

    attack_rect = attacker.get_attack_rect()
    defender_rect = defender.get_rect()

    if attack_rect.colliderect(defender_rect):

        if attacker.attack_type == "punch":

            damage = 45
            knockback = 7

        elif attacker.attack_type == "kick":

            damage = 70
            knockback = 11

        else:
            return

        direction = 1 if attacker.facing == 1 else -1

        defender.take_damage(
            damage,
            knockback * direction
        )

        attacker.has_hit = True


def reset_round(player1, player2):

    player1.reset()
    player2.reset()

    player1.x = 260
    player2.x = WIDTH - 330

    player1.facing = 1
    player2.facing = -1


# =========================================================
# CONTROLES
# =========================================================

player1_controls = {

    "left": pygame.K_a,
    "right": pygame.K_d,
    "down": pygame.K_s,
    "block": pygame.K_q,

}

player2_controls = {

    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "down": pygame.K_DOWN,
    "block": pygame.K_KP0,

}


# =========================================================
# CRIAÇÃO DOS LUTADORES
# =========================================================

player1 = Fighter(
    260,
    GROUND_Y - 150,
    BLUE,
    "PLAYER 1",
    player1_controls
)

player2 = Fighter(
    WIDTH - 330,
    GROUND_Y - 150,
    RED,
    "PLAYER 2",
    player2_controls,
    facing=-1
)


# =========================================================
# ESTADO DO JOGO
# =========================================================

game_state = "fight"

round_number = 1

timer = 60
timer_accumulator = 0

winner_text = ""

running = True


# =========================================================
# LOOP PRINCIPAL
# =========================================================

while running:

    dt = CLOCK.tick(FPS)

    # -----------------------------------------------------
    # EVENTOS
    # -----------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        if event.type == pygame.KEYDOWN:

            # P1
            if event.key == pygame.K_w:
                player1.jump()

            if event.key == pygame.K_j:
                player1.attack("punch")

            if event.key == pygame.K_k:
                player1.attack("kick")

            # P2
            if event.key == pygame.K_UP:
                player2.jump()

            if event.key == pygame.K_KP1:
                player2.attack("punch")

            if event.key == pygame.K_KP2:
                player2.attack("kick")

            # reiniciar
            if (
                event.key == pygame.K_RETURN
                and game_state == "winner"
            ):

                round_number = 1

                timer = 60

                winner_text = ""

                reset_round(
                    player1,
                    player2
                )

                game_state = "fight"

    # -----------------------------------------------------
    # JOGO
    # -----------------------------------------------------

    if game_state == "fight":

        keys = pygame.key.get_pressed()

        player1.handle_input(keys)
        player2.handle_input(keys)

        player1.update()
        player2.update()

        separate_players(
            player1,
            player2
        )

        process_attack(
            player1,
            player2
        )

        process_attack(
            player2,
            player1
        )

        # -------------------------------------------------
        # TIMER
        # -------------------------------------------------

        timer_accumulator += dt

        if timer_accumulator >= 1000:

            timer -= 1
            timer_accumulator = 0

            if timer <= 0:

                if player1.health > player2.health:

                    winner_text = "PLAYER 1 VENCEU"

                elif player2.health > player1.health:

                    winner_text = "PLAYER 2 VENCEU"

                else:

                    winner_text = "EMPATE"

                game_state = "winner"

        # -------------------------------------------------
        # MORTE
        # -------------------------------------------------

        if not player1.alive:

            winner_text = "PLAYER 2 VENCEU"
            game_state = "winner"

        elif not player2.alive:

            winner_text = "PLAYER 1 VENCEU"
            game_state = "winner"

    # -----------------------------------------------------
    # DESENHO
    # -----------------------------------------------------

    draw_background()

    player1.draw(SCREEN)
    player2.draw(SCREEN)

    draw_hud(
        player1,
        player2,
        timer
    )

    # -----------------------------------------------------
    # VITÓRIA
    # -----------------------------------------------------

    if game_state == "winner":

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 150)
        )

        SCREEN.blit(
            overlay,
            (0, 0)
        )

        draw_center_text(
            winner_text,
            70
        )

        info = SMALL_FONT.render(
            "Pressione ENTER para jogar novamente",
            True,
            WHITE
        )

        SCREEN.blit(
            info,
            (
                WIDTH // 2 - info.get_width() // 2,
                HEIGHT // 2 + 75
            )
        )

    pygame.display.flip()


pygame.quit()
sys.exit()