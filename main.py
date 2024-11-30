import pygame
import sys
from pygame import mixer
from fighter import Fighter
from network import Network

if len(sys.argv) > 1:
  IS_HOST = sys.argv[1].lower() == "host"
else:
  IS_HOST = False

mixer.init()
pygame.init()

#create game window
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Rock-em-Sock-em")

#set framerate
clock = pygame.time.Clock()
FPS = 60

#define colours
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

#define game variables
intro_count = 3
last_count_update = pygame.time.get_ticks()
score = [0, 0]#player scores. [P1, P2]
round_over = False
ROUND_OVER_COOLDOWN = 2000

#define fighter variables
WARRIOR_SIZE = 162
WARRIOR_SCALE = 4
WARRIOR_OFFSET = [72, 56]
WARRIOR_DATA = [WARRIOR_SIZE, WARRIOR_SCALE, WARRIOR_OFFSET]
WIZARD_SIZE = 250
WIZARD_SCALE = 3
WIZARD_OFFSET = [112, 107]
WIZARD_DATA = [WIZARD_SIZE, WIZARD_SCALE, WIZARD_OFFSET]

#load music and sounds
pygame.mixer.music.load("assets/audio/music.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1, 0.0, 5000)
sword_fx = pygame.mixer.Sound("assets/audio/sword.wav")
sword_fx.set_volume(0.5)
magic_fx = pygame.mixer.Sound("assets/audio/magic.wav")
magic_fx.set_volume(0.75)

#load background image
bg_image = pygame.image.load("assets/images/background/boxing-ring-background.jpg").convert_alpha()

#load spritesheets
warrior_sheet = pygame.image.load("assets/images/warrior/Sprites/warrior.png").convert_alpha()
wizard_sheet = pygame.image.load("assets/images/wizard/Sprites/wizard.png").convert_alpha()

#load vicory image
victory_img = pygame.image.load("assets/images/icons/victory.png").convert_alpha()

#define number of steps in each animation
WARRIOR_ANIMATION_STEPS = [10, 8, 1, 7, 7, 3, 7]
WIZARD_ANIMATION_STEPS = [8, 8, 1, 8, 8, 3, 7]

#define font
count_font = pygame.font.Font("assets/fonts/turok.ttf", 80)
score_font = pygame.font.Font("assets/fonts/turok.ttf", 30)

#function for drawing text
def draw_text(text, font, text_col, x, y):
  img = font.render(text, True, text_col)
  screen.blit(img, (x, y))

#function for drawing background
def draw_bg():
  scaled_bg = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
  screen.blit(scaled_bg, (0, 0))

#function for drawing fighter health bars
def draw_health_bar(health, x, y):
  ratio = health / 100
  pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34))
  pygame.draw.rect(screen, RED, (x, y, 400, 30))
  pygame.draw.rect(screen, YELLOW, (x, y, 400 * ratio, 30))


#create two instances of fighters
fighter_1 = Fighter(1, 200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIMATION_STEPS, sword_fx)
fighter_2 = Fighter(2, 700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIMATION_STEPS, magic_fx)

network = Network(host="localhost", is_host=IS_HOST)
my_fighter = fighter_1 if IS_HOST else fighter_2
opponent_fighter = fighter_2 if IS_HOST else fighter_1

#game loop
run = True
while run:
  

  clock.tick(FPS)

  #draw background
  draw_bg()

  #show player stats
  draw_health_bar(fighter_1.health, 20, 20)
  draw_health_bar(fighter_2.health, 580, 20)
  draw_text("P1: " + str(score[0]), score_font, RED, 20, 60)
  draw_text("P2: " + str(score[1]), score_font, RED, 580, 60)

  #update countdown
  if intro_count <= 0:
    #move fighters
    my_fighter.move(SCREEN_WIDTH, SCREEN_HEIGHT, screen, opponent_fighter, round_over)
    
    fighter_data = {
        #position and size
        'x': my_fighter.rect.x,
        'y': my_fighter.rect.y,
        'vel_y': my_fighter.vel_y,
        
        # Animation states
        'action': my_fighter.action,
        'frame_index': my_fighter.frame_index,
        'update_time': my_fighter.update_time,
        'flip': my_fighter.flip,
        
        # Movement states
        'running': my_fighter.running,
        'jump': my_fighter.jump,
        
        # Combat states
        'attacking': my_fighter.attacking,
        'attack_type': my_fighter.attack_type,
        'attack_cooldown': my_fighter.attack_cooldown,
        'hit': my_fighter.hit,
        'health': my_fighter.health,
        'alive': my_fighter.alive
    }
    network.send(fighter_data)
    
    opponent_data = network.receive()
    if opponent_data:
        # Position and size
        opponent_fighter.rect.x = opponent_data['x']
        opponent_fighter.rect.y = opponent_data['y']
        opponent_fighter.vel_y = opponent_data['vel_y']
        
        # Animation states
        opponent_fighter.action = opponent_data['action']
        opponent_fighter.frame_index = opponent_data['frame_index']
        opponent_fighter.update_time = opponent_data['update_time']
        opponent_fighter.flip = opponent_data['flip']
        
        # Movement states
        opponent_fighter.running = opponent_data['running']
        opponent_fighter.jump = opponent_data['jump']
        
        # Combat states
        opponent_fighter.attacking = opponent_data['attacking']
        opponent_fighter.attack_type = opponent_data['attack_type']
        opponent_fighter.attack_cooldown = opponent_data['attack_cooldown']
        opponent_fighter.hit = opponent_data['hit']
        opponent_fighter.health = opponent_data['health']
        opponent_fighter.alive = opponent_data['alive']
  else:
    #display count timer
    draw_text(str(intro_count), count_font, RED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3)
    #update count timer
    if (pygame.time.get_ticks() - last_count_update) >= 1000:
      intro_count -= 1
      last_count_update = pygame.time.get_ticks()

  #update fighters
  fighter_1.update()
  fighter_2.update()

  #draw fighters
  fighter_1.draw(screen)
  fighter_2.draw(screen)

  #check for player defeat
  if round_over == False:
    if fighter_1.alive == False:
      score[1] += 1
      round_over = True
      round_over_time = pygame.time.get_ticks()
    elif fighter_2.alive == False:
      score[0] += 1
      round_over = True
      round_over_time = pygame.time.get_ticks()
  else:
    #display victory image
    screen.blit(victory_img, (360, 150))
    if pygame.time.get_ticks() - round_over_time > ROUND_OVER_COOLDOWN:
      round_over = False
      intro_count = 3
      fighter_1 = Fighter(1, 200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIMATION_STEPS, sword_fx)
      fighter_2 = Fighter(2, 700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIMATION_STEPS, magic_fx)

  #event handler
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      run = False


  #update display
  pygame.display.update()

#exit pygame
pygame.quit()