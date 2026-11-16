import math

def _slide_row(row):
    nz = [v for v in row if v != 0]
    out, i = [], 0
    while i < len(nz):
        if i + 1 < len(nz) and nz[i] == nz[i + 1]:
            out.append(nz[i] * 2); i += 2
        else:
            out.append(nz[i]); i += 1
    return out + [0] * (4 - len(out))

def simulate(board, direction):
    b = [r[:] for r in board]
    moved = False
    rows = direction in ('up', 'down')
    rev  = direction in ('right', 'down')
    for i in range(4):
        line = [b[0][i], b[1][i], b[2][i], b[3][i]] if rows else b[i][:]
        if rev: line.reverse()
        slid = _slide_row(line)
        if rev: slid.reverse()
        for j in range(4):
            r, c = (j, i) if rows else (i, j)
            if b[r][c] != slid[j]: moved = True
            b[r][c] = slid[j]
    return b, moved

def score(board):
    empties = smooth = 0
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                empties += 1; continue
            v = math.log2(board[r][c])
            if c < 3 and board[r][c+1]:
                smooth -= abs(v - math.log2(board[r][c+1]))
            if r < 3 and board[r+1][c]:
                smooth -= abs(v - math.log2(board[r+1][c]))
    max_v = max(max(row) for row in board)
    corner = max_v in (board[0][0], board[0][3], board[3][0], board[3][3])
    return empties * 270 + smooth * 15 + (500 if corner else 0) + math.log2(max_v) * 60

def best_move(board):
    best, bs = None, -float('inf')
    for d in ('up', 'right', 'down', 'left'):
        nb, moved = simulate(board, d)
        if not moved: continue
        s = score(nb)
        if s > bs: bs, best = s, d
    return best