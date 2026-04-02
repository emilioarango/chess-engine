"""
search.py — Minimax search with Alpha-Beta pruning

─────────────────────────────────────────────────────────────────────────────
MINIMAX
─────────────────────────────────────────────────────────────────────────────
Assume both sides play perfectly:
  • White (maximiser) always picks the move with the HIGHEST score.
  • Black (minimiser) always picks the move with the LOWEST score.

At depth 0 we call evaluate() to score the leaf position.

─────────────────────────────────────────────────────────────────────────────
ALPHA-BETA PRUNING
─────────────────────────────────────────────────────────────────────────────
Keep two bounds:
  alpha = best score the maximiser is already guaranteed
  beta  = best score the minimiser is already guaranteed

If at any node beta ≤ alpha, the other player will never allow us to reach
this position, so we can skip ("prune") the remaining siblings.

In practice this lets us search roughly twice as deep for the same time cost.

─────────────────────────────────────────────────────────────────────────────
MOVE ORDERING
─────────────────────────────────────────────────────────────────────────────
Alpha-beta is most effective when the best move is searched first.
A cheap heuristic: try captures (especially winning captures) before quiet moves.
"""

from board import Board, Move
from moves import get_legal_moves, is_checkmate, is_stalemate
from evaluate import evaluate, PIECE_VALUES
from typing import Optional, Tuple
import time

INF = float('inf')


# ── Move ordering ─────────────────────────────────────────────────────────────

def _mvv_lva(board: Board, move: Move) -> int:
    """
    MVV-LVA: Most Valuable Victim – Least Valuable Attacker.
    Captures are scored by (victim value - attacker value / 10) so we
    prefer capturing a queen with a pawn over capturing a pawn with a queen.
    Returns 0 for quiet moves (not a capture).
    """
    target = board.squares[move.to_sq[0]][move.to_sq[1]]
    if target == '.':
        return 10 if move.promotion else 0     # promotions before quiet moves
    attacker = board.squares[move.from_sq[0]][move.from_sq[1]].upper()
    victim   = target.upper()
    return PIECE_VALUES.get(victim, 0) - PIECE_VALUES.get(attacker, 0) // 10


def _order_moves(board: Board, moves: list) -> list:
    return sorted(moves, key=lambda m: _mvv_lva(board, m), reverse=True)


# ── Alpha-Beta search ─────────────────────────────────────────────────────────

def _alpha_beta(board: Board, depth: int, alpha: float, beta: float,
                maximising: bool) -> Tuple[float, Optional[Move]]:
    """
    Recursive minimax with alpha-beta pruning.

    Returns (score, best_move).
    score is always from White's perspective (positive = White winning).
    """

    # ── Terminal conditions ──────────────────────────────────────────────────
    if is_checkmate(board):
        # The side to move has no legal moves and is in check — they lose.
        # Return a large penalty for the loser (with depth adjustment so
        # the engine prefers mates that happen sooner).
        return (-INF + depth if maximising else INF - depth), None

    if is_stalemate(board):
        return 0, None

    if depth == 0:
        return evaluate(board), None

    # ── Recursive case ───────────────────────────────────────────────────────
    legal_moves = _order_moves(board, get_legal_moves(board))
    best_move: Optional[Move] = None

    if maximising:
        best_score = -INF
        for move in legal_moves:
            board.make_move(move)
            score, _ = _alpha_beta(board, depth - 1, alpha, beta, False)
            board.undo_move()

            if score > best_score:
                best_score = score
                best_move  = move
            alpha = max(alpha, score)
            if beta <= alpha:
                break          # ← Beta cut-off: minimiser won't allow this branch

        return best_score, best_move

    else:
        best_score = INF
        for move in legal_moves:
            board.make_move(move)
            score, _ = _alpha_beta(board, depth - 1, alpha, beta, True)
            board.undo_move()

            if score < best_score:
                best_score = score
                best_move  = move
            beta = min(beta, score)
            if beta <= alpha:
                break          # ← Alpha cut-off: maximiser won't allow this branch

        return best_score, best_move


# ── Public API ────────────────────────────────────────────────────────────────

def find_best_move(board: Board, depth: int = 3) -> Optional[Move]:
    """
    Find the best move for the side to move.

    Args:
        board: Current position.
        depth: Search depth in plies (half-moves). Higher = stronger but slower.
               Depth 3 ≈ instant, depth 4 ≈ 1-5 s, depth 5 ≈ 10-60 s.

    Returns:
        The best Move found, or None if there are no legal moves.
    """
    start       = time.time()
    maximising  = board.turn == 'w'
    score, move = _alpha_beta(board, depth, -INF, INF, maximising)
    elapsed     = time.time() - start

    color = 'White' if board.turn == 'w' else 'Black'
    if abs(score) > INF / 2:
        score_str = 'Mate' if score > 0 else '-Mate'
    else:
        score_str = f"{score/100:+.2f}"

    print(f"  ┌ Engine ({color}): {move.to_algebraic() if move else '—'}"
          f"  score={score_str}  depth={depth}  time={elapsed:.2f}s")

    return move
