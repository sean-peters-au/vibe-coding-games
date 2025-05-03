import pygame
import random

# Global constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
PLAY_WIDTH = 300  # 10 blocks * 30 px
PLAY_HEIGHT = 600  # 20 blocks * 30 px
BLOCK_SIZE = 30

TOP_LEFT_X = (SCREEN_WIDTH - PLAY_WIDTH) // 2
TOP_LEFT_Y = SCREEN_HEIGHT - PLAY_HEIGHT - 50

# Define tetromino shapes and their rotations
S = [['.....',
      '.....',
      '..XX.',
      '.XX..',
      '.....'],
     ['.....',
      '..X..',
      '..XX.',
      '...X.',
      '.....']]

Z = [['.....',
      '.....',
      '.XX..',
      '..XX.',
      '.....'],
     ['.....',
      '..X..',
      '.XX..',
      '.X...',
      '.....']]

I = [['..X..',
      '..X..',
      '..X..',
      '..X..',
      '.....'],
     ['.....',
      '.....',
      'XXXX.',
      '.....',
      '.....']]

O = [['.....',
      '.....',
      '.XX..',
      '.XX..',
      '.....']]

J = [['.....',
      '.X...',
      '.XXX.',
      '.....',
      '.....'],
     ['.....',
      '..XX.',
      '..X..',
      '..X..',
      '.....'],
     ['.....',
      '.....',
      '.XXX.',
      '...X.',
      '.....'],
     ['.....',
      '..X..',
      '..X..',
      '.XX..',
      '.....']]

L = [['.....',
      '...X.',
      '.XXX.',
      '.....',
      '.....'],
     ['.....',
      '..X..',
      '..X..',
      '..XX.',
      '.....'],
     ['.....',
      '.....',
      '.XXX.',
      '.X...',
      '.....'],
     ['.....',
      '.XX..',
      '..X..',
      '..X..',
      '.....']]

T = [['.....',
      '..X..',
      '.XXX.',
      '.....',
      '.....'],
     ['.....',
      '..X..',
      '..XX.',
      '..X..',
      '.....'],
     ['.....',
      '.....',
      '.XXX.',
      '..X..',
      '.....'],
     ['.....',
      '..X..',
      '.XX..',
      '..X..',
      '.....']]

SHAPES = [S, Z, I, O, J, L, T]
SHAPE_COLORS = [
    (0, 255, 0),    # S
    (255, 0, 0),    # Z
    (0, 255, 255),  # I
    (255, 255, 0),  # O
    (255, 165, 0),  # J
    (0, 0, 255),    # L
    (128, 0, 128)   # T
]

class Piece:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = SHAPE_COLORS[SHAPES.index(shape)]
        self.rotation = 0


def create_grid(locked_positions={}):
    grid = [[(0,0,0) for _ in range(10)] for _ in range(20)]
    for (x, y), color in locked_positions.items():
        if y > -1:
            grid[y][x] = color
    return grid


def convert_shape_format(piece):
    positions = []
    format = piece.shape[piece.rotation % len(piece.shape)]
    for i, line in enumerate(format):
        for j, char in enumerate(line):
            if char == 'X':
                positions.append((piece.x + j - 2, piece.y + i - 4))
    return positions


def valid_space(piece, grid):
    accepted = [(j, i) for i in range(20) for j in range(10) if grid[i][j] == (0,0,0)]
    formatted = convert_shape_format(piece)
    for pos in formatted:
        if pos not in accepted:
            if pos[1] > -1:
                return False
    return True


def check_lost(locked_positions):
    for (_x, y) in locked_positions:
        if y < 1:
            return True
    return False


def get_shape():
    # Spawn pieces slightly higher to prevent immediate game over on rotation
    return Piece(3, -1, random.choice(SHAPES))


def draw_text_middle(surface, text, size, color):
    font = pygame.font.SysFont('comicsans', size, bold=True)
    label = font.render(text, True, color)
    surface.blit(label, (
        TOP_LEFT_X + PLAY_WIDTH/2 - label.get_width()/2,
        TOP_LEFT_Y + PLAY_HEIGHT/2 - label.get_height()/2
    ))


