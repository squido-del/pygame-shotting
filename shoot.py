import pygame
import math
import random

pygame.init()

WIDTH = 1920
HEIGHT = 1120

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("blockeron")

clock = pygame.time.Clock()

# ── UPGRADES ──────────────────────────────────────────────────────────────────
# To add a new upgrade: just add a new dict to this list. Nothing else to change. = 
ALL_UPGRADES= [
    {
        "name": "Speed Boost",
        "desc": "+2 move speed",
        "color": (100, 180, 255),
        "apply": lambda p: setattr(p, "speed", p.speed + 2),
    },
    {
        "name": "Big Bullets",
        "desc": "Bullet radius +4",
        "color": (255, 180, 0),
        "apply": lambda p: setattr(p, "bullet_radius", p.bullet_radius + 4),
    },
    {
        "name": "Heal",
        "desc": "Restore 30 HP",
        "color": (80, 220, 80),
        "apply": lambda p: setattr(p, "health", min(p.health + 30, 200)),
    },
]


class Player:
    def __init__(self):
        self.radius = 20
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.speed = 5
        self.color = (255, 255, 255)
        self.health = 100
        self.bullet_radius = 5
        self.bullet_speed = 8

    def move(self, keys):
        if keys[pygame.K_w]: self.y -= self.speed
        if keys[pygame.K_s]: self.y += self.speed
        if keys[pygame.K_a]: self.x -= self.speed
        if keys[pygame.K_d]: self.x += self.speed
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

    def draw(self):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)


class Enemy:
    def __init__(self, x, y, enemy_type):
        self.x = x
        self.y = y
        self.damage_cooldown = 0

        if enemy_type == "normal":
            self.speed = 3;   self.radius = 15; self.health = 1
        elif enemy_type == "fast":
            self.speed = 5;   self.radius = 10; self.health = 1
        elif enemy_type == "tank":
            self.speed = 1.5; self.radius = 25; self.health = 3
        else:
            self.speed = 3;   self.radius = 15; self.health = 1

    def update(self, player_x, player_y):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist != 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1

    def draw(self):
        pygame.draw.circle(screen, (255, 60, 60), (int(self.x), int(self.y)), self.radius)


class Bullet:
    def __init__(self, x, y, dx, dy, speed, radius):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = speed
        self.radius = radius

    def update(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

    def draw(self):
        pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), self.radius)


class UpgradeDrop:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self._pulse = 0

    def draw(self):
        self._pulse += 0.1
        r = self.radius + int(math.sin(self._pulse) * 3)
        pygame.draw.circle(screen, (0, 220, 220), (int(self.x), int(self.y)), r)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), r, 2)


