import pygame
from .paddle import Paddle
from .ball import Ball
from .brick import Brick
from .sounds import SoundManager

# Game Engine

WHITE = (255, 255, 255)
BG = (15, 15, 25)
BRICK_COLORS = [
    (200, 60, 60),
    (200, 140, 60),
    (200, 200, 60),
    (80, 180, 80),
    (80, 140, 200),
]

DIFFICULTIES = {
    "easy": {"ball_speed": 3, "paddle_width": 140},
    "medium": {"ball_speed": 4, "paddle_width": 100},
    "hard": {"ball_speed": 6, "paddle_width": 70},
}


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rows, self.cols = 5, 8
        self.font = pygame.font.SysFont("Arial", 28)
        self.big_font = pygame.font.SysFont("Arial", 40, bold=True)
        self.sounds = SoundManager()
        self.quit_requested = False
        self.state = "playing"  # "playing" | "end" | "difficulty"
        self.difficulty = "medium"
        self.new_game("medium")

    def new_game(self, difficulty="medium"):
        settings = DIFFICULTIES.get(difficulty, DIFFICULTIES["medium"])
        self.difficulty = difficulty

        paddle_w = settings["paddle_width"]
        self.paddle = Paddle(self.width // 2 - paddle_w // 2, self.height - 30, paddle_w, 14)

        self.ball_speed = settings["ball_speed"]
        self.ball = Ball(self.width // 2, self.height - 50, radius=8)
        self.ball.vx, self.ball.vy = self.ball_speed, -self.ball_speed

        self.bricks = self._build_bricks(self.rows, self.cols)

        self.lives = 3
        self.score = 0
        self.state = "playing"
        self.result = None

    def _build_bricks(self, rows, cols):
        bricks = []
        margin, gap, top = 30, 6, 60
        brick_w = (self.width - margin * 2 - gap * (cols - 1)) // cols
        brick_h = 22
        for r in range(rows):
            for c in range(cols):
                x = margin + c * (brick_w + gap)
                y = top + r * (brick_h + gap)
                bricks.append(Brick(x, y, brick_w, brick_h))
        return bricks

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "end":
            if event.key == pygame.K_r:
                self.state = "difficulty"
            elif event.key == pygame.K_q:
                self.quit_requested = True

        elif self.state == "difficulty":
            if event.key == pygame.K_e:
                self.new_game("easy")
            elif event.key == pygame.K_m:
                self.new_game("medium")
            elif event.key == pygame.K_h:
                self.new_game("hard")
            elif event.key == pygame.K_q:
                self.quit_requested = True

    def handle_input(self):
        if self.state != "playing":
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle.move(-self.paddle.speed, self.width)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle.move(self.paddle.speed, self.width)

    def _resolve_bounce(self, other_rect):
        """Flip the ball's velocity on whichever axis matches the side
        that was actually hit, instead of always flipping vy."""
        ball_rect = self.ball.rect()
        overlap_x = min(ball_rect.right, other_rect.right) - max(ball_rect.left, other_rect.left)
        overlap_y = min(ball_rect.bottom, other_rect.bottom) - max(ball_rect.top, other_rect.top)

        if overlap_x < overlap_y:
            self.ball.vx *= -1
        else:
            self.ball.vy *= -1

    def update(self):
        if self.state != "playing":
            return

        self.ball.move()

        if self.ball.x - self.ball.radius <= 0 or self.ball.x + self.ball.radius >= self.width:
            self.ball.vx *= -1
            self.sounds.play("wall")
        if self.ball.y - self.ball.radius <= 0:
            self.ball.vy *= -1
            self.sounds.play("wall")

        if self.ball.rect().colliderect(self.paddle.rect()):
            self._resolve_bounce(self.paddle.rect())
            self.sounds.play("paddle")

        for brick in self.bricks:
            if brick.alive and self.ball.rect().colliderect(brick.rect()):
                self._resolve_bounce(brick.rect())
                brick.alive = False
                self.score += 1
                self.sounds.play("brick")
                break

        if self.ball.y - self.ball.radius > self.height:
            self.lives -= 1
            if self.lives <= 0:
                self._end_game("lose")
            else:
                self._reset_ball()

        if all(not b.alive for b in self.bricks):
            self._end_game("win")

    def _end_game(self, result):
        self.result = result
        self.state = "end"
        self.sounds.play(result)

    def _reset_ball(self):
        self.ball.x, self.ball.y = self.width // 2, self.height - 50
        self.ball.vx, self.ball.vy = self.ball_speed, -self.ball_speed

    def render(self, screen):
        screen.fill(BG)

        pygame.draw.rect(screen, WHITE, self.paddle.rect())
        pygame.draw.circle(screen, WHITE, (int(self.ball.x), int(self.ball.y)), self.ball.radius)

        for i, brick in enumerate(self.bricks):
            if brick.alive:
                row = i // self.cols
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                pygame.draw.rect(screen, color, brick.rect())

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(lives_text, (self.width - 130, 10))

        if self.state == "end":
            self._render_end_overlay(screen)
        elif self.state == "difficulty":
            self._render_difficulty_overlay(screen)

    def _render_overlay_bg(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

    def _render_end_overlay(self, screen):
        self._render_overlay_bg(screen)
        title = "You Win!" if self.result == "win" else "Game Over"
        title_color = (80, 220, 120) if self.result == "win" else (220, 80, 80)

        title_surf = self.big_font.render(title, True, title_color)
        screen.blit(title_surf, title_surf.get_rect(center=(self.width // 2, self.height // 2 - 50)))

        score_surf = self.font.render(f"Final Score: {self.score}", True, WHITE)
        screen.blit(score_surf, score_surf.get_rect(center=(self.width // 2, self.height // 2)))

        hint_surf = self.font.render("Press R to Play Again or Q to Quit", True, WHITE)
        screen.blit(hint_surf, hint_surf.get_rect(center=(self.width // 2, self.height // 2 + 50)))

    def _render_difficulty_overlay(self, screen):
        self._render_overlay_bg(screen)
        title_surf = self.big_font.render("Select Difficulty", True, WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(self.width // 2, self.height // 2 - 60)))

        lines = ["E - Easy", "M - Medium", "H - Hard", "Q - Quit"]
        for idx, line in enumerate(lines):
            surf = self.font.render(line, True, WHITE)
            screen.blit(surf, surf.get_rect(center=(self.width // 2, self.height // 2 - 10 + idx * 36)))