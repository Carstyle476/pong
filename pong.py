
import pygame
from random import random, randint

WINDOW_SIZE: tuple[int, int] = (640, 480)
WINDOW_NAME: str = "Pong!"
TRANSPARENCY: int = 192
SCORE_TEXT_DIST: int = 12

MOVE_FORCE: int = 7500
MOVE_SLOWDOWN: int = 10
ENEMY_MOVE_FORCE: int = 7500
ENEMY_MOVE_SLOWDOWN: int = 10

PADDLE_SIZE: tuple[int, int] = (10, 90)
BALL_RADIUS: int = 5
START_DELAY: int = 1

PARTICLE_SPAWN_NOISE: int = 25
PARTICLE_VEL_NOISE: int = 100
PARTICLE_VEL_MULT: float = 0.5
PARTICLE_SPAWN_MIN: int = 10
PARTICLE_SPAWN_MAX: int = 20
PARTICLE_RADIUS: int = 1
PARTICLE_SLOWDOWN: int = 2

START_X: int = 200
X_INCREMENT: int = 20
X_MAX: int = 400
START_Y: int = 200


class Ball(pygame.sprite.Sprite):

    def __init__(self, wall_bounce_sound: pygame.mixer.Sound, radius: float, x: float, y: float, vel_x: float = 0, vel_y: float = 0) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 255), (radius, radius), radius)
        self.rect: pygame.Rect = self.image.get_rect(center=(int(x), int(y)))
        self.wall_bounce_sound: pygame.mixer.Sound = wall_bounce_sound
        self.radius: float = radius
        self.x: float = x
        self.y: float = y
        self.vel_x: float = vel_x
        self.vel_y: float = vel_y

    def update(self, dt: float) -> None:
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt

        if self.y < 0 or self.y > WINDOW_SIZE[1] - self.radius * 2:
            if self.y < 0: self.y = abs(self.y)
            else: self.y -= self.y - (WINDOW_SIZE[1] - self.radius * 2)
            self.vel_y *= -1
            self.wall_bounce_sound.play()

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)


class Particle(Ball):

    def __init__(self, wall_bounce_sound: pygame.mixer.Sound, radius: float, x: float, y: float, vel_x: float = 0, vel_y: float = 0, life: float = 1) -> None:
        super().__init__(wall_bounce_sound, radius, x, y, vel_x, vel_y)
        pygame.draw.circle(self.image, (255, 255, 255, max(0, min(255, int(life * 255)))), (radius, radius), radius)
        self.life = life

    def update(self, dt: float) -> None:
        self.vel_x -= self.vel_x * PARTICLE_SLOWDOWN * dt / 2
        self.vel_y -= self.vel_y * PARTICLE_SLOWDOWN * dt / 2
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        self.vel_x -= self.vel_x * PARTICLE_SLOWDOWN * dt / 2
        self.vel_y -= self.vel_y * PARTICLE_SLOWDOWN * dt / 2

        self.life -= dt
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (255, 255, 255, max(0, min(255, int(self.life * 255)))), (self.radius, self.radius), self.radius)
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)


class Paddle(pygame.sprite.Sprite):

    def __init__(self, size: tuple[int, int], x: float, y: float, vel_y: float = 0, ai: bool = False) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.Surface(size)
        self.image.fill((255, 255, 255))
        self.rect: pygame.Rect = self.image.get_rect(topleft=(int(x), int(y)))
        self.x: float = x
        self.y: float = y
        self.vel_y: float = vel_y
        self.ai: bool = ai

    def update(self, dt: float, ball_pos: tuple[float, float], ball_vel: tuple[float, float]) -> None:
        pending_accel_y: float = 0

        if self.ai:
            if ball_vel[0] < 0:
                # perfect prediction code
                predicted: float = ball_pos[1] + ball_vel[1] * (ball_pos[0] - self.x + self.rect.width / 2) / abs(ball_vel[0])
                while predicted < 0 or predicted > WINDOW_SIZE[1] - BALL_RADIUS * 2:
                    predicted = abs(predicted)
                    if predicted > WINDOW_SIZE[1] - BALL_RADIUS * 2: predicted -= (predicted - (WINDOW_SIZE[1] - BALL_RADIUS * 2)) * 2
                if predicted < self.y: pending_accel_y -= ENEMY_MOVE_FORCE
                elif predicted > self.y + self.rect.height: pending_accel_y += ENEMY_MOVE_FORCE
        else:
            keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
            if keys[pygame.K_w] or keys[pygame.K_UP]: pending_accel_y -= MOVE_FORCE
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: pending_accel_y += MOVE_FORCE

        pending_accel_y -= self.vel_y * (ENEMY_MOVE_SLOWDOWN if self.ai else MOVE_SLOWDOWN)

        self.vel_y += pending_accel_y * dt / 2
        self.y += self.vel_y * dt
        self.vel_y += pending_accel_y * dt / 2

        if self.y < 0 or self.y > WINDOW_SIZE[1] - self.rect.height:
            self.y = max(0, min(WINDOW_SIZE[1] - self.rect.height, self.y))
            self.vel_y = 0

        self.rect.y = int(self.y)