def draw_upgrade_menu(options):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    title = pygame.font.SysFont(None, 52).render("CHOOSE AN UPGRADE", True, (255, 220, 0))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 150))

    card_w, card_h = 260, 90
    gap = 20
    total_w = len(options) * card_w + (len(options) - 1) * gap
    start_x = WIDTH // 2 - total_w // 2
    f = pygame.font.SysFont(None, 30)
    rects = []

    for i, opt in enumerate(options):
        x = start_x + i * (card_w + gap)
        y = HEIGHT // 2 - card_h // 2 
        rect = pygame.Rect(x, y, card_w, card_h)
        pygame.draw.rect(screen, (30, 30, 60), rect, border_radius=10)
        name = f.render(opt["name"], True, opt["color"])
        desc = f.render(opt["desc"], True, (200, 200, 200))
        screen.blit(name, (x + card_w // 2 - name.get_width() // 2, y + 18))
        screen.blit(desc, (x + card_w // 2 - desc.get_width() // 2, y + 52))
        rects.append((rect, opt))

    return rects


def reset_game():
    player = Player()
    enemies = [Enemy(100, 100, "tank"), Enemy(700, 100, "tank"), Enemy(100, 400, "fast")]
    return player, enemies, [], [], 0, 1, 2000


# ── state ─────────────────────────────────────────────────────────────────────
player, enemies, bullets, upgrade_drops, kills, wave, spawn_delay = reset_game()
spawn_timer = 0
last_drop_milestone = 0
game_over = False
upgrade_menu_active = False
upgrade_options = []
upgrade_option_rects = []
font = pygame.font.SysFont(None, 30)

running = True
while running:
    dt = clock.tick(60)
    screen.fill((30, 30, 30))

    # ── events ────────────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_over:
            player, enemies, bullets, upgrade_drops, kills, wave, spawn_delay = reset_game()
            spawn_timer = 0
            last_drop_milestone = 0
            upgrade_menu_active = False
            game_over = False

        if upgrade_menu_active:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, opt in upgrade_option_rects:
                    if rect.collidepoint(event.pos):
                        opt["apply"](player)
                        upgrade_menu_active = False
            continue  # freeze game while menu is open

        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            mx, my = pygame.mouse.get_pos()

            dx, dy = mx - player.x, my - player.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist != 0:
                dx /= dist; dy /= dist
            bullets.append(Bullet(player.x, player.y, dx, dy, player.bullet_speed, player.bullet_radius))

    # ── upgrade menu ──────────────────────────────────────────────────────────
    if upgrade_menu_active:
        for e in enemies: e.draw()
        for b in bullets: b.draw()
        for d in upgrade_drops: d.draw()
        player.draw()
        upgrade_option_rects = draw_upgrade_menu(upgrade_options)
        pygame.display.update()
        continue

    # ── game update ───────────────────────────────────────────────────────────
    if not game_over:
        player.move(pygame.key.get_pressed())

        for enemy in enemies[:]:
            enemy.update(player.x, player.y)
            dx, dy = player.x - enemy.x, player.y - enemy.y
            if math.sqrt(dx**2 + dy**2) < player.radius + enemy.radius:
                if enemy.damage_cooldown == 0:
                    player.health -= 10
                    enemy.damage_cooldown = 30
            enemy.draw()

        for bullet in bullets[:]:
            bullet.update()
            if not (0 <= bullet.x <= WIDTH and 0 <= bullet.y <= HEIGHT):
                bullets.remove(bullet)
                continue
            hit = False
            for enemy in enemies[:]:
                dx, dy = bullet.x - enemy.x, bullet.y - enemy.y
                if math.sqrt(dx**2 + dy**2) < bullet.radius + enemy.radius:
                    enemy.health -= 1
                    if enemy.health <= 0:
                        enemies.remove(enemy)
                        kills += 1
                        milestone = kills // 10
                        if milestone > last_drop_milestone:
                            last_drop_milestone = milestone
                            upgrade_drops.append(UpgradeDrop(enemy.x, enemy.y))
                    hit = True
                    break
            if hit:
                bullets.remove(bullet)
            else:
                bullet.draw()

        for drop in upgrade_drops[:]:
            dx, dy = player.x - drop.x, player.y - drop.y
            if math.sqrt(dx**2 + dy**2) < player.radius + drop.radius:
                upgrade_drops.remove(drop)
                upgrade_menu_active = True
                upgrade_options = random.sample(ALL_UPGRADES, min(3, len(ALL_UPGRADES)))
            else:
                drop.draw()

        if player.health <= 0:
            game_over = True

        spawn_timer += dt
        if spawn_timer > spawn_delay:
            spawn_timer = 0
            for _ in range(wave):
                side = random.choice(["top", "bottom", "left", "right"])
                if side == "top":      x, y = random.randint(0, WIDTH), 0
                elif side == "bottom": x, y = random.randint(0, WIDTH), HEIGHT
                elif side == "left":   x, y = 0, random.randint(0, HEIGHT)
                else:                  x, y = WIDTH, random.randint(0, HEIGHT)
                enemies.append(Enemy(x, y, random.choice(["normal", "fast", "tank"])))

        new_wave = kills // 10 + 1
        if new_wave != wave:
            wave = new_wave
            spawn_delay = max(500, 2000 - (wave - 1) * 200)

    player.draw()

    # ── HUD ───────────────────────────────────────────────────────────────────
    screen.blit(font.render(f"Health: {player.health}", True, (255, 255, 255)), (10, 10))
    screen.blit(font.render(f"Wave: {wave}", True, (255, 255, 255)), (10, 40))
    screen.blit(font.render(f"Kills: {kills}", True, (255, 255, 255)), (10, 70))

    if game_over:
        over = pygame.font.SysFont(None, 52).render("GAME OVER - Press R to Restart", True, (255, 0, 0))
        screen.blit(over, (WIDTH // 2 - over.get_width() // 2, HEIGHT // 2))

    pygame.display.update()

pygame.quit()