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
    empty_cells = [
        (r, c) for r in range(4)
        for c in range(4) if does_empty_cell_border_non_empty_cell((r, c), board)
    ]
    if not empty_cells: return [(board, 1.0)]
    
    
    num_empty = len(empty_cells)
    possible_boards = []
    for r, c in empty_cells:
        for value, base_prob in ((2, 0.9), (4, 0.1)):    
            new_board = [row[:] for row in board]        
            new_board[r][c] = value
            
            prob = base_prob / num_empty
            possible_boards.append((new_board, prob))
            
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

def get_adjacent_positions(
        pos: Tuple[int, int],
        rows: int = 4, 
        cols: int = 4
    ) -> List[Tuple[int, int]]:
    r, c = pos
    adjacent_positions = []
    if r > 0: adjacent_positions.append((r - 1, c))
    if r < rows - 1: adjacent_positions.append((r + 1, c))
    if c > 0: adjacent_positions.append((r, c - 1))
    if c < cols - 1: adjacent_positions.append((r, c + 1))
    return adjacent_positions

def monotonicity_penalty(line: list[Tile]) -> tuple[float, float]:
    values = [math.log2(v) for v in line if v]

    increasing = 0.0
    decreasing = 0.0

    for a, b in zip(values, values[1:]):
        if a > b:
            increasing += a - b
        else:
            decreasing += b - a

    return increasing, decreasing

def is_monotonic(row: list[Tile]) -> bool:
    filtered_row = [value for value in row if value != 0]
    if len(filtered_row) < 2:
        return True
    return all(filtered_row[i] <= filtered_row[i + 1] for i in range(len(filtered_row) - 1)) or \
           all(filtered_row[i] >= filtered_row[i + 1] for i in range(len(filtered_row) - 1))

def score(board: Board, logger: logging.Logger = None) -> float:
    empties: int = 0
    smooth: float = 0.0
    monotonicity: float = 0.0
    
    max_value: int = 0
    max_value_position: Tuple[int, int] = (-1, -1)
    second_highest_position = (-1, -1)
    tiles = []
          
    for c in range(4):
        column = [board[r][c] for r in range(4)]
        monotonicity -= min(monotonicity_penalty(column))
          
    for r in range(4):
        monotonicity -= min(monotonicity_penalty(board[r]))
        for c in range(4):           
            
            if board[r][c] == 0:
                empties += 1
                continue
            tiles.append((board[r][c], r, c))
                    
            v: float = math.log2(board[r][c])
            if c < 3 and board[r][c + 1]:
                smooth -= abs(v - math.log2(board[r][c + 1]))
            if r < 3 and board[r + 1][c]:
                smooth -= abs(v - math.log2(board[r + 1][c]))
    
    if not tiles:
        return 0.0
       
    # Sort tiles descending by value to reliably find max and second-to-max
    tiles.sort(key=lambda x: x[0], reverse=True)
    max_value, max_r, max_c = tiles[0]
    max_value_position = (max_r, max_c)
    
    second_highest = max_value
    
    for val, r, c in tiles:
        if val < max_value:
            second_highest = val
            second_highest_position = (r, c)
            break
    
    
    max_at_the_corner: bool = max_value in (board[0][0], board[0][3], board[3][0], board[3][3])   
    max_at_preferred_corner: bool = max_value == board[0][0]
    max_near_preferred_corner: bool = max_value in (board[0][1], board[1][0], board[1][1])
    
    max_adjacent_positions = get_adjacent_positions(max_value_position)
    second_adjacent_positions = get_adjacent_positions(second_highest_position) if second_highest_position != (-1, -1) else []
    
    second_next_to_max = second_highest_position in max_adjacent_positions
    
    second_next_to_third: bool = any(
        board[pos[0]][pos[1]] == second_highest / 2
        for pos in second_adjacent_positions
    ) if second_highest_position != (-1, -1) else False
       
    
    total_score: float = (
        270 * empties ** 1.5
        + smooth * 15
        + monotonicity * 10
        + (100 if max_at_preferred_corner else 0)
        + (100 if max_at_the_corner else 0)
        + (100 if max_near_preferred_corner else 0)
        + (100 if second_next_to_max else 0)
        + (500 if second_next_to_max and max_at_preferred_corner else 0)
        + (100 if second_next_to_third else 0)
        + math.log2(max_value) * 60
    )
    logger and logger.debug(
        f"Scoring board -> Empties: {empties}, Smoothness: {smooth:.2f}, Corner Bonus: {max_at_the_corner}, Max Tile: {max_value}, Total Score: {total_score:.2f}"
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
                
                logger and logger.info(f"({len(possible_boards)}) Direction {direction} score = {new_score:.2f}")
        
        if new_score > best_score:
            best_score, best_direction = new_score, direction
    return best_direction, best_score