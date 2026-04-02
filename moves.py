"""
moves.py — Move generation

Two-phase approach:
  1. Pseudo-legal moves: what pieces can physically do, ignoring check.
  2. Legal moves: filter pseudo-legal moves that leave the king in check.

We also provide `is_attacked`, a direct attack-detection function that
does NOT recurse through move generation, which keeps things simple and fast.
"""

from board import Board, Move
from typing import List, Tuple, Optional


# ── Attack detection (no recursion) ──────────────────────────────────────────

def is_attacked(board: Board, sq: Tuple[int, int], by_color: str) -> bool:
    """
    Return True if `sq` is attacked by any piece of `by_color`.
    Uses ray-casting and pattern matching — no move generation, no recursion.
    """
    row, col = sq
    opp = by_color

    # Pawn attacks — a white pawn at (r+1, c±1) attacks (r, c)
    if opp == 'w':
        for dc in (-1, 1):
            r, c = row + 1, col + dc
            if board.in_bounds(r, c) and board.squares[r][c] == 'P':
                return True
    else:
        for dc in (-1, 1):
            r, c = row - 1, col + dc
            if board.in_bounds(r, c) and board.squares[r][c] == 'p':
                return True

    # Knight attacks
    knight = 'N' if opp == 'w' else 'n'
    for dr, dc in ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)):
        r, c = row + dr, col + dc
        if board.in_bounds(r, c) and board.squares[r][c] == knight:
            return True

    # Bishop / Queen diagonals
    bq = ('B','Q') if opp == 'w' else ('b','q')
    for dr, dc in ((-1,-1),(-1,1),(1,-1),(1,1)):
        r, c = row + dr, col + dc
        while board.in_bounds(r, c):
            p = board.squares[r][c]
            if p != '.':
                if p in bq: return True
                break
            r += dr; c += dc

    # Rook / Queen straights
    rq = ('R','Q') if opp == 'w' else ('r','q')
    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
        r, c = row + dr, col + dc
        while board.in_bounds(r, c):
            p = board.squares[r][c]
            if p != '.':
                if p in rq: return True
                break
            r += dr; c += dc

    # King attacks
    king = 'K' if opp == 'w' else 'k'
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == dc == 0: continue
            r, c = row + dr, col + dc
            if board.in_bounds(r, c) and board.squares[r][c] == king:
                return True

    return False


def is_in_check(board: Board, color: str) -> bool:
    """Return True if `color`'s king is currently in check."""
    king = 'K' if color == 'w' else 'k'
    for row in range(8):
        for col in range(8):
            if board.squares[row][col] == king:
                return is_attacked(board, (row, col), board.opponent() if color == board.turn
                                   else board.turn)
    return True   # King missing — shouldn't happen in a valid game


def _king_in_check(board: Board) -> bool:
    """Check if the side that just moved left their king in check."""
    # After make_move, board.turn has already flipped to the opponent.
    # We want to check the player who just moved, i.e. the current opponent.
    color = board.opponent()
    king = 'K' if color == 'w' else 'k'
    attacker = board.turn              # the side now to move is the attacker
    for row in range(8):
        for col in range(8):
            if board.squares[row][col] == king:
                return is_attacked(board, (row, col), attacker)
    return True


# ── Legal move generation ─────────────────────────────────────────────────────

def get_legal_moves(board: Board) -> List[Move]:
    """
    Generate all legal moves for the side to move.
    Filters pseudo-legal moves that leave the king in check.
    """
    legal = []
    for move in _pseudo_legal_moves(board):
        board.make_move(move)
        if not _king_in_check(board):
            legal.append(move)
        board.undo_move()
    return legal


def is_checkmate(board: Board) -> bool:
    return is_in_check(board, board.turn) and not get_legal_moves(board)


def is_stalemate(board: Board) -> bool:
    return not is_in_check(board, board.turn) and not get_legal_moves(board)


# ── Pseudo-legal move generators ─────────────────────────────────────────────

def _pseudo_legal_moves(board: Board) -> List[Move]:
    """All moves the current side can make, ignoring whether they leave king in check."""
    moves: List[Move] = []
    for row in range(8):
        for col in range(8):
            piece = board.squares[row][col]
            if piece == '.' or board.color(piece) != board.turn:
                continue
            sq = (row, col)
            t  = piece.upper()
            if   t == 'P': moves.extend(_pawn_moves(board, sq))
            elif t == 'N': moves.extend(_knight_moves(board, sq))
            elif t == 'B': moves.extend(_bishop_moves(board, sq))
            elif t == 'R': moves.extend(_rook_moves(board, sq))
            elif t == 'Q': moves.extend(_queen_moves(board, sq))
            elif t == 'K': moves.extend(_king_moves(board, sq))
    return moves


