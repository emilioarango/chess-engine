"""
board.py — Chess board representation

Board layout:
  Row 0 = rank 8 (black's back rank)
  Row 7 = rank 1 (white's back rank)
  Col 0 = file a, Col 7 = file h

Piece encoding:
  White: P N B R Q K  (uppercase)
  Black: p n b r q k  (lowercase)
  Empty: '.'
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List


@dataclass
class Move:
    """Represents a single chess move."""
    from_sq: Tuple[int, int]          # (row, col) source square
    to_sq: Tuple[int, int]            # (row, col) destination square
    promotion: Optional[str] = None   # 'Q', 'R', 'B', or 'N' if pawn promotes

    # --- Fields filled in by make_move (needed for undo) ---
    captured: str = '.'
    was_en_passant: bool = False
    was_castling: bool = False
    castling_rook_from: Optional[Tuple[int, int]] = None
    castling_rook_to:   Optional[Tuple[int, int]] = None
    prev_en_passant: Optional[Tuple[int, int]] = None
    prev_castling: Optional[dict] = None
    prev_halfmove: int = 0

    # ── Algebraic notation helpers ───────────────────────────────────────────

    def to_algebraic(self) -> str:
        """Convert to coordinate notation, e.g. 'e2e4' or 'e7e8q'."""
        files = 'abcdefgh'
        ranks = '87654321'
        fr, fc = self.from_sq
        tr, tc = self.to_sq
        s = files[fc] + ranks[fr] + files[tc] + ranks[tr]
        if self.promotion:
            s += self.promotion.lower()
        return s

    @classmethod
    def from_algebraic(cls, notation: str) -> 'Move':
        """Parse coordinate notation like 'e2e4' or 'e7e8q'."""
        notation = notation.strip().lower()
        files = 'abcdefgh'
        ranks = '87654321'
        fc = files.index(notation[0])
        fr = ranks.index(notation[1])
        tc = files.index(notation[2])
        tr = ranks.index(notation[3])
        promotion = notation[4].upper() if len(notation) > 4 else None
        return cls((fr, fc), (tr, tc), promotion)

    def __repr__(self):
        return self.to_algebraic()


class Board:
    """
    Chess board using a simple 8×8 list.

    The board remembers full history so moves can be undone efficiently
    without copying the entire board state.
    """

    STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    def __init__(self, fen: str = None):
        self.squares: List[List[str]] = [['.' for _ in range(8)] for _ in range(8)]
        self.turn: str = 'w'                        # 'w' or 'b'
        self.castling: dict = {}                    # e.g. {'wK': True, 'wQ': True, ...}
        self.en_passant: Optional[Tuple[int,int]] = None  # target square
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1
        self.history: List[Move] = []

        self.load_fen(fen or self.STARTING_FEN)

    # ── FEN ──────────────────────────────────────────────────────────────────

    def load_fen(self, fen: str):
        """Set up position from a FEN string."""
        parts = fen.split()

        # 1. Piece placement
        self.squares = [['.' for _ in range(8)] for _ in range(8)]
        for row, rank_str in enumerate(parts[0].split('/')):
            col = 0
            for ch in rank_str:
                if ch.isdigit():
                    col += int(ch)
                else:
                    self.squares[row][col] = ch
                    col += 1

        # 2. Active colour
        self.turn = parts[1]

        # 3. Castling rights
        cs = parts[2]
        self.castling = {
            'wK': 'K' in cs, 'wQ': 'Q' in cs,
            'bK': 'k' in cs, 'bQ': 'q' in cs,
        }

        # 4. En-passant target
        if parts[3] != '-':
            files, ranks = 'abcdefgh', '87654321'
            self.en_passant = (ranks.index(parts[3][1]), files.index(parts[3][0]))
        else:
            self.en_passant = None

        # 5. Clocks
        self.halfmove_clock  = int(parts[4])
        self.fullmove_number = int(parts[5])

    def to_fen(self) -> str:
        """Export current position as a FEN string."""
        rows = []
        for row in self.squares:
            empty, rank_str = 0, ''
            for sq in row:
                if sq == '.':
                    empty += 1
                else:
                    if empty: rank_str += str(empty); empty = 0
                    rank_str += sq
            if empty: rank_str += str(empty)
            rows.append(rank_str)

        cs = (('K' if self.castling['wK'] else '') +
              ('Q' if self.castling['wQ'] else '') +
              ('k' if self.castling['bK'] else '') +
              ('q' if self.castling['bQ'] else '')) or '-'

        if self.en_passant:
            files, ranks = 'abcdefgh', '87654321'
            r, c = self.en_passant
            ep = files[c] + ranks[r]
        else:
            ep = '-'

        return f"{'/'.join(rows)} {self.turn} {cs} {ep} {self.halfmove_clock} {self.fullmove_number}"

    # ── Convenience helpers ───────────────────────────────────────────────────

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8

    def color(self, piece: str) -> Optional[str]:
        """Return 'w', 'b', or None for an empty square."""
        if piece.isupper() and piece != '.': return 'w'
        if piece.islower(): return 'b'
        return None

    def opponent(self) -> str:
        return 'b' if self.turn == 'w' else 'w'

    # ── Make / Undo ───────────────────────────────────────────────────────────

    def make_move(self, move: Move):
        """Apply a move, saving enough info to undo it later."""
        fr, fc = move.from_sq
        tr, tc = move.to_sq
        piece   = self.squares[fr][fc]

        # Save state needed for undo
        move.captured        = self.squares[tr][tc]
        move.prev_en_passant = self.en_passant
        move.prev_castling   = dict(self.castling)
        move.prev_halfmove   = self.halfmove_clock

        # Halfmove clock resets on pawn moves and captures
        self.halfmove_clock = 0 if (piece.upper() == 'P' or move.captured != '.') \
                              else self.halfmove_clock + 1

        # En-passant capture — remove the captured pawn
        if piece.upper() == 'P' and self.en_passant == (tr, tc):
            move.was_en_passant = True
            self.squares[fr][tc] = '.'  # The captured pawn sits on the mover's rank

        # Set new en-passant target (double pawn push)
        if piece.upper() == 'P' and abs(tr - fr) == 2:
            self.en_passant = ((fr + tr) // 2, fc)
        else:
            self.en_passant = None

        # Castling — move the rook too
        if piece.upper() == 'K' and abs(tc - fc) == 2:
            move.was_castling = True
            rook_col_from = 7 if tc > fc else 0
            rook_col_to   = 5 if tc > fc else 3
            move.castling_rook_from = (fr, rook_col_from)
            move.castling_rook_to   = (fr, rook_col_to)
            self.squares[fr][rook_col_to]   = self.squares[fr][rook_col_from]
            self.squares[fr][rook_col_from] = '.'

        # Place piece (handle promotion)
        landing = move.promotion if move.promotion else piece
        if move.promotion and self.turn == 'b':
            landing = landing.lower()
        self.squares[tr][tc] = landing
        self.squares[fr][fc] = '.'

        # Update castling rights whenever king or rook moves/is captured
        _cr_squares = {(7,4):'wK',(7,4):'wQ',(0,4):'bK',(0,4):'bQ',
                       (7,7):'wK',(7,0):'wQ',(0,7):'bK',(0,0):'bQ'}
        if piece == 'K': self.castling['wK'] = self.castling['wQ'] = False
        if piece == 'k': self.castling['bK'] = self.castling['bQ'] = False
        for sq_key, right in [((7,7),'wK'),((7,0),'wQ'),((0,7),'bK'),((0,0),'bQ')]:
            if (fr,fc) == sq_key or (tr,tc) == sq_key:
                self.castling[right] = False

        if self.turn == 'b':
            self.fullmove_number += 1
        self.turn = self.opponent()
        self.history.append(move)

    def undo_move(self):
        """Restore the board to its state before the last move."""
        if not self.history:
            return
        move = self.history.pop()
        self.turn = self.opponent()      # switch back

        fr, fc = move.from_sq
        tr, tc = move.to_sq

        # The piece that moved (undo promotion → restore pawn)
        if move.promotion:
            piece = 'P' if self.turn == 'w' else 'p'
        else:
            piece = self.squares[tr][tc]

        self.squares[fr][fc] = piece

        # Restore captured square
        self.squares[tr][tc] = '.' if move.was_en_passant else move.captured

        # Restore en-passant captured pawn
        if move.was_en_passant:
            self.squares[fr][tc] = 'p' if self.turn == 'w' else 'P'

        # Restore castled rook
        if move.was_castling:
            rf, rfc = move.castling_rook_from
            rt, rtc = move.castling_rook_to
            self.squares[rf][rfc] = self.squares[rt][rtc]
            self.squares[rt][rtc] = '.'

        # Restore saved state
        self.en_passant      = move.prev_en_passant
        self.castling        = move.prev_castling
        self.halfmove_clock  = move.prev_halfmove
        if self.turn == 'b':
            self.fullmove_number -= 1

    # ── Display ──────────────────────────────────────────────────────────────

    def display(self, perspective: str = 'w'):
        """Pretty-print the board using Unicode chess symbols."""
        SYMBOLS = {
            'P':'♙','N':'♘','B':'♗','R':'♖','Q':'♕','K':'♔',
            'p':'♟','n':'♞','b':'♝','r':'♜','q':'♛','k':'♚',
            '.':'·',
        }
        print()
        row_range = range(8)       if perspective == 'w' else range(7,-1,-1)
        col_range = range(8)       if perspective == 'w' else range(7,-1,-1)
        ranks = '87654321'
        for row in row_range:
            line = f"  {ranks[row]} "
            for col in col_range:
                line += SYMBOLS.get(self.squares[row][col], '?') + ' '
            print(line)
        files_label = '    a b c d e f g h' if perspective == 'w' \
                      else '    h g f e d c b a'
        print(files_label)
        turn_str = 'White' if self.turn == 'w' else 'Black'
        print(f"\n     {turn_str} to move\n")
