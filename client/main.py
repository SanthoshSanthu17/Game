import sys
import pygame

from client.network import GameClient
from client.screens import ScreenManager


MIN_WIDTH = 800
MIN_HEIGHT = 750
INITIAL_WIDTH = 1152
INITIAL_HEIGHT = 800


def main():
    pygame.init()

    screen = pygame.display.set_mode(
        (INITIAL_WIDTH, INITIAL_HEIGHT),
        pygame.RESIZABLE
    )
    pygame.display.set_caption("Ben 10 Galactic Battle")

    clock = pygame.time.Clock()

    client = GameClient()
    manager = ScreenManager(screen, client)

    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                new_width = max(event.w, MIN_WIDTH)
                new_height = max(event.h, MIN_HEIGHT)

                screen = pygame.display.set_mode(
                    (new_width, new_height),
                    pygame.RESIZABLE
                )

                manager.screen = screen

            else:
                manager.handle_event(event)

        manager.update()
        manager.draw(screen, mouse_pos)

        pygame.display.flip()
        clock.tick(60)

    client.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()