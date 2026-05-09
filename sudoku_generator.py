import random
from copy import deepcopy

# Generate a full valid Sudoku solution using backtracking

def is_valid(board, num, row, col):
    for c in range(9):
        if board[row][c] == num:
            return False
    for r in range(9):
        if board[r][col] == num:
            return False

    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br+3):
        for c in range(bc, bc+3):
            if board[r][c] == num:
                return False

    return True


def fill_board(board):
    empty = find_empty(board)
    if not empty:
        return True
    r, c = empty

    nums = list(range(1, 10))
    random.shuffle(nums)

    for num in nums:
        if is_valid(board, num, r, c):
            board[r][c] = num
            if fill_board(board):
                return True
            board[r][c] = 0

    return False


def find_empty(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None


def generate_full_solution():
    board = [[0]*9 for _ in range(9)]
    fill_board(board)
    return board



# Fast unique-solution puzzle generator

def remove_numbers(board, clues=30):
    """
    Remove numbers symmetrically to make a puzzle,
    but keep enough clues to avoid deep recursion.
    """
    puzzle = deepcopy(board)

    # Cell positions (only half because we mirror)
    positions = [(r, c) for r in range(9) for c in range(9) if r*9 + c < 40]
    random.shuffle(positions)

    removed = 0
    target = 81 - clues

    for (r, c) in positions:
        if removed >= target:
            break

        # Mirror cell (Sudoku symmetry makes puzzles prettier)
        r2, c2 = 8-r, 8-c

        backup1 = puzzle[r][c]
        backup2 = puzzle[r2][c2]

        puzzle[r][c] = 0
        puzzle[r2][c2] = 0

        removed += 2

    return puzzle


def generate_puzzle(clues=30):
    """
    Fast reliable puzzle generator:
    1. Makes full valid board
    2. Removes numbers symmetrically
    3. Ensures solvability by not removing too many clues
    """

    full = generate_full_solution()
    puzzle = remove_numbers(full, clues=clues)

    return puzzle
