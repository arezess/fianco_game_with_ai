# game.py
import pygame
from constants import *

class FiancoGame:
    def __init__(self):
        self.board = [['.' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        
        # Initialize the white pieces (reverse pyramid)
        self.board[8] = ['W'] * BOARD_SIZE
        self.board[7] = ['.', 'W', '.', '.', '.', '.', '.', 'W', '.']
        self.board[6] = ['.', '.', 'W', '.', '.', '.', 'W', '.', '.']
        self.board[5] = ['.', '.', '.', 'W', '.', 'W', '.', '.', '.']
        
        # Initialize the black pieces (pyramid)
        self.board[0] = ['B'] * BOARD_SIZE
        self.board[1] = ['.', 'B', '.', '.', '.', '.', '.', 'B', '.']
        self.board[2] = ['.', '.', 'B', '.', '.', '.', 'B', '.', '.']
        self.board[3] = ['.', '.', '.', 'B', '.', 'B', '.', '.', '.']
        
        self.current_player = 'B'
        self.move_history = []
        self.zobrist_hash = self.compute_zobrist_hash()
        self.capture_move_cache = {}
        self.move_cache = {}
        self.undo_stack = []  # Stack for undoing moves
        self.redo_stack = []  # Stack for redoing moves
    
    def compute_zobrist_hash(self):
        h = 0
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece == 'B':
                    piece_index = 0
                elif piece == 'W':
                    piece_index = 1
                else:
                    continue  # Empty squares don't affect the hash
                h ^= ZOBRIST_TABLE[row][col][piece_index]
        # Include current player in hash
        if self.current_player == 'B':
            h ^= PLAYER_HASH
        return h

    def update_zobrist_hash(self, start, end, piece, captured_piece=None, capture_end=None):
        if piece == 'B':
            piece_index = 0
        elif piece == 'W':
            piece_index = 1
        else:
            return

        s_row, s_col = start
        e_row, e_col = end

        # Remove piece from start position
        self.zobrist_hash ^= ZOBRIST_TABLE[s_row][s_col][piece_index]
        # Add piece to end position
        self.zobrist_hash ^= ZOBRIST_TABLE[e_row][e_col][piece_index]

        if captured_piece:
            if captured_piece == 'B':
                captured_index = 0
            elif captured_piece == 'W':
                captured_index = 1
            else:
                return
            c_row, c_col = capture_end
            # Remove captured piece
            self.zobrist_hash ^= ZOBRIST_TABLE[c_row][c_col][captured_index]

    def draw_board(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if (row + col) % 2 == 0:
                    pygame.draw.rect(screen, DARK_GRAY, rect)
                else:
                    pygame.draw.rect(screen, GRAY, rect)
                # Draw the square notation
                square_notation = self.get_square_notation((row, col))
                notation_surface = font.render(square_notation, True, WHITE)
                notation_rect = notation_surface.get_rect(center=(col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2))
                screen.blit(notation_surface, notation_rect)
               
                piece = self.board[row][col]
                if piece == 'B':
                    pygame.draw.circle(screen, BLACK, (col * CELL_SIZE + CELL_SIZE // 2,
                                                       row * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2 - 10)
                elif piece == 'W':
                    pygame.draw.circle(screen, WHITE, (col * CELL_SIZE + CELL_SIZE // 2,
                                                       row * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2 - 10)

    def make_move(self, start, end):
        row_start, col_start = start
        row_end, col_end = end

        moving_piece = self.board[row_start][col_start]
        captured_piece = None
        capture_end = None

        if self.is_capture_move(start, end):
            row_diff = row_end - row_start
            col_diff = col_end - col_start
            row_after = row_end + row_diff
            col_after = col_end + col_diff

            if 0 <= row_after < BOARD_SIZE and 0 <= col_after < BOARD_SIZE:
                captured_piece = self.board[row_end][col_end]
                self.board[row_after][col_after] = moving_piece
                self.board[row_start][col_start] = '.'
                self.board[row_end][col_end] = '.'
                # Update Zobrist hash
                self.update_zobrist_hash(start, (row_after, col_after), moving_piece, captured_piece, (row_end, col_end))
                # Update move history
                move_notation = f"{self.get_square_notation(start)}x{self.get_square_notation((row_after, col_after))}"
                self.move_history.append(move_notation)
                # Return updated end position and captured piece info
                return (start, (row_after, col_after)), (captured_piece, (row_end, col_end))
            else:
                return None
        elif self.is_valid_move(start, end):
            self.board[row_end][col_end] = moving_piece
            self.board[row_start][col_start] = '.'
            # Update Zobrist hash
            self.update_zobrist_hash(start, end, moving_piece)
            # Update move history
            move_notation = f"{self.get_square_notation(start)}-{self.get_square_notation(end)}"
            self.move_history.append(move_notation)
            return (start, end), None  # No capture
        else:
            return None  # Invalid move

    def undo_move(self, move_info, captured_piece_info):
        (start, end) = move_info
        moving_piece = self.board[end[0]][end[1]]  # Get the piece from the end position
        s_row, s_col = start
        e_row, e_col = end
        self.board[s_row][s_col] = moving_piece
        self.board[e_row][e_col] = '.'

        if captured_piece_info:
            captured_piece, capture_pos = captured_piece_info
            c_row, c_col = capture_pos
            self.board[c_row][c_col] = captured_piece

            # Update Zobrist hash for captured piece
            captured_index = 0 if captured_piece == 'B' else 1
            self.zobrist_hash ^= ZOBRIST_TABLE[c_row][c_col][captured_index]

        # Update Zobrist hash
        piece_index = 0 if moving_piece == 'B' else 1
        # Remove piece from end position
        self.zobrist_hash ^= ZOBRIST_TABLE[e_row][e_col][piece_index]
        # Add piece back to start position
        self.zobrist_hash ^= ZOBRIST_TABLE[s_row][s_col][piece_index]

        # Remove move from history
        if self.move_history:
            self.move_history.pop()

    def get_square_notation(self, square):
        row, col = square
        return f"{chr(97 + col)}{9 - row}"

    def is_valid_move(self, start, end):
        row_start, col_start = start
        row_end, col_end = end
        piece = self.board[row_start][col_start]

        # If there is a capture move available, normal moves are not allowed
        if self.has_capture_move():
            return False

        row_diff = row_end - row_start
        col_diff = col_end - col_start

        # Check if moving to an empty square
        if self.board[row_end][col_end] != '.':
            return False

        # Only allow forward or sideways moves
        if abs(row_diff) + abs(col_diff) != 1:
            return False

        # Black moves down, White moves up
        if (piece == 'B' and row_diff == 1) or (piece == 'W' and row_diff == -1) or (col_diff != 0):
            return True

        return False

    def is_capture_move(self, start, end):
        row_start, col_start = start
        row_end, col_end = end

        row_diff = row_end - row_start
        col_diff = col_end - col_start

        piece = self.board[row_start][col_start]
        opponent = 'W' if piece == 'B' else 'B'

        # Ensure capture is in forward diagonal direction
        if piece == 'B' and row_diff != 1:
            return False
        if piece == 'W' and row_diff != -1:
            return False

        if abs(col_diff) != 1:
            return False

        if self.board[row_end][col_end] != opponent:
            return False

        row_after = row_end + row_diff
        col_after = col_end + col_diff

        if 0 <= row_after < BOARD_SIZE and 0 <= col_after < BOARD_SIZE:
            if self.board[row_after][col_after] == '.':
                return True

        return False

    def has_capture_move(self):
        cache_key = self.zobrist_hash
        if cache_key in self.capture_move_cache:
            return self.capture_move_cache[cache_key]

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.board[row][col] == self.current_player:
                    if self.can_capture_from((row, col)):
                        self.capture_move_cache[cache_key] = True
                        return True
        self.capture_move_cache[cache_key] = False
        return False

    def can_capture_from(self, position):
        row, col = position
        piece = self.board[row][col]
        opponent = 'W' if piece == 'B' else 'B'
        captures = self.get_capture_directions(piece)

        for d_row, d_col in captures:
            row_end = row + d_row
            col_end = col + d_col
            row_after = row_end + d_row
            col_after = col_end + d_col
            if 0 <= row_end < BOARD_SIZE and 0 <= col_end < BOARD_SIZE:
                if self.board[row_end][col_end] == opponent:
                    if 0 <= row_after < BOARD_SIZE and 0 <= col_after < BOARD_SIZE:
                        if self.board[row_after][col_after] == '.':
                            return True
        return False

    def get_capture_directions(self, piece):
        if piece == 'B':
            return [(1, -1), (1, 1)]  # Black moves down the board
        else:
            return [(-1, -1), (-1, 1)]  # White moves up the board

    def switch_player(self):
        # Update the zobrist hash for the current player
        self.zobrist_hash ^= PLAYER_HASH
        self.current_player = 'W' if self.current_player == 'B' else 'B'
        self.capture_move_cache.clear()  # Clear cache when switching player

    def check_win(self):
        # Check if any player has reached the opposite side
        for i in range(BOARD_SIZE):
            if self.board[0][i] == 'W':
                return 'W'
            if self.board[8][i] == 'B':
                return 'B'
        # Check if any player has no valid moves
        if not self.get_all_moves():
            return 'W' if self.current_player == 'B' else 'B'
        return None

    def get_all_moves(self):
        cache_key = (self.zobrist_hash, self.current_player)
        if cache_key in self.move_cache:
            return self.move_cache[cache_key]

        moves = []
        has_capture = self.has_capture_move()
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.board[row][col] == self.current_player:
                    if has_capture:
                        moves.extend(self.get_capture_moves(row, col))
                    else:
                        moves.extend(self.get_normal_moves(row, col))

        self.move_cache[cache_key] = moves
        return moves

    def is_super_strong_piece(self, row, col):
        piece = self.board[row][col]
        opponent = 'W' if piece == 'B' else 'B'
        is_clear = True

        if piece == 'B':
            # Black pawn moving down
            for r in range(row + 1, BOARD_SIZE):
                distance = r - row
                col_start = col - distance
                col_end = col + distance
                for c in range(col_start, col_end + 1):
                    if 0 <= c < BOARD_SIZE:
                        if self.board[r][c] == opponent:
                            is_clear = False
                            break
                if not is_clear:
                    break
        elif piece == 'W':
            # White pawn moving up
            for r in range(row - 1, -1, -1):
                distance = row - r
                col_start = col - distance
                col_end = col + distance
                for c in range(col_start, col_end + 1):
                    if 0 <= c < BOARD_SIZE:
                        if self.board[r][c] == opponent:
                            is_clear = False
                            break
                if not is_clear:
                    break
        else:
            is_clear = False  # Not a pawn

        return is_clear

    def get_capture_moves(self, row, col):
        moves = []
        piece = self.board[row][col]
        opponent = 'W' if piece == 'B' else 'B'
        captures = self.get_capture_directions(piece)
        for d_row, d_col in captures:
            end_row = row + d_row
            end_col = col + d_col
            final_row = end_row + d_row
            final_col = end_col + d_col
            if 0 <= end_row < BOARD_SIZE and 0 <= end_col < BOARD_SIZE:
                if self.board[end_row][end_col] == opponent:
                    if 0 <= final_row < BOARD_SIZE and 0 <= final_col < BOARD_SIZE:
                        if self.board[final_row][final_col] == '.':
                            # Return the initial and the immediate capture position
                            moves.append(((row, col), (end_row, end_col)))
        return moves

    def get_normal_moves(self, row, col):
        moves = []
        piece = self.board[row][col]
        if piece == 'B':
            directions = [(1, 0), (0, -1), (0, 1)]  # Black moves down the board
        else:
            directions = [(-1, 0), (0, -1), (0, 1)]  # White moves up the board
        for d_row, d_col in directions:
            end_row = row + d_row
            end_col = col + d_col
            if 0 <= end_row < BOARD_SIZE and 0 <= end_col < BOARD_SIZE:
                if self.board[end_row][end_col] == '.':
                    moves.append(((row, col), (end_row, end_col)))
        return moves
    
    def evaluate(self):
        from ai import evaluate_board
        return evaluate_board(self)
    
    def get_piece_moves(self, position):
        row, col = position
        moves = []
        has_capture = self.has_capture_move()

        if has_capture:
            # Get all capture moves if there is a capture possibility
            moves = self.get_capture_moves(row, col)
        else:
            # Get normal moves if no capture is required
            moves = self.get_normal_moves(row, col)

        return moves