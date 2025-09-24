# constants.py
import pygame
import random

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