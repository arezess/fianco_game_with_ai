# ui.py
import pygame
import sys
from constants import *

def draw_button(screen, text, rect, color, text_color):
    pygame.draw.rect(screen, color, rect)
    font = pygame.font.Font(None, 36)
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)

def color_selection_menu():
    while True:
        screen.fill(DARK_GRAY)
        font = pygame.font.Font(None, 48)
        text_surface = font.render("Choose Your Color", True, WHITE)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        screen.blit(text_surface, text_rect)
        
        # Button for choosing White
        white_button_rect = pygame.Rect(SCREEN_WIDTH // 4 - 100, SCREEN_HEIGHT // 2, 200, 60)
        draw_button(screen, "Play as White", white_button_rect, WHITE, BLACK)
        
        # Button for choosing Black
        black_button_rect = pygame.Rect(SCREEN_WIDTH * 3 // 4 - 100, SCREEN_HEIGHT // 2, 200, 60)
        draw_button(screen, "Play as Black", black_button_rect, BLACK, WHITE)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if white_button_rect.collidepoint(pos):
                    return 'W', 'B'  # Human plays White, AI plays Black
                elif black_button_rect.collidepoint(pos):
                    return 'B', 'W'  # Human plays Black, AI plays White

def draw_sidebar(screen, move_history, current_player):
    sidebar_rect = pygame.Rect(BOARD_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, WHITE, sidebar_rect)
    
    font = pygame.font.Font(None, 24)
    title = font.render("Move History", True, BLACK)
    screen.blit(title, (BOARD_WIDTH + 10, 10))
    
    # Display the last 10 moves
    start_y = 40  # Starting y-coordinate for move list
    moves_to_display = move_history[-10:]  # Get the last 10 moves
    for i, move in enumerate(moves_to_display):
        move_text = font.render(f"{len(move_history) - len(moves_to_display) + i + 1}. {move}", True, BLACK)
        screen.blit(move_text, (BOARD_WIDTH + 10, start_y + i * 25))

    # Display current player
    player_text = font.render(f"Current Player: {current_player}", True, BLACK)
    screen.blit(player_text, (BOARD_WIDTH + 10, SCREEN_HEIGHT - 140))
    
    # Draw Undo and Redo buttons
    undo_button_rect = pygame.Rect(BOARD_WIDTH + 10, SCREEN_HEIGHT - 100, SIDEBAR_WIDTH - 20, 40)
    redo_button_rect = pygame.Rect(BOARD_WIDTH + 10, SCREEN_HEIGHT - 50, SIDEBAR_WIDTH - 20, 40)
    draw_button(screen, "Undo", undo_button_rect, GRAY, BLACK)
    draw_button(screen, "Redo", redo_button_rect, GRAY, BLACK)
    
    return undo_button_rect, redo_button_rect