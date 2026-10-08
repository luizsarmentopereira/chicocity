import pygame
import sys
import os

# ---------------- CONFIGURAÇÕES ----------------
WIDTH, HEIGHT = 1200, 896
FPS = 60
GROUND_Y = HEIGHT - 120
SCALE = 1.5

# Estados do jogo
MENU = 0
INSTRUCOES = 1
JOGANDO = 2

# ---------------- INICIALIZAÇÃO ----------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chico Science Game - Manguebeat")
clock = pygame.time.Clock()

# --- CARREGAMENTO DA FONTE RETRÔ ---
try:
    font_title = pygame.font.Font("retro.ttf", 50)
    font_option = pygame.font.Font("retro.ttf", 25)
    font_small = pygame.font.Font("retro.ttf", 15)
except FileNotFoundError:
    print("AVISO: Arquivo 'retro.ttf' não encontrado! Usando fonte padrão.")
    font_title = pygame.font.Font(None, 80)
    font_option = pygame.font.Font(None, 40)
    font_small = pygame.font.Font(None, 25)

# Variáveis do cenário infinito
bg_offset = 0
scroll_speed = 5

# Estado inicial
game_state = MENU
selected_option = 0

# --- CARREGAMENTO DO CENÁRIO (fundo do jogo) ---
try:
    background_img = pygame.image.load(os.path.join("cenarios", "background.png")).convert_alpha()
except FileNotFoundError:
    try:
        background_img = pygame.image.load(os.path.join("cenarios", "cenario.png")).convert_alpha()
    except FileNotFoundError:
        background_img = pygame.Surface((WIDTH, HEIGHT))
        background_img.fill((40, 40, 60))

bg_w_original = background_img.get_width()
bg_h_original = background_img.get_height()
nova_altura = HEIGHT
nova_largura = int(bg_w_original * (nova_altura / bg_h_original))
background_img = pygame.transform.scale(background_img, (nova_largura, nova_altura))

# --- CARREGAMENTO DA IMAGEM DO MENU ---
try:
    menu_img = pygame.image.load(os.path.join("cenarios", "menu_iniciar.png")).convert_alpha()
    menu_img = pygame.transform.scale(menu_img, (WIDTH, HEIGHT))
except FileNotFoundError:
    menu_img = pygame.Surface((WIDTH, HEIGHT))
    menu_img.fill((40, 20, 60))

# --- CARREGAMENTO DO CARANGUEJO (INDICADOR DE SELEÇÃO) ---
try:
    # Carrega o caranguejo da pasta chicocity
    crab_img = pygame.image.load("caranguejo.png").convert_alpha()
    # Redimensiona para um tamanho bom para o menu (ex: 40x40)
    crab_img = pygame.transform.scale(crab_img, (40, 40))
except FileNotFoundError:
    print("AVISO: Arquivo 'caranguejo.png' não encontrado! Usando um quadrado vermelho no lugar.")
    crab_img = pygame.Surface((40, 40))
    crab_img.fill((255, 0, 0))

# ---------------- FUNÇÃO AUXILIAR PARA TEXTO COM BORDA ----------------
# Agora essa função retorna o 'rect' (retângulo) do texto para podermos posicionar o caranguejo ao lado
def draw_text_with_outline(text, font, color, center_pos, surface):
    text_black = font.render(text, True, (0, 0, 0))
    offsets = [(-2, -2), (2, -2), (-2, 2), (2, 2)]
    for ox, oy in offsets:
        rect = text_black.get_rect(center=(center_pos[0] + ox, center_pos[1] + oy))
        surface.blit(text_black, rect)
    
    text_color = font.render(text, True, color)
    rect_color = text_color.get_rect(center=center_pos)
    surface.blit(text_color, rect_color)
    
    return rect_color # Retorna a posição do texto colorido

# ---------------- IMAGENS DO PERSONAGEM ----------------
def load_images(folder, prefix, count):
    images = []
    for i in range(1, count + 1):
        filename = os.path.join(folder, f"{prefix}_{i}.png")
        try:
            img = pygame.image.load(filename).convert_alpha()
            width = int(img.get_width() * SCALE)
            height = int(img.get_height() * SCALE)
            img = pygame.transform.scale(img, (width, height))
            images.append(img)
        except FileNotFoundError:
            print(f"Erro: {filename} não encontrado")
            img = pygame.Surface((50, 50))
            img.fill((255, 0, 0))
            images.append(img)
    return images

