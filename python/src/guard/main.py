"""Точка входа pygame-демо. Переключение режима: клавиша M (FSM/BT)."""

import sys

import pygame

from guard.bt import build_guard_tree
from guard.fsm import GuardFSM


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    mode = "FSM"
    fsm, tree, bb = GuardFSM(), build_guard_tree(), {}
    _ = tree  # используется в режиме BT: tree.tick(bb)
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_m:
                mode = "BT" if mode == "FSM" else "FSM"
        # TODO: обновить сенсоры, вызвать fsm.fire(...) или tree.tick(bb), нарисовать сцену
        screen.fill((20, 20, 30))
        pygame.display.set_caption(f"Guard demo — {mode} — {fsm.state.name if mode == 'FSM' else bb.get('action')}")
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
