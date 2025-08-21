# stylish_snake_full.py
# Advanced Stylish Snake Game with optional sounds (bgm, eat, gameover)
# Requirements: pygame
# Run: python stylish_snake_full.py

import pygame, sys, random, os, math, time

# ---------------- CONFIG ----------------
GRID_SIZE = 20
GRID_W, GRID_H = 30, 20
SCREEN_W, SCREEN_H = GRID_W * GRID_SIZE, GRID_H * GRID_SIZE
FPS = 60

BG_TOP = (10, 16, 36)
BG_BOTTOM = (36, 16, 50)

SNAKE_COLOR = (0, 210, 160)
SNAKE_HEAD_COLOR = (200, 255, 220)
FOOD_COLOR = (255, 95, 85)

START_SPEED = 7
SPEED_INCREASE_EVERY = 5
MAX_SPEED = 24

HIGHSCORE_FILE = "highscore_pro.txt"
SOUND_BGM = "bgm.mp3"        # optional background music
SOUND_EAT = "eat.wav"        # optional eat sound
SOUND_GAMEOVER = "gameover.wav"
# ----------------------------------------

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Stylish Snake - Pro")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 18)
bigfont = pygame.font.SysFont("consolas", 40, bold=True)

# ---------------- Sounds (optional, safe fallback) ----------------
sounds = {"bgm": None, "eat": None, "gameover": None}
def load_sounds():
    # load if present, else keep None
    try:
        if os.path.exists(SOUND_BGM):
            sounds["bgm"] = pygame.mixer.Sound(SOUND_BGM)
            sounds["bgm"].set_volume(0.35)
    except Exception:
        sounds["bgm"] = None
    try:
        if os.path.exists(SOUND_EAT):
            sounds["eat"] = pygame.mixer.Sound(SOUND_EAT)
            sounds["eat"].set_volume(0.6)
    except Exception:
        sounds["eat"] = None
    try:
        if os.path.exists(SOUND_GAMEOVER):
            sounds["gameover"] = pygame.mixer.Sound(SOUND_GAMEOVER)
            sounds["gameover"].set_volume(0.6)
    except Exception:
        sounds["gameover"] = None

load_sounds()

def play_bgm(loop=-1):
    if sounds["bgm"]:
        sounds["bgm"].play(loops=loop)
def stop_bgm():
    if sounds["bgm"]:
        sounds["bgm"].stop()
def play_eat():
    if sounds["eat"]:
        sounds["eat"].play()
def play_gameover_sound():
    if sounds["gameover"]:
        sounds["gameover"].play()

# ---------------- Highscore ----------------
def load_highscore():
    try:
        if os.path.exists(HIGHSCORE_FILE):
            return int(open(HIGHSCORE_FILE).read().strip() or 0)
    except:
        pass
    return 0
def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(score))
    except:
        pass

# ---------------- Drawing helpers ----------------
def draw_gradient(surf, top_color, bottom_color):
    h = surf.get_height()
    for y in range(h):
        t = y / (h - 1)
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (surf.get_width(), y))

def draw_grid_overlay(surf):
    alpha = 18
    grid_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    for x in range(0, SCREEN_W, GRID_SIZE):
        pygame.draw.line(grid_surf, (255,255,255,alpha), (x,0),(x,SCREEN_H))
    for y in range(0, SCREEN_H, GRID_SIZE):
        pygame.draw.line(grid_surf, (255,255,255,alpha), (0,y),(SCREEN_W,y))
    surf.blit(grid_surf, (0,0))

