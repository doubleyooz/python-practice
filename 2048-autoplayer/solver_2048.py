import math
import logging
from typing import Literal, List, Tuple


directions = ['up', 'right', 'down', 'left']

type Tile = int
type Board = List[List[Tile]]
type BoardDirection = Literal['up', 'right', 'down', 'left']


def _slide_row(row: List[Tile]) -> List[Tile]:
    nz = filter_out_empty_cells(row)
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

def monotonicity_penalty(line: List[Tile]) -> tuple[float, float]:
    values = [math.log2(v) for v in line if v]

    increasing = 0.0
    decreasing = 0.0

    for a, b in zip(values, values[1:]):
        if a > b:
            increasing += a - b
        else:
            decreasing += b - a

    return increasing, decreasing

def filter_out_empty_cells(row: List[Tile]) -> List[Tile]:
    return [val for val in row if val != 0]

def is_monotonic(row: List[Tile]) -> bool:
    filtered_row = filter_out_empty_cells(row)
    if len(filtered_row) < 2:
        return True
    return all(filtered_row[i] <= filtered_row[i + 1] for i in range(len(filtered_row) - 1)) or \
           all(filtered_row[i] >= filtered_row[i + 1] for i in range(len(filtered_row) - 1))

def score(board: Board, logger: logging.Logger = None) -> (float, str):
    empties: int = 0
    smooth: float = 0.0
    monotonicity: float = 0.0
    board_size: int = len(board) * len(board[0]) if board else 0
    
    max_value: int = 0
    max_value_position: Tuple[int, int] = (-1, -1)
    
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
    
    second_highest, second_r, second_c = tiles[1] if len(tiles) > 1 else (0, -1, -1)
    second_highest_position = (second_r, second_c)
    
    third_highest, third_r, third_c = tiles[2] if len(tiles) > 2 else (0, -1, -1)
    third_highest_position = (third_r, third_c)

    max_at_the_corner: bool = max_value in (board[0][0], board[0][3], board[3][0], board[3][3])   
    max_at_preferred_corner: bool = max_value == board[0][0]
    max_near_preferred_row_or_column: bool = max_value_position[0] < 1 or max_value_position[1] < 1
    max_near_preferred_corner: bool = max_value_position in ((0, 0), (0, 1), (1, 0), (1, 1))
    
    max_adjacent_positions = get_adjacent_positions(max_value_position)
    second_adjacent_positions = get_adjacent_positions(second_highest_position) if second_highest_position != (-1, -1) else []
    third_adjacent_positions = get_adjacent_positions(third_highest_position) if third_highest_position != (-1, -1) else []
    
    second_next_to_max = second_highest_position in max_adjacent_positions
    third_next_to_second = third_highest_position in second_adjacent_positions
    
       
    bonus = 10 
    corner_bonuses = (
          (3 * bonus if max_at_preferred_corner else 0)
        + (bonus if max_at_the_corner else 0)
        + (2 * bonus if max_near_preferred_corner else 0)
        + (2 * bonus if max_near_preferred_row_or_column else 0)
        + (3 * bonus if second_next_to_max and max_at_preferred_corner else 0)
        + (3 * bonus if second_next_to_max and max_near_preferred_row_or_column else 0)
    )
    
    corner_bonuses *= 1 + 3 * (board_size - empties) / board_size
    monoticity_bonus = monotonicity * 1.5 * bonus
    smoothness_bonus = smooth * 1.5 * bonus 
    empty_bonus = 3 * empties * bonus ** 1.5
    total_score: float = (
        empty_bonus
        + smoothness_bonus
        + monoticity_bonus
        + corner_bonuses
        + (5 * bonus if second_next_to_max else 0)        
        + (3 * bonus if third_next_to_second else 0)
        + math.log2(max_value) * 6 * bonus
    )
    foo = f"Empties: {empty_bonus:.2f}, Smoothness: {smoothness_bonus:.2f}, Monotonicity: {monoticity_bonus:.2f}, Corner Bonuses: {corner_bonuses:.2f}, Max Tile: {max_value}, Total Score: {total_score:.2f}"
    logger and logger.debug(foo)
    
    return total_score, foo

def best_move(board: Board, depth: int = 2, logger: logging.Logger = None) -> tuple[BoardDirection | None, float]:
    best_direction: BoardDirection | None = None
    best_score: float = -math.inf
    
    
    if depth <= 0:
        s, foo = score(board, logger)
        
        logger and logger.info(f"Depth limit reached (depth=0). Board score: {s:.2f}")
        return best_direction, s
   
    
    for direction in directions:
        new_board, moved = simulate(board, direction, logger)
        if not moved: continue
        
        if depth == 1:
            new_score, foo = score(new_board, logger)
            logger and logger.info(f"Direction {direction} score = {new_score:.2f} {foo}")
        else: 
        
            possible_boards = spawn_possible_boards(new_board)
           
            if depth > 1:              
          
                new_score = sum([
                    best_move(pb, depth - 1, logger)[1] * prob
                    for pb, prob in possible_boards
                ])
                
                logger and logger.debug(f"({len(possible_boards)}) Direction {direction} score = {new_score:.2f}")
        
        if new_score > best_score:
            best_score, best_direction = new_score, direction
    return best_direction, best_score