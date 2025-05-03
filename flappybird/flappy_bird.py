import pygame
import random
import sys
import os

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
GRAVITY = 0.25
FLAP_STRENGTH = -7
PIPE_SPEED = 3
PIPE_GAP = 150
PIPE_FREQUENCY = 1500  # milliseconds

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
SKY_BLUE = (135, 206, 235)

# Asset loading
def load_sprite(name, scale=1):
    path = os.path.join('assets', name)
    image = pygame.image.load(path).convert_alpha()
    if scale != 1:
        new_size = (int(image.get_width() * scale), 
                   int(image.get_height() * scale))
        image = pygame.transform.scale(image, new_size)
    return image

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Flappy Bird Clone')
clock = pygame.time.Clock()

class Bird:
    def __init__(self):
        self.x = SCREEN_WIDTH // 3
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.size = 30
        
        # Load bird sprites
        self.sprites = []
        for i in range(1, 4):
            sprite = load_sprite(f'bird{i}.png', 1.5)  # Increased scale to 2.0
            self.sprites.append(sprite)
            
        self.sprite_index = 0
        self.animation_speed = 0.1
        self.sprite = self.sprites[0]
        self.rotated_sprite = self.sprite
        self.rect = self.sprite.get_rect(center=(self.x, self.y))
        
    def flap(self):
        self.velocity = FLAP_STRENGTH
        
    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        
        # Animate bird
        self.sprite_index = (self.sprite_index + self.animation_speed) % len(self.sprites)
        self.sprite = self.sprites[int(self.sprite_index)]
        
        # Rotate bird based on velocity
        angle = max(-90, min(45, self.velocity * -3))
        self.rotated_sprite = pygame.transform.rotate(self.sprite, angle)
        self.rect = self.rotated_sprite.get_rect(center=(self.x, int(self.y)))
        
    def draw(self):
        screen.blit(self.rotated_sprite, self.rect)
        
    def check_collision(self, pipes):
        if self.y <= 0 or self.y >= SCREEN_HEIGHT:
            return True
        
        mask = pygame.mask.from_surface(self.rotated_sprite)
        bird_pos = (self.rect.left, self.rect.top)
        
        for pipe in pipes:
            if pipe.check_collision_with_mask(mask, bird_pos):
                return True
        return False

class Pipe:
    def __init__(self):
        self.width = 50
        self.gap_y = random.randint(200, SCREEN_HEIGHT - 200)
        self.x = SCREEN_WIDTH
        
        # Load pipe sprites
        self.pipe_sprite = load_sprite('pipe.png', 0.5)
        self.pipe_height = self.pipe_sprite.get_height()
        
        # Create top and bottom pipes
        self.top_height = self.gap_y - PIPE_GAP // 2
        self.bottom_height = SCREEN_HEIGHT - (self.gap_y + PIPE_GAP // 2)
        
        # Create rectangles for collision
        self.top_rect = pygame.Rect(self.x, 0, self.width, self.top_height)
        self.bottom_rect = pygame.Rect(self.x, SCREEN_HEIGHT - self.bottom_height, 
                                     self.width, self.bottom_height)
        
    def update(self):
        self.x -= PIPE_SPEED
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x
        
    def draw(self):
        # Draw top pipe (flipped)
        top_pipe = pygame.transform.scale(self.pipe_sprite, (self.width, self.top_height))
        top_pipe = pygame.transform.flip(top_pipe, False, True)
        screen.blit(top_pipe, self.top_rect)
        
        # Draw bottom pipe
        bottom_pipe = pygame.transform.scale(self.pipe_sprite, (self.width, self.bottom_height))
        screen.blit(bottom_pipe, self.bottom_rect)
        
    def check_collision_with_mask(self, bird_mask, bird_pos):
        # Create masks for pipes
        top_mask = pygame.mask.from_surface(
            pygame.transform.scale(self.pipe_sprite, (self.width, self.top_height)))
        bottom_mask = pygame.mask.from_surface(
            pygame.transform.scale(self.pipe_sprite, (self.width, self.bottom_height)))
        
        top_offset = (int(self.x - bird_pos[0]), int(0 - bird_pos[1]))
        bottom_offset = (int(self.x - bird_pos[0]), 
                        int(SCREEN_HEIGHT - self.bottom_height - bird_pos[1]))
        
        return (bird_mask.overlap(top_mask, top_offset) or 
                bird_mask.overlap(bottom_mask, bottom_offset))

def main():
    bird = Bird()
    pipes = []
    score = 0
    last_pipe = pygame.time.get_ticks()
    font = pygame.font.Font(None, 36)
    passed_pipes = set()  # Keep track of pipes we've passed
    
    while True:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.flap()
                    
        # Generate new pipes
        if current_time - last_pipe > PIPE_FREQUENCY:
            pipes.append(Pipe())
            last_pipe = current_time
            
        # Update game objects
        bird.update()
        for pipe in pipes:
            pipe.update()
            
        # Remove off-screen pipes
        pipes = [pipe for pipe in pipes if pipe.x > -pipe.width]
        
        # Check for collisions
        if bird.check_collision(pipes):
            return score
            
        # Update score
        for pipe in pipes:
            if pipe.x + pipe.width < bird.x and pipe not in passed_pipes:
                score += 1
                passed_pipes.add(pipe)
        
        # Remove passed pipes that are off screen
        passed_pipes = {pipe for pipe in passed_pipes if pipe in pipes}
        
        # Draw everything
        screen.fill(SKY_BLUE)
        for pipe in pipes:
            pipe.draw()
        bird.draw()
        
        # Draw score
        score_text = font.render(f'Score: {score}', True, WHITE)
        screen.blit(score_text, (10, 10))
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    while True:
        final_score = main()
        # Game over screen
        screen.fill(SKY_BLUE)
        font = pygame.font.Font(None, 48)
        game_over_text = font.render('Game Over!', True, WHITE)
        score_text = font.render(f'Final Score: {final_score}', True, WHITE)
        restart_text = font.render('Press SPACE to restart', True, WHITE)
        
        screen.blit(game_over_text, 
                   (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 
                    SCREEN_HEIGHT//3))
        screen.blit(score_text, 
                   (SCREEN_WIDTH//2 - score_text.get_width()//2, 
                    SCREEN_HEIGHT//2))
        screen.blit(restart_text, 
                   (SCREEN_WIDTH//2 - restart_text.get_width()//2, 
                    2*SCREEN_HEIGHT//3))
        
        pygame.display.flip()
        
        # Wait for space to restart
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False 