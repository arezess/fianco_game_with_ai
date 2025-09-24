# Fianco Game

A Python implementation of the Fianco board game with AI opponent using Pygame.

## File Structure

The code has been organized into separate modules for better maintainability:

### `constants.py`
- Game constants (board size, colors, screen dimensions)
- Pygame initialization
- Global variables (Zobrist hashing tables, transposition table, etc.)

### `game.py`
- `FiancoGame` class containing all game logic
- Board representation and state management
- Move validation and execution
- Win condition checking
- Zobrist hashing for position caching

### `ai.py`
- AI engine with advanced algorithms
- Board evaluation function
- Negamax algorithm with alpha-beta pruning
- Principal Variation Search (PVS)
- Move ordering and killer move heuristics
- Iterative deepening search

### `ui.py`
- User interface functions
- Color selection menu
- Sidebar with move history and buttons
- Button drawing utilities

### `main.py`
- Main game loop and entry point
- Event handling for human player
- AI move execution
- Undo/Redo functionality

## How to Run

1. Make sure you have pygame installed:
   ```bash
   pip install pygame
   ```

2. Run the main file:
   ```bash
   python main.py
   ```

## Dependencies

- `pygame` - For graphics and user interface
- `random` - For Zobrist hashing
- `time` - For AI time management
- `sys` - For system operations

## Features

- Human vs AI gameplay
- Choose to play as Black or White
- Advanced AI with configurable depth
- Move history display
- Undo/Redo functionality
- Zobrist hashing for position caching
- Iterative deepening search
- Principal Variation Search optimization

## Game Rules

Fianco is played on a 9x9 board where players try to advance their pieces to the opposite side or eliminate all opponent pieces. The game features mandatory captures and strategic positioning.