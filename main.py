# main.py
import pygame
import sys
import time
import cProfile
import pstats
import io

from constants import *
from game import FiancoGame
from ai import get_ai_move
from ui import color_selection_menu, draw_sidebar

# Main game loop
def main():
    # Let the player choose their color at the start
    human_player, ai_player = color_selection_menu()

    game = FiancoGame()
    game.current_player = 'W'  # White always starts

    selected_piece = None
    possible_moves = []  # To store the valid moves for the selected piece

    # Main game loop
    while True:
        screen.fill(DARK_GRAY)
        game.draw_board()
        clock.tick(60)
        # Highlight possible moves for the selected piece
        for move in possible_moves:
            _, (row, col) = move  # Get the target cell of the move
            pygame.draw.rect(screen, BLUE, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE), 3)

        # Get the button rects
        undo_button_rect, redo_button_rect = draw_sidebar(screen, game.move_history, game.current_player)
        pygame.display.flip()
        
        winner = game.check_win()
        if winner:
            font = pygame.font.Font(None, 72)
            text = font.render(f"{winner} wins!", True, GREEN)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.wait(3000)
            pygame.quit()
            return

        # Handle human turn
        if game.current_player == human_player:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    if undo_button_rect.collidepoint(pos):
                        # Handle Undo
                        if len(game.undo_stack) >= 2:
                            # Undo AI's move
                            start, end, move_info, captured_piece_info, player = game.undo_stack.pop()
                            game.switch_player()  # Switch to AI
                            game.undo_move(move_info, captured_piece_info)
                            game.redo_stack.append((start, end, move_info, captured_piece_info, player))
                            
                            # Undo user's move
                            start, end, move_info, captured_piece_info, player = game.undo_stack.pop()
                            game.switch_player()  # Switch to human
                            game.undo_move(move_info, captured_piece_info)
                            game.redo_stack.append((start, end, move_info, captured_piece_info, player))
                        else:
                            print("No moves to undo")
                    elif redo_button_rect.collidepoint(pos):
                        # Handle Redo
                        if len(game.redo_stack) >= 2:
                            # Redo user's move
                            start, end, move_info, captured_piece_info, player = game.redo_stack.pop()
                            move_made = game.make_move(start, end)
                            game.undo_stack.append((start, end, move_made[0], move_made[1], player))
                            game.switch_player()  # Switch to AI
                            
                            # Redo AI's move
                            start, end, move_info, captured_piece_info, player = game.redo_stack.pop()
                            move_made = game.make_move(start, end)
                            game.undo_stack.append((start, end, move_made[0], move_made[1], player))
                            game.switch_player()  # Switch back to human
                        else:
                            print("No moves to redo")
                    else:
                        # Click on board
                        row, col = pos[1] // CELL_SIZE, pos[0] // CELL_SIZE
                        # Check if the click is inside the board boundaries
                        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                            if selected_piece is None:
                                # Select a piece and calculate its possible moves
                                if game.board[row][col] == human_player:
                                    selected_piece = (row, col)
                                    possible_moves = game.get_piece_moves(selected_piece)  # Get all valid moves for the selected piece
                            else:
                                # Try to make a move
                                move = (selected_piece, (row, col))
                                if move in possible_moves:
                                    move_info, captured_piece_info = game.make_move(*move)
                                    if move_info:
                                        # Record the move onto the undo_stack
                                        game.undo_stack.append((selected_piece, (row, col), move_info, captured_piece_info, game.current_player))
                                        game.redo_stack.clear()
                                        selected_piece = None
                                        possible_moves = []  # Clear possible moves after making the move
                                        game.switch_player()  # Switch to AI turn
                                else:
                                    # Invalid move or clicked outside possible moves, deselect piece
                                    selected_piece = None
                                    possible_moves = []
                        else:
                            # Click was outside the board, deselect any selected piece
                            selected_piece = None
                            possible_moves = []

        # Handle AI turn
        elif game.current_player == ai_player:
            depth = 15  # Set AI depth
            try:
                move = get_ai_move(game, depth, time_limit=8)
            except TimeoutError:
                move = None  # If time runs out, make no move
            
            if move:
                start, end = move
                move_info, captured_piece_info = game.make_move(start, end)
                print(f"AI {game.current_player} moved from {start} to {end}")
                # Record the AI's move onto the undo_stack
                game.undo_stack.append((start, end, move_info, captured_piece_info, game.current_player))
                game.redo_stack.clear()
                game.switch_player()  # Switch back to human turn
            else:
                print(f"AI {game.current_player} has no valid moves")
                winner = human_player if game.current_player == ai_player else ai_player
                font = pygame.font.Font(None, 72)
                text = font.render(f"{winner} wins!", True, GREEN)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                screen.blit(text, text_rect)
                pygame.display.flip()
                pygame.time.wait(3000)
                pygame.quit()
                return

        pygame.time.wait(100)  # Reduce the wait time for responsiveness

if __name__ == "__main__":
    main()