# return a tuple containing rendered text and its centering info
def text_rect_center(font: pygame.font.Font, text: str, color: tuple[int, int, int], pos: tuple[int, int]) -> tuple[pygame.Surface, pygame.Rect]:
    result: pygame.Surface = font.render(text, True, color)
    return (result, result.get_rect(center=pos))


def main() -> None:
    pygame.init()

    pygame.mixer.init()
    wall_bounce: pygame.mixer.Sound = pygame.mixer.Sound("sounds/wall_bounce.ogg")
    paddle_bounce: pygame.mixer.Sound = pygame.mixer.Sound("sounds/paddle_bounce.ogg")
    player_scored: pygame.mixer.Sound = pygame.mixer.Sound("sounds/player_scored.ogg")
    enemy_scored: pygame.mixer.Sound = pygame.mixer.Sound("sounds/enemy_scored.ogg")
    menu_move: pygame.mixer.Sound = pygame.mixer.Sound("sounds/menu_move.ogg")

    SMALL_FONT: pygame.font.Font = pygame.font.SysFont("Verdana", 24)
    BIG_FONT: pygame.font.Font = pygame.font.SysFont("Verdana", 48)

    MENU_TEXT: tuple[pygame.Surface, pygame.Rect] = text_rect_center(
        BIG_FONT,
        "Pong!",
        (255, 255, 255),
        (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 3)
    )

    MENU_INSTRUCTIONS: tuple[pygame.Surface, pygame.Rect] = text_rect_center(
        SMALL_FONT,
        "Space to play, Escape to exit",
        (255, 255, 255),
        (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
    )

    CONTROL_INSTRUCTIONS: tuple[pygame.Surface, pygame.Rect] = text_rect_center(
        SMALL_FONT,
        "W/S or up/down arrow keys",
        (255, 255, 255),
        (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] * 2 // 3)
    )

    PAUSE_TEXT: tuple[pygame.Surface, pygame.Rect] = text_rect_center(
        BIG_FONT,
        "Paused",
        (255, 255, 255),
        (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 3)
    )

    PAUSE_INSTRUCTIONS: tuple[pygame.Surface, pygame.Rect] = text_rect_center(
        SMALL_FONT,
        "Space to continue, Escape to exit",
        (255, 255, 255),
        (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] * 2 // 3)
    )

    screen: pygame.Surface = pygame.display.set_mode(WINDOW_SIZE, pygame.SCALED, vsync=1)
    transparent: pygame.Surface = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
    pygame.display.set_caption(WINDOW_NAME)
    clock: pygame.time.Clock = pygame.time.Clock()

    # ugh i have to initialize these twice
    running: bool = True
    paused: bool = False
    start_timer: float = START_DELAY
    player_score: int = 0
    enemy_score: int = 0
    player_score_render: pygame.Surface = SMALL_FONT.render(str(player_score), True, (255, 255, 255))
    enemy_score_render: pygame.Surface = SMALL_FONT.render(str(enemy_score), True, (255, 255, 255))

    particles: pygame.sprite.Group = pygame.sprite.Group()
    all_sprites: pygame.sprite.Group = pygame.sprite.Group()
    player: Paddle = Paddle(PADDLE_SIZE, WINDOW_SIZE[0] - PADDLE_SIZE[0] * 2, WINDOW_SIZE[1] / 2 - PADDLE_SIZE[1] / 2)
    enemy: Paddle = Paddle(PADDLE_SIZE, PADDLE_SIZE[0], WINDOW_SIZE[1] / 2 - PADDLE_SIZE[1] / 2, ai=True)
    ball: Ball = Ball(wall_bounce, BALL_RADIUS, WINDOW_SIZE[0] / 2 - BALL_RADIUS, WINDOW_SIZE[1] / 2 - BALL_RADIUS)

    def setup_game(reset_score: bool) -> None:
        # questionable line of code
        nonlocal paused, start_timer, player_score, enemy_score, player_score_render, enemy_score_render, particles, all_sprites, player, enemy, ball

        paused = False
        start_timer = START_DELAY
        if reset_score:
            player_score = 0
            enemy_score = 0
        player_score_render = SMALL_FONT.render(str(player_score), True, (255, 255, 255))
        enemy_score_render = SMALL_FONT.render(str(enemy_score), True, (255, 255, 255))

        particles = pygame.sprite.Group()
        all_sprites = pygame.sprite.Group()
        player = Paddle(PADDLE_SIZE, WINDOW_SIZE[0] - PADDLE_SIZE[0] * 2, WINDOW_SIZE[1] / 2 - PADDLE_SIZE[1] / 2)
        enemy = Paddle(PADDLE_SIZE, PADDLE_SIZE[0], WINDOW_SIZE[1] / 2 - PADDLE_SIZE[1] / 2, ai=True)
        ball = Ball(wall_bounce, BALL_RADIUS, WINDOW_SIZE[0] / 2 - BALL_RADIUS, WINDOW_SIZE[1] / 2 - BALL_RADIUS)
        all_sprites.add(player)
        all_sprites.add(enemy)
        all_sprites.add(ball)

    # 0 = menu
    # 1 = game
    # 2 = game over
    # transitions: 0-1, 1-2, 2-0, 2-1
    state: int = 0


    # game loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if state == 0:
                    if event.key == pygame.K_SPACE:
                        state = 1
                        setup_game(True)
                        menu_move.play()
                    elif event.key == pygame.K_ESCAPE: running = False
                elif state == 1:
                    if paused:
                        if event.key == pygame.K_ESCAPE:
                            state = 0
                            menu_move.play()
                        elif event.key == pygame.K_SPACE:
                            paused = False
                            menu_move.play()
                    elif event.key == pygame.K_ESCAPE:
                        paused = True
                        menu_move.play()

        dt: float = clock.tick() / 1000
        transparent.fill((0, 0, 0, TRANSPARENCY)) # drawing background with transparency makes a cool fake motion blur effect
        screen.blit(transparent, (0, 0))

        if state == 0: # menu (nothing interesting)
            screen.blit(MENU_TEXT[0], MENU_TEXT[1])
            screen.blit(MENU_INSTRUCTIONS[0], MENU_INSTRUCTIONS[1])
            screen.blit(CONTROL_INSTRUCTIONS[0], CONTROL_INSTRUCTIONS[1])
        elif state == 1: # game
            if not(paused):
                if start_timer < 0:
                    ball.vel_x = START_X
                    if random() > 0.5: ball.vel_x *= -1
                    ball.vel_y = random() * 2 * START_Y - START_Y
                    start_timer = 0
                elif start_timer > 0: start_timer -= dt

                ball_pos: tuple[float, float] = (ball.x, ball.y)
                ball_vel: tuple[float, float] = (ball.vel_x, ball.vel_y)
                player.update(dt, ball_pos, ball_vel)
                enemy.update(dt, ball_pos, ball_vel)
                ball.update(dt)
                particles.update(dt)

                if ball.x < 0 or ball.x > WINDOW_SIZE[0] - ball.radius * 2:
                    if ball.x < 0:
                        player_score += 1
                        player_scored.play()
                    else:
                        enemy_score += 1
                        enemy_scored.play()
                    setup_game(False)

                # ball-paddle collision
                hit_player: bool = ball.rect.colliderect(player.rect)
                if hit_player or ball.rect.colliderect(enemy.rect):
                    ball.vel_x *= -1
                    if hit_player: ball.x -= ball.x + ball.radius * 2 - player.x
                    else: ball.x += enemy.x + enemy.rect.width - ball.x

                    bounce_off: Paddle = player if hit_player else enemy
                    ball.vel_y += bounce_off.vel_y
                    if abs(ball.vel_x) < X_MAX:
                        sign: float = ball.vel_x / abs(ball.vel_x)
                        ball.vel_x += X_INCREMENT * sign # it gets a little faster every time
                    paddle_bounce.play()
                    
                    for i in range(randint(PARTICLE_SPAWN_MIN, PARTICLE_SPAWN_MAX + 1)):
                        particles.add(Particle(
                            wall_bounce,
                            PARTICLE_RADIUS,
                            ball.x + ball.radius - PARTICLE_RADIUS,
                            ball.y + ball.radius - PARTICLE_RADIUS,
                            ball.vel_x * PARTICLE_VEL_MULT + random() * 2 * PARTICLE_VEL_NOISE - PARTICLE_VEL_NOISE,
                            ball.vel_y * PARTICLE_VEL_MULT + random() * 2 * PARTICLE_VEL_NOISE - PARTICLE_VEL_NOISE,
                            random() * 0.2 - 0.1 + 0.9
                        ))


                to_delete: list[Particle] = []
                for particle in particles:
                    if particle.life <= 0: to_delete.append(particle)
                for particle in to_delete: particles.remove(particle)

            screen.blit(player_score_render, player_score_render.get_rect(topleft=(WINDOW_SIZE[0] / 2 + SCORE_TEXT_DIST, 0)))
            screen.blit(enemy_score_render, enemy_score_render.get_rect(topright=(WINDOW_SIZE[0] / 2 - SCORE_TEXT_DIST, 0)))
            particles.draw(screen)
            all_sprites.draw(screen)
            if paused:
                screen.blit(transparent, (0, 0))
                screen.blit(PAUSE_TEXT[0], PAUSE_TEXT[1])
                screen.blit(PAUSE_INSTRUCTIONS[0], PAUSE_INSTRUCTIONS[1])

        pygame.display.flip()


    pygame.quit()

if __name__ == "__main__": main()
