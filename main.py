"""
main.py — Play chess against your engine in the terminal!

Usage:
    python main.py              # You play as White vs engine
    python main.py --black      # You play as Black vs engine
    python main.py --auto       # Engine vs Engine (watch it play itself)
    python main.py --depth 4    # Set search depth (default 3)

Controls during the game:
    e2e4          Move from e2 to e4
    e7e8q         Promote pawn to queen
    undo          Take back your last move (+ engine's reply)
    resign        Resign the game
    fen           Print the current FEN string
    quit / exit   Quit
"""

import sys
from board import Board, Move
from moves import get_legal_moves, is_checkmate, is_stalemate, is_in_check
from search import find_best_move


def parse_args():
    args = sys.argv[1:]
    human_color = 'w'
    auto        = False
    depth       = 3

    if '--black'  in args: human_color = 'b'
    if '--auto'   in args: auto = True
    if '--depth'  in args:
        idx = args.index('--depth')
        depth = int(args[idx + 1])

    return human_color, auto, depth


def print_header(human_color, auto, depth):
    print()
    print("  ♟  Chess Engine — Python from Scratch")
    print("  " + "─" * 38)
    if auto:
        print(f"  Mode:  Engine vs Engine  (depth {depth})")
    else:
        side = 'White' if human_color == 'w' else 'Black'
        print(f"  Mode:  You ({side}) vs Engine  (depth {depth})")
        print("  Moves: e2e4  ·  g1f3  ·  e7e8q")
        print("  Commands: undo · resign · fen · quit")
    print("  " + "─" * 38)


def game_over_message(board):
    """Check and print game-over conditions. Returns True if the game is over."""
    if is_checkmate(board):
        winner = 'Black' if board.turn == 'w' else 'White'
        print(f"\n  ♛  Checkmate!  {winner} wins!\n")
        return True
    if is_stalemate(board):
        print("\n  ½  Stalemate — it's a draw!\n")
        return True
    if board.halfmove_clock >= 100:
        print("\n  ½  Draw by the fifty-move rule.\n")
        return True
    return False


def human_turn(board) -> bool:
    """Prompt human for a move. Returns False if they want to quit."""
    legal = get_legal_moves(board)
    legal_alg = {m.to_algebraic() for m in legal}

    while True:
        try:
            raw = input("  Your move › ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            return False

        if raw in ('quit', 'exit'):
            print("  Goodbye!")
            return False

        if raw == 'resign':
            winner = 'Black' if board.turn == 'w' else 'White'
            print(f"\n  You resigned. {winner} wins!\n")
            return False

        if raw == 'fen':
            print(f"  FEN: {board.to_fen()}")
            continue

        if raw == 'undo':
            if len(board.history) >= 2:
                board.undo_move()   # Undo engine reply
                board.undo_move()   # Undo human move
                board.display()
            else:
                print("  Nothing to undo.")
            continue

        if len(raw) < 4:
            print("  ✗  Use coordinate notation, e.g. e2e4")
            continue

        try:
            move = Move.from_algebraic(raw)
        except (ValueError, IndexError):
            print("  ✗  Couldn't parse that move.")
            continue

        if move.to_algebraic() not in legal_alg:
            # Try to give a helpful hint
            piece_moves = [m.to_algebraic() for m in legal
                           if m.from_sq == move.from_sq]
            if piece_moves:
                print(f"  ✗  Illegal. That piece can go to: {', '.join(sorted(piece_moves))}")
            else:
                print("  ✗  Illegal move.")
            continue

        board.make_move(move)
        board.display()
        return True


def play():
    human_color, auto, depth = parse_args()
    board = Board()

    print_header(human_color, auto, depth)
    board.display(perspective=human_color if not auto else 'w')

    while True:
        if game_over_message(board):
            break

        if is_in_check(board, board.turn):
            print("  ⚠  Check!")

        if auto or board.turn != human_color:
            # Engine move
            print()
            move = find_best_move(board, depth=depth)
            if move is None:
                break
            board.make_move(move)
            board.display(perspective=human_color if not auto else 'w')
        else:
            # Human move
            if not human_turn(board):
                break


if __name__ == '__main__':
    play()