# ---------------- CLASSE CHICO SCIENCE ----------------
class ChicoScience:
    def __init__(self):
        self.animations = {
            "idle": load_images("Sprites/chico", "parado", 4),
            "walk": load_images("Sprites/chico", "andando", 6),
            "punch": load_images("Sprites/chico", "murro", 3),
            "jump": load_images("Sprites/chico", "pulo", 6),
            "down": load_images("Sprites/chico", "abaixado", 1),
            "murro_abaixado": load_images("Sprites/chico", "murroabaixado", 3)
        }

        self.state = "idle"
        self.frame_index = 0
        self.anim_speed = 0.15

        self.image = self.animations[self.state][0]
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (250, GROUND_Y)

        self.facing_right = True
        self.hold_punch = False

        self.vel_y = 0
        self.gravity = 0.8
        self.jump_force = -16

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.frame_index = 0

    def punch_start(self):
        if self.state == "down":
            self.set_state("murro_abaixado")
        elif self.state not in ["punch", "murro_abaixado"]:
            self.set_state("punch")

    def punch_release(self):
        self.hold_punch = False

    def animate(self, loop=True):
        if self.state in ["punch", "murro_abaixado"]:
            if self.hold_punch and int(self.frame_index) == 1:
                self.image = self.animations[self.state][1]
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.image, True, False)
                return

        self.frame_index += self.anim_speed

        if self.frame_index >= len(self.animations[self.state]):
            if loop:
                self.frame_index = 0
            else:
                self.set_state("idle")
                return

        self.image = self.animations[self.state][int(self.frame_index)]
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)

    def update(self, keys):
        global bg_offset

        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        on_ground = False
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vel_y = 0
            on_ground = True

        if self.state in ["punch", "murro_abaixado"]:
            self.animate(loop=False)
            return

        moving = False
        if not keys[pygame.K_s]:
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.facing_right = True
                moving = True
                bg_offset -= scroll_speed
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.facing_right = False
                moving = True
                bg_offset += scroll_speed

        if not on_ground:
            self.set_state("jump")
        else:
            if keys[pygame.K_s]:
                self.set_state("down")
            elif moving:
                self.set_state("walk")
            else:
                self.set_state("idle")

        if self.state == "jump":
            self.animate(loop=False)
        else:
            self.animate(loop=True)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

# ---------------- FUNÇÕES DO MENU ----------------
def desenha_menu():
    screen.blit(menu_img, (0, 0))

    opcoes = ["Iniciar Jogo", "Instruções", "Sair"]
    cores = [(255, 255, 255) if i != selected_option else (255, 215, 0) for i in range(3)]
    
    center_x = WIDTH // 2  
    start_y = HEIGHT - 350 
    spacing = 80
    
    for i, opcao in enumerate(opcoes):
        # Desenha o texto e pega a posição exata dele
        text_rect = draw_text_with_outline(
            opcao, 
            font_option, 
            cores[i], 
            (center_x, start_y + i * spacing), 
            screen
        )
        
        # Se esta for a opção selecionada, desenha o caranguejo à esquerda
        if i == selected_option:
            # O caranguejo fica com o lado direito alinhado a 20 pixels de distância da esquerda do texto
            # E centralizado verticalmente com o texto
            crab_rect = crab_img.get_rect(midright=(text_rect.left - 20, text_rect.centery))
            screen.blit(crab_img, crab_rect)

    draw_text_with_outline(
        "Use as setas e Enter", 
        font_small, 
        (200, 200, 200), 
        (WIDTH // 2, HEIGHT - 30), 
        screen
    )

def desenha_instrucoes():
    screen.blit(menu_img, (0, 0))

    draw_text_with_outline("INSTRUÇÕES", font_title, (255, 215, 0), (WIDTH // 2, 100), screen)

    controles = [
        "← / A  -> Esquerda",
        "→ / D  -> Direita",
        "↑ / Espaço -> Pular",
        "S      -> Agachar",
        "P      -> Socar",
        "ESC    -> Voltar"
    ]

    start_y = 250
    spacing = 60

    for i, linha in enumerate(controles):
        draw_text_with_outline(linha, font_small, (255, 255, 255), (WIDTH // 2, start_y + i * spacing), screen)

    draw_text_with_outline("Pressione ESC", font_small, (200, 200, 200), (WIDTH // 2, HEIGHT - 80), screen)

# ---------------- INSTÂNCIA ----------------
chico = ChicoScience()

# ---------------- LOOP PRINCIPAL ----------------
running = True
while running:
    clock.tick(FPS)

    # ----- EVENTOS -----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == MENU:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % 3
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % 3
                elif event.key == pygame.K_RETURN:
                    if selected_option == 0:
                        game_state = JOGANDO
                        chico.rect.bottomleft = (250, GROUND_Y)
                        chico.vel_y = 0
                        bg_offset = 0
                    elif selected_option == 1:
                        game_state = INSTRUCOES
                    elif selected_option == 2:
                        running = False

        elif game_state == INSTRUCOES:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = MENU

        elif game_state == JOGANDO:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_UP, pygame.K_SPACE, pygame.K_w]:
                    if chico.rect.bottom >= GROUND_Y:
                        chico.vel_y = chico.jump_force
                if event.key == pygame.K_p:
                    chico.hold_punch = True
                    chico.punch_start()
                if event.key == pygame.K_ESCAPE:
                    game_state = MENU

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_p:
                    chico.punch_release()

    # ----- ATUALIZAÇÃO -----
    if game_state == JOGANDO:
        keys = pygame.key.get_pressed()
        chico.update(keys)

    # ----- DESENHO -----
    screen.fill((0, 0, 0))

    if game_state == MENU:
        desenha_menu()

    elif game_state == INSTRUCOES:
        desenha_instrucoes()

    elif game_state == JOGANDO:
        bg_w = background_img.get_width()
        offset = bg_offset % bg_w
        for x in range(-bg_w, WIDTH + bg_w, bg_w):
            screen.blit(background_img, (x + offset, 0))

        chico.draw(screen)

    pygame.display.update()

pygame.quit()
sys.exit()