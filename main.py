import pygame
import sys
import random

pygame.init()

# Set up the game window
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
WINDOW_TITLE = 'Python Invaders'
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

pygame.display.set_caption(WINDOW_TITLE)

# Set up the clock for consistent frame rate
clock = pygame.time.Clock()
FPS = 60

wave = 1

# Load the player's spaceship image
player_image = pygame.image.load('player.png')

# Create a player object
player_x = WINDOW_WIDTH / 2 - player_image.get_width() / 2
player_y = WINDOW_HEIGHT - player_image.get_height() - 10
player_speed = 5
player_rect = pygame.Rect(player_x, player_y, player_image.get_width(),
                          player_image.get_height())

# Load the bullet image
bullet_image = pygame.image.load('bullet.png')
bullet_speed = 10
player_bullet_rect = None

# Load the enemy bullet image
enemy_bullet_image = pygame.image.load('enemy_bullet.png')
enemy_bullet_speed = 5
enemy_bullets = []
# Bullet trails list
bullet_trails = []
# Bullet trail duration
BULLET_TRAIL_DURATION = 1000  # in milliseconds


def draw_triangle(surface, x, y, width, height, color):
    pygame.draw.polygon(surface, color, [(x + width // 2, y), (x, y + height),
                                         (x + width, y + height)])


def get_faded_color(current_time):
    fade_duration = 750
    t = (current_time % fade_duration) / fade_duration
    if t > 0.5:
        t = 1 - t
    blue = (128, 128, 128)
    purple = (0, 0, 0)
    r = blue[0] + t * (purple[0] - blue[0])
    g = blue[1] + t * (purple[1] - blue[1])
    b = blue[2] + t * (purple[2] - blue[2])
    return int(r), int(g), int(b)


def draw_rotated_triangle(surface, x, y, width, height, rotation, color):
    triangle_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    draw_triangle(triangle_surface, 0, 0, width, height, color)
    rotated_triangle_surface = pygame.transform.rotate(triangle_surface,
                                                       rotation)
    surface.blit(rotated_triangle_surface,
                 (x - rotated_triangle_surface.get_width() // 2,
                  y - rotated_triangle_surface.get_height() // 2))


# Load the enemy images
enemy_images = [
    pygame.image.load('enemy1.png'),
    pygame.image.load('enemy2.png')
]

# Add an animation timer
ENEMY_ANIMATION_DELAY = 1000
ENEMY_ROW_COUNT = 8
last_enemy_animation_time = pygame.time.get_ticks()
enemy_image_index = 0

# Load the explosion image
explosion_image = pygame.image.load('explosion2.png')

# Create a list to store active explosions
explosions = []

# Explosion duration
EXPLOSION_DURATION = 150  # in milliseconds


def create_explosion(x, y):
    explosion = {
        'rect':
        pygame.Rect(x, y, explosion_image.get_width(),
                    explosion_image.get_height()),
        'start_time':
        pygame.time.get_ticks()
    }
    explosions.append(explosion)


# Create enemy objects
enemies = []
for row in range(2):
    for i in range(ENEMY_ROW_COUNT):

        enemy_x = WINDOW_WIDTH * 0.25 + i * (enemy_images[0].get_width() + 10)
        enemy_y = (enemy_images[0].get_height() + 10) * row + 50
        enemy_rect = pygame.Rect(enemy_x, enemy_y, enemy_images[0].get_width(),
                                 enemy_images[0].get_height())
        enemies.append(enemy_rect)

enemy_speed = 1
max_enemy_speed = 10  # Set the maximum enemy speed
enemy_direction = 1
enemies_down_speed = 30
enemies_destroyed = 0


def move_enemies():
    global enemies, enemy_speed, enemy_direction, enemies_down_speed, game_state
    move_down = False
    for enemy_rect in enemies:
        if (enemy_rect.left <= WINDOW_WIDTH * 0.10 and enemy_direction
                == -1) or (enemy_rect.right >= WINDOW_WIDTH * 0.90
                           and enemy_direction == 1):
            move_down = True
            break

    if move_down:
        enemy_direction *= -1
        for enemy_rect in enemies:
            enemy_rect.move_ip(0, enemies_down_speed)
        
    else:
        for enemy_rect in enemies:
            enemy_rect.move_ip(enemy_speed * enemy_direction, 0)
    if enemy_rect[1] >= WINDOW_HEIGHT:
            game_state = 'game_over'


def enemy_shoot():
    shooting_enemy = random.choice(enemies)
    enemy_bullet_x, enemy_bullet_y = shooting_enemy.centerx - enemy_bullet_image.get_width(
    ) // 2, shooting_enemy.bottom
    target_x, target_y = player_rect.centerx - enemy_bullet_x, player_rect.centery - enemy_bullet_y
    normalized_x, normalized_y = normalize_vector(target_x, target_y)
    velocity_x, velocity_y = normalized_x * enemy_bullet_speed, normalized_y * enemy_bullet_speed
    enemy_bullet_rect = {
        'rect':
        pygame.Rect(enemy_bullet_x, enemy_bullet_y,
                    enemy_bullet_image.get_width(),
                    enemy_bullet_image.get_height()),
        'velocity': (velocity_x, velocity_y),
        'trails': []
    }  # Add the 'trails' key

    enemy_bullets.append(enemy_bullet_rect)


def draw_text(surface, text, x, y, size, color):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)


# Player lives and score
lives = 3
score = 0

# Enemy shooting timer
ENEMY_SHOOT_DELAY = 1000
last_enemy_shoot_time = pygame.time.get_ticks()


def show_end_screen():
    screen.fill((0, 0, 0))
    draw_text(screen, "GAME OVER", WINDOW_WIDTH // 2 - 200,
              WINDOW_HEIGHT // 2 - 100, 72, (255, 255, 255))
    draw_text(screen, "Press R to restart or Q to quit",
              WINDOW_WIDTH // 2 - 300, WINDOW_HEIGHT // 2, 36, (255, 255, 255))
    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # Do not restart
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True  # Restart
                elif event.key == pygame.K_q:
                    return False  # Do not restart


def reset_game(rowing):
    global player_rect, player_bullet_rect, enemy_bullets, enemies, score, enemies_destroyed, enemy_speed, lives, game_over

    # Reset player position
    player_rect.x = WINDOW_WIDTH / 2 - player_image.get_width() / 2
    player_rect.y = WINDOW_HEIGHT - player_image.get_height() - 10

    # Reset bullets
    player_bullet_rect = None
    enemy_bullets = []

    # Reset enemies
    enemies = []
    for row in range(rowing):
        for i in range(ENEMY_ROW_COUNT):
            enemy_x = WINDOW_WIDTH * 0.25 + i * (enemy_images[0].get_width() +
                                                 10)
            enemy_y = (enemy_images[0].get_height() + 10) * row + 50
            enemy_rect = pygame.Rect(enemy_x, enemy_y,
                                     enemy_images[0].get_width(),
                                     enemy_images[0].get_height())
            enemies.append(enemy_rect)

    # Reset lives and score
    if game_over == True:
        lives = 3
        score = 0

    # Reset enemy speed
    enemy_speed = 1
    enemies_destroyed = 0


def normalize_vector(x, y):
    magnitude = (x**2 + y**2)**0.5
    if magnitude == 0:
        return 0, 0
    return x / magnitude, y / magnitude


def move_enemy_bullets():
    global enemy_bullets
    for enemy_bullet in enemy_bullets[:]:
        enemy_bullet_rect = enemy_bullet['rect']
        velocity_x, velocity_y = enemy_bullet['velocity']
        enemy_bullet_rect.move_ip(velocity_x, velocity_y)

        # Add bullet trail
        current_time = pygame.time.get_ticks()
        trail = {
            'position': (enemy_bullet_rect.centerx, enemy_bullet_rect.centery),
            'start_time': current_time
        }
        enemy_bullet['trails'].append(trail)

        # Update the alpha value of the trails
        for trail in enemy_bullet['trails']:
            time_since_creation = current_time - trail['start_time']
            alpha = max(
                0, 255 - int(
                    (time_since_creation / BULLET_TRAIL_DURATION) * 255))
            # trail['color'] = (128, 0, 0, alpha)

        # Remove bullets that leave the screen and their trails
        if enemy_bullet_rect.top > WINDOW_HEIGHT:
            enemy_bullets.remove(enemy_bullet)


def pause_menu():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()
                elif event.key == pygame.K_ESCAPE:
                    return

        screen.fill((0, 0, 32))  # fill screen with black
        draw_text(screen, "PAUSED", WINDOW_WIDTH // 2 - 200,
                  WINDOW_HEIGHT // 2 - 100, 72, (255, 255, 255))
        draw_text(screen, "Press ESC to continue or Q to quit",
                  WINDOW_WIDTH // 2 - 300, WINDOW_HEIGHT // 2, 36,
                  (255, 255, 255))
        pygame.display.update()


def process_events():
    global player_rect, player_speed, is_shooting, player_bullet_rect

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pause_menu()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                is_shooting = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                is_shooting = False


# Game loop
is_shooting = False  # add this variable to keep track of shooting status
game_state = "running"
running = True
game_over = False

while running:
    if not game_over:
        # All the game logic and rendering code here, e.g.:
        # - Event handling
        # - Moving and updating game objects
        # - Collision detection
        # - Drawing game elements on the screen

        # Check if the game is over
        process_events()
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pause_menu()

        clock.tick(FPS)

        # Update player bullet object only if is_shooting is True
        if is_shooting:
            if not player_bullet_rect:
                player_bullet_x, player_bullet_y = player_rect.centerx - bullet_image.get_width(
                ) // 2, player_rect.top
                player_bullet_rect = pygame.Rect(player_bullet_x,
                                                 player_bullet_y,
                                                 bullet_image.get_width(),
                                                 bullet_image.get_height())
            else:
                player_bullet_rect.move_ip(0, -bullet_speed)
                if player_bullet_rect.top <= 0:
                    player_bullet_rect = None

        # Move the player's spaceship
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_rect.left > 0:
            player_rect.move_ip(-player_speed, 0)
        if keys[pygame.K_RIGHT] and player_rect.right < WINDOW_WIDTH:
            player_rect.move_ip(player_speed, 0)

        # Move the player's bullet
        if player_bullet_rect is not None:
            player_bullet_rect.move_ip(0, -bullet_speed)
            if player_bullet_rect.bottom < 0:
                player_bullet_rect = None

        # Move the enemies
        move_enemies()

        # Update the animation delay based on the enemy speed
        ENEMY_ANIMATION_DELAY = max(100, int(1000 / (1 + enemy_speed)))

        # Update the animation timer and enemy_image_index inside the game loop
        current_time = pygame.time.get_ticks()
        if current_time - last_enemy_animation_time > ENEMY_ANIMATION_DELAY:
            enemy_image_index = (enemy_image_index + 1) % len(enemy_images)
            last_enemy_animation_time = current_time

        # Enemy shooting
        current_time = pygame.time.get_ticks()
        if current_time - last_enemy_shoot_time > (
                ENEMY_SHOOT_DELAY - (0.1 * ENEMY_SHOOT_DELAY * wave)):
            enemy_shoot()
            last_enemy_shoot_time = current_time

        # Move enemy bullets
        move_enemy_bullets()

        # Detect collisions between the player's spaceship and the enemies
        for enemy_rect in enemies:
            if player_rect.colliderect(enemy_rect):
                lives -= 1
                if lives <= 0:
                    game_state = "game_over"
                else:
                    enemies.remove(enemy_rect)
                    break
            # if enemies.bottom >= WINDOW_HEIGHT:
            # game_over = True

        # Detect collisions between the player's bullets and the enemies
        if player_bullet_rect is not None:
            for i, enemy_rect in enumerate(enemies):
                if player_bullet_rect.colliderect(enemy_rect):
                    enemies.pop(i)
                    player_bullet_rect = None
                    enemies_destroyed += 1
                    if enemy_speed < max_enemy_speed:  # Check if enemy_speed is less than max_enemy_speed
                        enemy_speed += 0.03 * enemies_destroyed

                    score += 100
                    create_explosion(
                        enemy_rect.x, enemy_rect.y
                    )  # Creates an explosion at the enemy's position
                    break

        # Detect collisions between enemy bullets and the player
        for enemy_bullet in enemy_bullets[:]:
            if enemy_bullet['rect'].colliderect(player_rect):
                lives -= 1
                if lives <= 0:
                    game_state = "game_over"
                else:
                    enemy_bullets.remove(enemy_bullet)
                    create_explosion(
                        player_rect.x, player_rect.y
                    )  # Creates an explosion at the player's position
                    break

        # Update the explosion objects
        current_time = pygame.time.get_ticks()
        explosions = [
            explosion for explosion in explosions
            if current_time - explosion['start_time'] <= EXPLOSION_DURATION
        ]

        # Draw the game elements on the screen
        screen.fill((0, 0, 32))
        screen.blit(player_image, player_rect)
        for enemy_rect in enemies:
            screen.blit(enemy_images[enemy_image_index], enemy_rect)

        if player_bullet_rect is not None:
            screen.blit(bullet_image, player_bullet_rect)

        # Draw enemy bullets with rotation and color fading
        current_time = pygame.time.get_ticks()
        for enemy_bullet in enemy_bullets:
            bullet_color = get_faded_color(current_time)
            bullet_rotation = (current_time % 1000) * 360 / 1000
            draw_rotated_triangle(screen, enemy_bullet['rect'].centerx,
                                  enemy_bullet['rect'].centery, 14, 14,
                                  bullet_rotation, bullet_color)

        # Draw bullet trails
        static_red_color = (32, 32, 64
                            )  # A static red color for the bullet trails
        for enemy_bullet in enemy_bullets:
            for trail in enemy_bullet['trails']:
                time_since_creation = current_time - trail['start_time']
                alpha = max(0, 128 - int(
                    (time_since_creation / BULLET_TRAIL_DURATION) *
                    128))  # Use 128 as the initial alpha value
                rgba_color = (
                    *static_red_color, alpha
                )  # Use the static red color with the updated alpha value
                trail_surface = pygame.Surface(
                    (4, 4),
                    pygame.SRCALPHA)  # Create a surface with an alpha channel
                trail_surface.fill(rgba_color)
                screen.blit(trail_surface,
                            (trail['position'][0] - 2, trail['position'][1] -
                             2))  # Draw the trail with its alpha value

        # Draw the explosions on the screen
        for explosion in explosions:
            current_time = pygame.time.get_ticks()
            time_since_creation = current_time - explosion['start_time']
            alpha = max(
                0, 255 - int((time_since_creation / EXPLOSION_DURATION) * 255))

            # Apply the alpha value to the explosion image
            explosion_surface = explosion_image.copy(
            )  # Copy the explosion image to prevent modifying the original
            explosion_surface.set_alpha(alpha)
            screen.blit(explosion_surface, explosion['rect'])

        draw_text(screen, f"Lives: {lives}", 10, 10, 36, (255, 255, 255))
        draw_text(screen, f"Score: {score}", 10, 50, 36, (255, 255, 255))
        draw_text(screen, f"Wave: {wave}", 10, 90, 36, (255, 255, 255))
        draw_text(screen, f"debug: {enemy_rect}", 10, 130, 36, (255, 255, 255))

    if game_state == "game_over":
        if show_end_screen():  # Returns True if the player wants to restart
            wave = 1
            reset_game(wave + 1)
            game_state = "running"
        else:
            running = False

    # Check if all enemies are destroyed
    if len(enemies) == 0:
        wave += 1
        reset_game(wave + 1)

    pygame.display.update()
#        pygame.quit()
#        sys.exit()