def draw_grid(surface, grid):
    sx, sy = TOP_LEFT_X, TOP_LEFT_Y
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            # draw block fill
            pygame.draw.rect(surface, grid[i][j], (sx + j*BLOCK_SIZE, sy + i*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
            # draw block outline for better depth
            pygame.draw.rect(surface, (40,40,40), (sx + j*BLOCK_SIZE, sy + i*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)
    # draw grid lines
    for i in range(len(grid) + 1):
        pygame.draw.line(surface, (128,128,128), (sx, sy + i*BLOCK_SIZE), (sx + PLAY_WIDTH, sy + i*BLOCK_SIZE))
    for j in range(len(grid[0]) + 1):
        pygame.draw.line(surface, (128,128,128), (sx + j*BLOCK_SIZE, sy), (sx + j*BLOCK_SIZE, sy + PLAY_HEIGHT))


def clear_rows(grid, locked_positions):
    rows_to_clear = []
    for i in range(len(grid)):
        if (0,0,0) not in grid[i]:
            rows_to_clear.append(i)
    if not rows_to_clear:
        return 0
    for row in rows_to_clear:
        for j in range(len(grid[row])):
            try:
                del locked_positions[(j, row)]
            except:
                pass
    # shift everything down
    for key in sorted(list(locked_positions), key=lambda x: x[1]):
        x, y = key
        shift = sum(1 for cleared_row in rows_to_clear if y < cleared_row)
        if shift > 0:
            color = locked_positions.pop(key)
            locked_positions[(x, y + shift)] = color
    return len(rows_to_clear)


def draw_next_shapes(next_pieces, surface):
    font = pygame.font.SysFont('comicsans', 30)
    label = font.render('Next:', True, (255,255,255))
    sx = TOP_LEFT_X + PLAY_WIDTH + 50
    sy_label = TOP_LEFT_Y + 50
    sy_start = sy_label + 40
    surface.blit(label, (sx, sy_label))

    for idx, piece in enumerate(next_pieces):
        format = piece.shape[piece.rotation % len(piece.shape)]
        # Calculate center offset for preview blocks
        start_x_offset = 0
        start_y_offset = 0
        if piece.shape == I:
             start_y_offset = -BLOCK_SIZE # Adjust I piece to center better
        elif piece.shape == O:
             start_x_offset = BLOCK_SIZE / 2 # Adjust O piece to center better

        for i, line in enumerate(format):
            for j, char in enumerate(line):
                if char == 'X':
                    block_x = sx + j*BLOCK_SIZE + start_x_offset
                    block_y = sy_start + i*BLOCK_SIZE + idx*120 + start_y_offset # Increased spacing with idx*120
                    # Draw fill
                    pygame.draw.rect(surface, piece.color, (block_x, block_y, BLOCK_SIZE, BLOCK_SIZE), 0)
                    # Draw outline
                    pygame.draw.rect(surface, (40,40,40), (block_x, block_y, BLOCK_SIZE, BLOCK_SIZE), 1)


def draw_window(surface, grid, score=0, level=1):
    # gradient background fill
    for y in range(SCREEN_HEIGHT):
        shade = 30 + int(25 * y / SCREEN_HEIGHT)
        pygame.draw.line(surface, (shade, shade, shade), (0, y), (SCREEN_WIDTH, y))
    # draw background panels
    pygame.draw.rect(surface, (50,50,50), (TOP_LEFT_X-5, TOP_LEFT_Y-5, PLAY_WIDTH+10, PLAY_HEIGHT+10), 0)
    sx = TOP_LEFT_X + PLAY_WIDTH + 50
    pygame.draw.rect(surface, (50,50,50), (sx-20, TOP_LEFT_Y-5, 200, PLAY_HEIGHT+10), 0)
    # Title
    font = pygame.font.SysFont('comicsans', 60, bold=True)
    label = font.render('TETRIS', True, (255,255,255))
    surface.blit(label, (TOP_LEFT_X + PLAY_WIDTH/2 - label.get_width()/2, 30))
    # Score and Level
    font = pygame.font.SysFont('comicsans', 30)
    score_label = font.render(f'Score: {score}', True, (255,255,255))
    level_label = font.render(f'Level: {level}', True, (255,255,255))
    surface.blit(score_label, (sx, TOP_LEFT_Y + PLAY_HEIGHT/2 + 150))
    surface.blit(level_label, (sx, TOP_LEFT_Y + PLAY_HEIGHT/2 + 190))
    # Draw play area
    draw_grid(surface, grid)
    pygame.draw.rect(surface, (255,255,255), (TOP_LEFT_X, TOP_LEFT_Y, PLAY_WIDTH, PLAY_HEIGHT), 4)


def main():
    pygame.init()
    win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Tetris')
    clock = pygame.time.Clock()
    # enable key repeat for smooth movement
    pygame.key.set_repeat(200, 50)

    locked_positions = {}
    grid = create_grid(locked_positions)

    change_piece = False
    run = True
    current_piece = get_shape()
    next_pieces = [get_shape() for _ in range(2)]
    fall_time = 0
    fall_speed = 0.5
    level_time = 0
    score = 0
    lines = 0

    # lock delay settings
    lock_delay = 0.5  # seconds
    lock_start_time = None

    while run:
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        level_time += clock.get_rawtime()
        clock.tick()

        # increase speed over time
        if level_time/1000 > 20 and fall_speed > 0.12:
            level_time = 0
            fall_speed -= 0.02

        # automatic fall
        if fall_time/1000 > fall_speed:
            fall_time = 0
            current_piece.y += 1
            if not valid_space(current_piece, grid) and current_piece.y > 0:
                current_piece.y -= 1
                if not lock_start_time:
                    lock_start_time = pygame.time.get_ticks()

        # event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if not valid_space(current_piece, grid):
                        current_piece.x += 1
                elif event.key == pygame.K_RIGHT:
                    current_piece.x += 1
                    if not valid_space(current_piece, grid):
                        current_piece.x -= 1
                elif event.key == pygame.K_DOWN:
                    current_piece.y += 1
                    if not valid_space(current_piece, grid):
                        current_piece.y -= 1
                        # initiate lock delay on bottom collision
                        if not lock_start_time:
                            lock_start_time = pygame.time.get_ticks()
                elif event.key == pygame.K_UP:
                    current_piece.rotation = (current_piece.rotation + 1) % len(current_piece.shape)
                    if not valid_space(current_piece, grid):
                        current_piece.rotation = (current_piece.rotation - 1) % len(current_piece.shape)
                elif event.key == pygame.K_SPACE:
                    # hard drop
                    while valid_space(current_piece, grid):
                        current_piece.y += 1
                    current_piece.y -= 1
                    change_piece = True

        # check lock delay expiration
        if lock_start_time:
            elapsed = (pygame.time.get_ticks() - lock_start_time) / 1000
            if elapsed >= lock_delay:
                change_piece = True

        # add current piece to grid for rendering
        shape_pos = convert_shape_format(current_piece)
        for x, y in shape_pos:
            if y > -1:
                grid[y][x] = current_piece.color

        # if piece should lock in place
        if change_piece:
            for pos in shape_pos:
                locked_positions[(pos[0], pos[1])] = current_piece.color
            cleared = clear_rows(grid, locked_positions)
            if cleared > 0:
                lines += cleared
                score += cleared * 100
            current_piece = next_pieces.pop(0)
            next_pieces.append(get_shape())
            change_piece = False
            lock_start_time = None
            if check_lost(locked_positions):
                draw_text_middle(win, "GAME OVER", 80, (255,255,255))
                pygame.display.update()
                pygame.time.delay(2000)
                run = False

        draw_window(win, grid, score, lines//10 + 1)
        draw_next_shapes(next_pieces, win)
        pygame.display.update()

    pygame.quit()


if __name__ == '__main__':
    main() 