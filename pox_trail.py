import pygame as pg
import pox_module as pox
import random

x_res = 1920
y_res = 1080

def main():
    pg.init()
    screen = pg.display.set_mode((x_res, y_res), pg.SHOWN)

    alpha_surf = pg.Surface(screen.get_size(), pg.SRCALPHA)
    clock = pg.time.Clock()
    running = True

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.MOUSEBUTTONDOWN:
                pox.add_charge(random.randint(1, x_res), random.randint(1, y_res), random.randint(100, 2000),
                               (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255)), True)
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                running = False

        NOW = pg.time.get_ticks()

        if not NOW % 200:
            pox.add_charge(random.randint(1, x_res), random.randint(1, y_res), random.randint(100, 2000),
                           (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255)), True)

        alpha_surf.fill((255, 255, 255, 120), special_flags=pg.BLEND_RGBA_MULT)

        screen.fill((0, 0, 0))
        pox.spriteGroup.update(alpha_surf)
        pox.spriteGroup.draw(alpha_surf)
        screen.blit(alpha_surf, (0, 0))
        pg.display.flip()
        clock.tick(120)


if __name__ == '__main__':
    main()
    pg.quit()
