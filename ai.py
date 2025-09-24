# ai.py
import time
from constants import *

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