def _pawn_moves(board: Board, sq: Tuple[int,int]) -> List[Move]:
    moves: List[Move] = []
    row, col = sq
    piece = board.squares[row][col]
    white     = piece.isupper()
    direction = -1 if white else 1          # white moves toward row 0
    start_row = 6  if white else 1
    promo_row = 0  if white else 7

    # One square forward
    nr = row + direction
    if board.in_bounds(nr, col) and board.squares[nr][col] == '.':
        if nr == promo_row:
            for p in ('Q','R','B','N'):
                moves.append(Move(sq, (nr, col), promotion=p))
        else:
            moves.append(Move(sq, (nr, col)))
            # Two squares from starting rank
            if row == start_row:
                nr2 = row + 2 * direction
                if board.squares[nr2][col] == '.':
                    moves.append(Move(sq, (nr2, col)))

    # Diagonal captures (including en-passant)
    for dc in (-1, 1):
        nc = col + dc
        if not board.in_bounds(nr, nc):
            continue
        target = board.squares[nr][nc]
        enemy  = (white and board.color(target) == 'b') or \
                 (not white and board.color(target) == 'w')
        ep     = (nr, nc) == board.en_passant

        if enemy or ep:
            if nr == promo_row:
                for p in ('Q','R','B','N'):
                    moves.append(Move(sq, (nr, nc), promotion=p))
            else:
                moves.append(Move(sq, (nr, nc)))

    return moves


def _knight_moves(board: Board, sq: Tuple[int,int]) -> List[Move]:
    moves: List[Move] = []
    row, col = sq
    for dr, dc in ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)):
        nr, nc = row + dr, col + dc
        if board.in_bounds(nr, nc) and board.color(board.squares[nr][nc]) != board.turn:
            moves.append(Move(sq, (nr, nc)))
    return moves


def _slide(board: Board, sq: Tuple[int,int], directions) -> List[Move]:
    """Generate sliding moves (bishop / rook / queen)."""
    moves: List[Move] = []
    row, col = sq
    for dr, dc in directions:
        nr, nc = row + dr, col + dc
        while board.in_bounds(nr, nc):
            target = board.squares[nr][nc]
            if target == '.':
                moves.append(Move(sq, (nr, nc)))
            elif board.color(target) != board.turn:   # enemy — capture and stop
                moves.append(Move(sq, (nr, nc)))
                break
            else:                                      # friendly — blocked
                break
            nr += dr; nc += dc
    return moves


def _bishop_moves(board: Board, sq): return _slide(board, sq, ((-1,-1),(-1,1),(1,-1),(1,1)))
def _rook_moves  (board: Board, sq): return _slide(board, sq, ((-1,0),(1,0),(0,-1),(0,1)))
def _queen_moves (board: Board, sq): return _slide(board, sq, ((-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)))


def _king_moves(board: Board, sq: Tuple[int,int]) -> List[Move]:
    moves: List[Move] = []
    row, col = sq

    # Normal one-square moves
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == dc == 0: continue
            nr, nc = row + dr, col + dc
            if board.in_bounds(nr, nc) and board.color(board.squares[nr][nc]) != board.turn:
                moves.append(Move(sq, (nr, nc)))

    # Castling
    # The king must not be in check, and must not pass through an attacked square.
    # We use is_attacked() directly to avoid any recursion.
    attacker = board.opponent()

    if board.turn == 'w' and (row, col) == (7, 4):
        # Kingside: e1-g1, rook on h1
        if (board.castling.get('wK') and
                board.squares[7][5] == '.' and board.squares[7][6] == '.' and
                not is_attacked(board, (7,4), attacker) and
                not is_attacked(board, (7,5), attacker)):
            moves.append(Move(sq, (7, 6)))
        # Queenside: e1-c1, rook on a1
        if (board.castling.get('wQ') and
                board.squares[7][1] == '.' and board.squares[7][2] == '.' and
                board.squares[7][3] == '.' and
                not is_attacked(board, (7,4), attacker) and
                not is_attacked(board, (7,3), attacker)):
            moves.append(Move(sq, (7, 2)))

    elif board.turn == 'b' and (row, col) == (0, 4):
        # Kingside: e8-g8
        if (board.castling.get('bK') and
                board.squares[0][5] == '.' and board.squares[0][6] == '.' and
                not is_attacked(board, (0,4), attacker) and
                not is_attacked(board, (0,5), attacker)):
            moves.append(Move(sq, (0, 6)))
        # Queenside: e8-c8
        if (board.castling.get('bQ') and
                board.squares[0][1] == '.' and board.squares[0][2] == '.' and
                board.squares[0][3] == '.' and
                not is_attacked(board, (0,4), attacker) and
                not is_attacked(board, (0,3), attacker)):
            moves.append(Move(sq, (0, 2)))

    return moves
