import pygame, pygame.gfxdraw, random, math


x_res = 1920
y_res = 1200
NOW_MS = 0
timer = pygame.time.Clock()
pygame.init()

class Particle(pygame.sprite.Sprite):
    GRAVITY = -7.8

    def __init__(self, x, y, color, gravity):
        super(Particle, self).__init__()
        self.gravity = gravity
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(1, 8)
        self.circle = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        #pygame.gfxdraw.aacircle(self.circle, int(self.size/2), int(self.size/2), int(self.size/2-1), self.color)
        pygame.gfxdraw.filled_circle(self.circle, int(self.size/2), int(self.size/2), int(self.size/2-1), self.color)
        self.poly = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        #pygame.gfxdraw.aapolygon(self.poly, [(0, self.size), (self.size/2, 0), (self.size, self.size)], self.color)
        pygame.gfxdraw.filled_polygon(self.poly, [(0, self.size), (self.size/2, 0), (self.size, self.size)], self.color)
        self.surface = random.choice([self.poly, self.circle])
        #self.surface = self.poly
        if self.color == (255, 255, 255):
            self.surface = self.circle
        if self.surface == self.circle:
            self.rotdelta = 0
            self.rotdeltach = 0
        else:    
            self.rotdelta = random.randint(-360, 360)
            self.rotdeltach = random.randint(1, 10)
        self.image = self.surface
        self.opacity = 255
        self.opacitydelta = random.randint(5, 20) / 10
        self.opacitych = random.randint(2, 5)
        self.rect = self.image.get_rect()
        self.ang = math.radians(random.randint(1, 360))
        self.power = random.randint(1,100)
        self.start_time = pygame.time.get_ticks()
    
    def update(self, screen):
        time_now = pygame.time.get_ticks()
        if (self.power > 0):
            time_change = (time_now - self.start_time)
            if (time_change > 0):
                time_change /= 200.0
                self.image = pygame.transform.rotate(self.surface, self.rotdelta)
                self.image.set_alpha(self.opacity)
                if self.rotdelta < 0:
                    self.rotdelta -= self.rotdeltach
                else:
                    self.rotdelta += self.rotdeltach
                #if self.color == (255, 255, 255):
                #    self.opacity += self.opacitych
                #    if self.opacity < 1 or self.opacity > 255:
                #        self.opacitych = -self.opacitych
                #else:
                self.opacity -= self.opacitydelta
                gravitydelta = self.GRAVITY * time_change * time_change / 2.0
                deltax = self.power * time_change * math.sin(self.ang)
                if self.gravity:
                    deltay = self.power * time_change * math.cos(self.ang) + gravitydelta
                else:
                    deltay = self.power * time_change * math.cos(self.ang)
                    
                self.rect.center = ( self.x + int(deltax), self.y - int(deltay))
                if self.opacity < 1:
                    #charges.remove(self)
                    self.kill()

                if not screen.get_rect().colliderect(self.rect) or (self.gravity and self.rect.y > 0 and not screen.get_rect().colliderect(self.rect)):
                    charges.remove(self)
                    self.kill()

def add_charge(x, y, amount, color, gravity=True):
    for i in range(1, amount):
        if not i % 10:
            charges.append(Particle(x, y, (255, 255, 255), gravity))    
        else:
            charges.append(Particle(x, y, color, gravity))
    spriteGroup.add(charges)

def flash_screen(col, screen):   
    if col > 1:
        screen.fill((col, col, col))
        col -= 15
    return col

maxSpr = 0
font = pygame.font.SysFont('msgothic', 18)
charges = []
spriteGroup = pygame.sprite.Group()
blasttime = 1000
blastinterval = 1000
flash = False
col = 0
total_fired = 0
startTime = pygame.time.get_ticks()
#running = True

#while running:
#    
#    for event in pygame.event.get():    
#        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
#                running = False
#        if event.type == pygame.MOUSEBUTTONDOWN:
#            mx, my = pygame.mouse.get_pos()
#            add_charge(mx, my, 1000, (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255)))
#        if event.type == pygame.QUIT:
#            running = False
    
    # Main routine begin
    
#    ticks = pygame.time.get_ticks()
#    if flash:
#        col = flash_screen(col)
#        if col < 1:
#            flash = False
#    else:
#        screen.fill((0, 0, 0)) 
#    spriteGroup.update()
#    spriteGroup.draw(screen)
    
    
#    if startTime + ticks > blasttime:
#        randX = random.randint(50, x_res - 50)
#        randY = random.randint(50, y_res - 50)
#        randA = random.randint(300, 3000)
#        randR = random.randint(1, 255)
#        randG = random.randint(1, 255)
#        randB = random.randint(1, 255)
#        flash = True
#        col = 255
#        add_charge(randX, randY, randA, (randR, randG, randB))
#        total_fired += 1
#        if randA < 1000:
#            total_fired +=1
#            add_charge(randX, randY, randA, (randG, randB, randR))
#        blasttime += blastinterval + random.randint(500, 2500)

#    if len(spriteGroup) > maxSpr:
#        maxSpr = len(spriteGroup)
#    screen.blit(font.render(f"sprites: {len(spriteGroup)} sprMax: {maxSpr}", True, "white"), (30, 30))
#    screen.blit(font.render(f"total fired: {total_fired}", True, "white"), (30, 50))
#    pygame.display.flip()
#    timer.tick(120)

    # Main routine end