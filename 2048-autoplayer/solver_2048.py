import math
import logging
from typing import Literal, List, Tuple


directions = ['up', 'right', 'down', 'left']

type Tile = int
type Board = list[list[Tile]]
type BoardDirection = Literal['up', 'right', 'down', 'left']


def _slide_row(row: list[Tile]) -> list[Tile]:
    nz = [value for value in row if value != 0]
    out, i = [], 0
    while i < len(nz):
        if i + 1 < len(nz) and nz[i] == nz[i + 1]:
            out.append(nz[i] * 2); i += 2
        else:
            out.append(nz[i]); i += 1
    return out + [0] * (4 - len(out))

def does_empty_cell_border_non_empty_cell(pos: Tuple[int, int], board: Board) -> bool:
    r, c = pos
    if board[r][c] == 0:
        if (r > 0 and board[r - 1][c] != 0) or \
           (r < 3 and board[r + 1][c] != 0) or \
                   (c > 0 and board[r][c - 1] != 0) or \
                   (c < 3 and board[r][c + 1] != 0):
                    return True
    return False

def spawn_possible_boards(board: Board) -> List[Tuple[Board, float]]:
    new_board = [r[:] for r in board] # copies board as it is into b
    empty_cells = [
        (r, c) for r in range(4)
        for c in range(4) if does_empty_cell_border_non_empty_cell((r, c), new_board)
    ]
    if not empty_cells: return (new_board, 1.0)
    possible_boards = []
    for r, c in empty_cells:
        for value in (2, 4):
            new_board[r][c] = value
            possible_boards.append(([row[:] for row in new_board], 0.9 if value == 2 else 0.1))
            new_board[r][c] = 0
    return possible_boards

def simulate(board: Board, direction: BoardDirection, logger: logging.Logger = None) -> tuple[Board, bool]:
    b = [r[:] for r in board] # copies board as it is into b
    moved = False
    is_vertical: bool = direction in ('up', 'down')
    is_to_be_reversed: bool = direction in ('right', 'down')
    if logger:
        logger.debug(f"Simulating move direction: {direction}")
    for i in range(4):
        line = [b[0][i], b[1][i], b[2][i], b[3][i]] if is_vertical else b[i][:]
        if is_to_be_reversed: line.reverse()
        slid = _slide_row(line)
        if is_to_be_reversed: slid.reverse()
        for j in range(4):
            r, c = (j, i) if is_vertical else (i, j)
            if b[r][c] != slid[j]: moved = True
            b[r][c] = slid[j]
    
    logger and logger.debug(f"Simulation result for {direction} - Moved: {moved}")
        
    return b, moved


def score(board: Board, logger: logging.Logger = None) -> float:
    empties: int = 0
    smooth: float = 0.0
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                empties += 1
                continue
            v: float = math.log2(board[r][c])
            if c < 3 and board[r][c + 1]:
                smooth -= abs(v - math.log2(board[r][c + 1]))
            if r < 3 and board[r + 1][c]:
                smooth -= abs(v - math.log2(board[r + 1][c]))
    max_value: int = max(max(row) for row in board)
    corner: bool = max_value in (board[0][0], board[0][3], board[3][0], board[3][3])
    is_preferred_corner: bool = max_value in (board[0][0], board[3][3])
    almost_corner: bool = max_value in (board[0][1], board[1][0], board[1][1])
    total_score: float = (
        empties * 270
        + smooth * 15
        + (1000 if is_preferred_corner else 0)
        + (500 if corner else 0)
        + (200 if almost_corner else 0)
        + math.log2(max_value) * 60
    )
    logger and logger.debug(
        f"Scoring board -> Empties: {empties}, Smoothness: {smooth:.2f}, Corner Bonus: {corner}, Max Tile: {max_value}, Total Score: {total_score:.2f}"
    )
    return total_score

def best_move(board: Board, depth: int = 2, logger: logging.Logger = None) -> tuple[BoardDirection | None, float]:
    best_direction: BoardDirection | None = None
    best_score: float = -math.inf
    
    
    if depth <= 0:
        s = score(board, logger)
        
        logger and logger.info(f"Depth limit reached (depth=0). Board score: {s:.2f}")
        return best_direction, s
   
    
    for direction in directions:
        new_board, moved = simulate(board, direction, logger)
        if not moved: continue
        
        if depth == 1:
            new_score = score(new_board, logger)
            logger and logger.debug(f"Direction {direction} (depth 1): score = {new_score:.2f}")
        else: 
        
            possible_boards = spawn_possible_boards(new_board)
           
            if depth > 1:              
          
                new_score = sum([
                    best_move(pb, depth - 1, logger)[1] * prob
                    for pb, prob in possible_boards
                ])
                
                logger and logger.info(f"Outcomes evaluated: {len(possible_boards)}")
                logger and logger.debug(f"Direction {direction} (depth 1): score = {new_score:.2f}")
        
        if new_score > best_score:
            best_score, best_direction = new_score, direction
    return best_direction, best_score