def cell_to_px(cell):
    return (cell[0]*GRID_SIZE + GRID_SIZE//2, cell[1]*GRID_SIZE + GRID_SIZE//2)

def rand_empty_cell(occupied):
    while True:
        c = (random.randrange(1, GRID_W-1), random.randrange(1, GRID_H-1))
        if c not in occupied:
            return c

def draw_glowing_food(surf, center, base_r, t):
    glow = pygame.Surface((base_r*6, base_r*6), pygame.SRCALPHA)
    cx = glow.get_width()//2
    cy = glow.get_height()//2
    pulse = 0.8 + 0.45 * math.sin(t * 3.0)
    max_r = int(base_r * 2.2 * pulse)
    for i in range(max_r, 0, -1):
        alpha = int(40 * (1 - i / max_r))
        color = (FOOD_COLOR[0], FOOD_COLOR[1], FOOD_COLOR[2], alpha)
        pygame.draw.circle(glow, color, (cx, cy), i)
    surf.blit(glow, (center[0]-cx, center[1]-cy), special_flags=pygame.BLEND_PREMULTIPLIED)
    pygame.draw.circle(surf, FOOD_COLOR, center, base_r)

def draw_snake(surf, snake, dir_vec):
    # smoother body using circles, size tapering
    L = len(snake)
    for idx, cell in enumerate(snake):
        center = cell_to_px(cell)
        # size larger near head, smaller tail
        size = int(GRID_SIZE * (0.9 - (idx / max(1, L)) * 0.45))
        size = max(4, size)
        color = SNAKE_COLOR if idx != 0 else SNAKE_HEAD_COLOR
        pygame.draw.circle(surf, color, center, size//2)
    # head eye
    head_center = cell_to_px(snake[0])
    eye_offset = (dir_vec[0]*GRID_SIZE//4, dir_vec[1]*GRID_SIZE//4)
    eye_pos = (head_center[0]+eye_offset[0], head_center[1]+eye_offset[1])
    pygame.draw.circle(surf, (10,10,10), eye_pos, max(2, GRID_SIZE//10))

# ---------------- Main gameplay ----------------
def play_game():
    # initialize
    start = (GRID_W//2, GRID_H//2)
    snake = [start, (start[0]-1,start[1]), (start[0]-2,start[1])]
    dir_vec = (1,0)
    pending = dir_vec
    occupied = set(snake)
    food = rand_empty_cell(occupied)
    score = 0
    high = load_highscore()
    paused = False
    game_over = False

    # timing
    speed = START_SPEED
    move_interval = 1.0 / speed
    last_move = time.time()
    t_total = 0.0

    # start/play bgm if available
    play_bgm()

    while True:
        dt = clock.tick(FPS) / 1000.0
        t_total += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE,):
                    pygame.quit(); sys.exit()
                if ev.key == pygame.K_p:
                    if not game_over:
                        paused = not paused
                if ev.key == pygame.K_r:
                    if game_over:
                        stop_bgm()
                        return
                if not paused and not game_over:
                    if ev.key in (pygame.K_UP, pygame.K_w):
                        if dir_vec != (0,1): pending = (0,-1)
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        if dir_vec != (0,-1): pending = (0,1)
                    elif ev.key in (pygame.K_LEFT, pygame.K_a):
                        if dir_vec != (1,0): pending = (-1,0)
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        if dir_vec != (-1,0): pending = (1,0)

        # update speed by score
        speed = min(MAX_SPEED, START_SPEED + score // SPEED_INCREASE_EVERY)
        move_interval = 1.0 / speed

        now = time.time()
        if (not paused) and (not game_over) and (now - last_move) >= move_interval:
            last_move = now
            dir_vec = pending
            new_head = (snake[0][0] + dir_vec[0], snake[0][1] + dir_vec[1])
            # collisions
            if new_head[0] <= 0 or new_head[0] >= GRID_W-1 or new_head[1] <= 0 or new_head[1] >= GRID_H-1:
                game_over = True
                stop_bgm()
                play_gameover_sound()
            elif new_head in snake:
                game_over = True
                stop_bgm()
                play_gameover_sound()
            else:
                snake.insert(0, new_head)
                if new_head == food:
                    score += 1
                    play_eat()
                    occupied = set(snake)
                    food = rand_empty_cell(occupied)
                    if score > high:
                        high = score
                        save_highscore(high)
                else:
                    snake.pop()

        # draw
        bg = pygame.Surface((SCREEN_W, SCREEN_H))
        draw_gradient(bg, BG_TOP, BG_BOTTOM)
        screen.blit(bg, (0,0))
        draw_grid_overlay(screen)

        # inner surface for effects
        inner = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        draw_glowing_food(inner, cell_to_px(food), max(4, GRID_SIZE//3), t_total)
        draw_snake(inner, snake, dir_vec)
        screen.blit(inner, (0,0))

        # HUD
        hud = font.render(f"Score: {score}   High: {high}   Speed: {speed}", True, (230,230,230))
        screen.blit(hud, (10,6))

        # paused / gameover overlays
        if paused and not game_over:
            p_s = bigfont.render("PAUSED", True, (240,240,240))
            screen.blit(p_s, p_s.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))
        if game_over:
            go_s = bigfont.render("GAME OVER", True, (255,95,85))
            go_r = go_s.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 24))
            screen.blit(go_s, go_r)
            info = font.render("Press R to Restart  |  Esc to Quit", True, (220,220,220))
            screen.blit(info, info.get_rect(center=(SCREEN_W//2, SCREEN_H//2 + 20)))
            score_txt = font.render(f"Your Score: {score}", True, (235,235,235))
            screen.blit(score_txt, (SCREEN_W//2 - score_txt.get_width()//2, SCREEN_H//2 + 50))

        pygame.display.flip()

# ---------------- Start Menu ----------------
def start_menu():
    title = bigfont.render("Stylish Snake PRO", True, (250,250,250))
    hint = font.render("SPACE or ENTER to Play   |   P to Pause during game", True, (220,220,220))
    sub = font.render("Walls enabled. Collect food to grow. Sounds optional.", True, (190,190,190))

    pulse_t = 0.0
    while True:
        dt = clock.tick(FPS) / 1000.0
        pulse_t += dt
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_SPACE, pygame.K_RETURN):
                    return
                if ev.key in (pygame.K_ESCAPE,):
                    pygame.quit(); sys.exit()

        # animated gradient
        t = pygame.time.get_ticks() / 1000.0
        top = tuple(int(BG_TOP[i] + 8*math.sin(t + i)) for i in range(3))
        bottom = tuple(int(BG_BOTTOM[i] + 8*math.cos(t + i)) for i in range(3))
        bg = pygame.Surface((SCREEN_W, SCREEN_H))
        draw_gradient(bg, top, bottom)
        screen.blit(bg, (0,0))
        draw_grid_overlay(screen)

        wob = math.sin(pulse_t * 1.5) * 6
        screen.blit(title, title.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 40 + wob)))
        screen.blit(hint, hint.get_rect(center=(SCREEN_W//2, SCREEN_H//2 + 20)))
        screen.blit(sub, sub.get_rect(center=(SCREEN_W//2, SCREEN_H//2 + 52)))
        # small footer help
        footer = font.render("If you want sound: place bgm.mp3, eat.wav, gameover.wav in same folder", True, (190,190,190))
        screen.blit(footer, (10, SCREEN_H - 24))

        pygame.display.flip()

# ---------------- Main ----------------
if __name__ == "__main__":
    # try loading sounds again (if user added files before running)
    load_sounds()
    while True:
        start_menu()
        play_game()
