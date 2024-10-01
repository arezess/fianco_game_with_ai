import pygame
import sys
import time
import random
import cProfile
import pstats
import io

# Initialize Pygame
pygame.init()
font = pygame.font.Font(None, 24)

# Constants for screen dimensions and colors
BOARD_SIZE = 9
CELL_SIZE = 60
BOARD_WIDTH = CELL_SIZE * BOARD_SIZE
SIDEBAR_WIDTH = 200
SCREEN_WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH
SCREEN_HEIGHT = BOARD_WIDTH
DARK_GRAY = (64, 64, 64)
GRAY = (128, 128, 128)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

clock = pygame.time.Clock()
killer_moves = {}

PLAYER_HASH = random.getrandbits(64)
# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fianco Game with AI")

# Initialize Zobrist hashing table
ZOBRIST_TABLE = [[[random.getrandbits(64) for _ in range(2)] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
transposition_table = {}

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
                if self.board[row_end][end_col := col + d_col] == opponent:
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


# Evaluation Function
def evaluate_board(game):
    player = game.current_player
    opponent = 'W' if player == 'B' else 'B'

    winner = game.check_win()
    if winner == player:
        return float('inf')  # Max score if the player has won
    elif winner == opponent:
        return float('-inf')  # Min score if the opponent has won
    elif winner == 'D':
        return 0  # Draw

    score = 0

    # Use a fixed piece value
    piece_value = 1000  # High value to emphasize material

    # Center squares
    center_squares = [
        (4, 4), (4, 3), (4, 5), (3, 4), (5, 4),
        (3, 3), (3, 5), (5, 3), (5, 5)
    ]

    player_pieces = 0
    opponent_pieces = 0

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = game.board[row][col]
            if piece == player:
                player_pieces += 1
                score += piece_value  # Assign value to player's piece

                # Advancement towards the last row
                advancement = row if player == 'B' else (BOARD_SIZE - 1 - row)
                score += advancement * 5  # Reduced advancement weight

                # Control of the center
                if (row, col) in center_squares:
                    score += 10  # Reduced center control bonus

                # Check for super strong piece
                if game.is_super_strong_piece(row, col):
                    score += 500  # Adjusted bonus for super strong piece

            elif piece == opponent:
                opponent_pieces += 1
                score -= piece_value  # Subtract value for opponent's piece

                # Advancement towards the last row
                advancement = row if opponent == 'B' else (BOARD_SIZE - 1 - row)
                score -= advancement * 5  # Reduced opponent's advancement

                # Control of the center
                if (row, col) in center_squares:
                    score -= 10  # Reduced penalty if opponent controls center

                # Check if opponent has super strong piece
                if game.is_super_strong_piece(row, col):
                    score -= 500  # Adjusted penalty for opponent's super strong piece


    # Mobility
    player_mobility = len(game.get_all_moves())
    game.switch_player()
    opponent_mobility = len(game.get_all_moves())
    game.switch_player()
    score += (player_mobility - opponent_mobility) * 2  # Reduced mobility weight

    return score

# Move Ordering
def order_moves(game, moves, killer_moves=None, depth=0):
    # Prioritize capture moves and advancements
    ordered_moves = []
    for move in moves:
        start, end = move
        score = 0
        # Prioritize killer moves
        if killer_moves and depth in killer_moves and move in killer_moves[depth]:
            score += 5000  # Assign a high score to killer moves

        # Capture moves
        if game.is_capture_move(start, end):
            score += 1000
        # Advancement
        row_start, col_start = start
        row_end, col_end = end
        row_diff = row_end - row_start
        if game.current_player == 'B':
            score += row_diff * 10
        else:
            score -= row_diff * 10
        ordered_moves.append((score, move))
    ordered_moves.sort(reverse=True)
    return [move for _, move in ordered_moves]


def pvs(game, depth, alpha, beta, start_time, time_limit):
    if time.time() - start_time > time_limit:
        raise TimeoutError

    zobrist_hash = game.zobrist_hash
    if zobrist_hash in transposition_table:
        entry = transposition_table[zobrist_hash]
        if entry['depth'] >= depth:
            return entry['value']

    winner = game.check_win()
    if winner == game.current_player:
        return float('inf')
    elif winner == ('W' if game.current_player == 'B' else 'B'):
        return float('-inf')

    if depth == 0:
        return game.evaluate()

    max_eval = float('-inf')
    moves = game.get_all_moves()
    
    if not moves:
        return float('-inf')

    moves = order_moves(game, moves)

    # First move is searched with the full window
    for i, move in enumerate(moves):
        start, end = move
        move_info, captured_piece_info = game.make_move(start, end)
        game.switch_player()

        if i == 0:
            # Full window search for the first move
            eval = -pvs(game, depth - 1, -beta, -alpha, start_time, time_limit)
        else:
            # Null window search (PVS assumption: this move is worse)
            eval = -pvs(game, depth - 1, -alpha - 1, -alpha, start_time, time_limit)
            if alpha < eval < beta:
                # Re-search with full window if null-window search failed
                eval = -pvs(game, depth - 1, -beta, -alpha, start_time, time_limit)

        game.switch_player()
        game.undo_move(move_info, captured_piece_info)

        if eval > max_eval:
            max_eval = eval

        alpha = max(alpha, eval)
        if alpha >= beta:
            break  # Alpha-beta pruning

    transposition_table[zobrist_hash] = {'value': max_eval, 'depth': depth}
    return max_eval

# Negamax with Alpha-Beta Pruning and Iterative Deepening
def negamax(game, depth, alpha, beta, start_time, time_limit, killer_moves):
    if time.time() - start_time > time_limit:
        raise TimeoutError

    # Check for terminal conditions
    winner = game.check_win()
    if winner == game.current_player:
        return float('inf')
    elif winner == ('W' if game.current_player == 'B' else 'B'):
        return float('-inf')

    if depth == 0:
        return game.evaluate()

    max_eval = float('-inf')
    moves = game.get_all_moves()
    moves = order_moves(game, moves, killer_moves, depth)  # Pass killer_moves and depth

    for move in moves:
        start, end = move
        move_info, captured_piece_info = game.make_move(start, end)
        game.switch_player()
        try:
            eval = -negamax(game, depth - 1, -beta, -alpha, start_time, time_limit, killer_moves)
        except TimeoutError:
            game.switch_player()
            game.undo_move(move_info, captured_piece_info)
            raise TimeoutError
        game.switch_player()
        game.undo_move(move_info, captured_piece_info)

        if eval > max_eval:
            max_eval = eval

        alpha = max(alpha, eval)
        if alpha >= beta:
            # Beta cutoff - record the killer move
            if depth not in killer_moves:
                killer_moves[depth] = []
            if move not in killer_moves[depth]:
                killer_moves[depth].append(move)
                # Keep only the top 2 killer moves per depth
                if len(killer_moves[depth]) > 2:
                    killer_moves[depth] = killer_moves[depth][-2:]
            break  # Alpha-beta pruning

    return max_eval

# AI move selection with Iterative Deepening
def get_ai_move(game, max_depth, time_limit):
    best_move = None
    start_time = time.time()
    global transposition_table
    transposition_table = {}
    killer_moves = {}  # Initialize killer moves


    # Check if there are mandatory captures
    capture_moves = []
    all_moves = game.get_all_moves()
    for move in all_moves:
        start, end = move
        if game.is_capture_move(start, end):
            capture_moves.append(move)

    if capture_moves:
        # If only one capture move is available, make it immediately
        if len(capture_moves) == 1:
            return capture_moves[0]
        else:
            # If multiple captures are available, search among them
            moves_to_consider = capture_moves
            search_depth = 1  # Shallow search since captures are mandatory
    else:
        moves_to_consider = all_moves
        search_depth = max_depth  # Use the provided max_depth

    # Iterative Deepening
    for depth in range(1, search_depth + 1):
        print('Enter depth:', depth)
        if time.time() - start_time > time_limit:
            break

        max_eval = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        current_best_move = None

        moves = game.get_all_moves()
        moves = order_moves(game, moves, killer_moves, depth)

        for move in moves:
            if time.time() - start_time > time_limit:
                break

            start, end = move
            move_info, captured_piece_info = game.make_move(start, end)
            game.switch_player()
            try:
                eval = -negamax(game, depth - 1, -beta, -alpha, start_time, time_limit, killer_moves)
            except TimeoutError:
                game.switch_player()
                game.undo_move(move_info, captured_piece_info)
                break
            game.switch_player()
            game.undo_move(move_info, captured_piece_info)

            if eval > max_eval:
                max_eval = eval
                current_best_move = move

            alpha = max(alpha, eval)
            if alpha >= beta:
                break

        if current_best_move:
            best_move = current_best_move

        if time.time() - start_time > time_limit:
            break

    return best_move

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