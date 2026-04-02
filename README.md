# ♟ Chess Engine — Python from Scratch

A fully playable chess engine written in pure Python, built to teach the core
concepts of chess programming step by step.

No dependencies — just Python 3.7+.

---

## Quick Start

```bash
git clone https://github.com/emilioarango/chess-engine.git
cd chess-engine

python main.py              # Play as White
python main.py --black      # Play as Black
python main.py --auto       # Watch engine vs engine
python main.py --depth 4    # Stronger (but slower) engine
```

### Controls

| Input | Action |
|-------|--------|
| `e2e4` | Move from e2 to e4 |
| `e7e8q` | Promote pawn to queen |
| `undo` | Take back your last move |
| `resign` | Resign the game |
| `fen` | Print current FEN string |
| `quit` | Exit |

---

## Project Structure

```
chess-engine/
├── board.py      ← Board state, FEN, make/undo move
├── moves.py      ← Legal move generation for all pieces
├── evaluate.py   ← Position scoring (material + piece-square tables)
├── search.py     ← Minimax with Alpha-Beta pruning
└── main.py       ← Terminal game loop
```

---

## How It Works — Concept by Concept

### 1. Board Representation (`board.py`)

The board is a simple 8×8 Python list.

```
Row 0  ←  rank 8  (black's starting side)
Row 7  ←  rank 1  (white's starting side)
Col 0  ←  file a
Col 7  ←  file h
```

Pieces are single characters:
- **Uppercase** = White: `P N B R Q K`
- **Lowercase** = Black: `p n b r q k`
- **Dot** = empty square: `.`

Positions can be loaded/saved as **FEN strings** — the standard notation used by all chess software:

```
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
```

The `Board` class also stores:
- **Whose turn** it is (`'w'` or `'b'`)
- **Castling rights** (which sides still have the right to castle)
- **En-passant target square** (if the last move was a double pawn push)
- **Move history** — a stack of moves with enough info to undo each one

### 2. Move Generation (`moves.py`)

Move generation is split into two phases:

**Phase 1 — Pseudo-legal moves**  
Generate every move a piece can physically make, *without* checking
whether it leaves the king in check.

Each piece type has its own generator:
- **Pawns**: forward push, double push from starting rank, diagonal captures, en passant, promotions
- **Knights**: 8 fixed L-shaped jumps
- **Bishops / Rooks / Queens**: ray casting — slide in a direction until blocked or off the board
- **King**: one square in any direction, plus castling

**Phase 2 — Filter illegal moves**  
Make each pseudo-legal move, check if the king is now under attack, and discard the move if it is.

**Attack detection** uses `is_attacked()` — a direct function that checks pawn patterns, knight jumps,
sliding rays, and king adjacency without any recursion.

### 3. Evaluation (`evaluate.py`)

The engine scores each position with two components:

**Material**  
Count up piece values for both sides (in centipawns, where 100 = 1 pawn):

| Piece | Value |
|-------|-------|
| Pawn | 100 |
| Knight | 320 |
| Bishop | 330 |
| Rook | 500 |
| Queen | 900 |

**Piece-square tables**  
Add a small bonus or penalty based on *where* each piece stands.
For example, a knight in the centre gets +20, a knight in a corner gets -50.
Tables are applied from White's perspective; for Black, the table is mirrored.

A positive total score favours White; negative favours Black.

### 4. Search (`search.py`)

**Minimax** — the engine imagines the game tree of all possible move sequences,
and picks the move that leads to the best position, assuming the opponent also
plays perfectly.

```
White maximises score
  └── Black minimises score
        └── White maximises score
              └── ... (repeat until depth limit)
```

At the bottom of the tree, evaluate() scores the position.

**Alpha-Beta pruning** — if we've already found a move that's better than
anything the opponent will allow, we can skip searching the rest of the
current branch. This reduces the search space dramatically (from O(b^d) to
roughly O(b^(d/2))), letting us search twice as deep for the same time cost.

**Move ordering** — Alpha-Beta works best when good moves are tried first.
The engine uses MVV-LVA (Most Valuable Victim – Least Valuable Attacker) to
prioritise captures where we take a valuable piece with a cheap one.

### Playing Strength

| Depth | Approximate ELO | Typical think time |
|-------|-----------------|-------------------|
| 2 | ~600 | < 0.1 s |
| 3 | ~900 | 0.1 – 0.5 s |
| 4 | ~1100 | 1 – 5 s |
| 5 | ~1300 | 10 – 60 s |

---

## Ideas for Extending the Engine

The engine as written is a solid foundation. Here are natural next steps,
roughly in order of difficulty:

- [ ] **Quiescence search** — at depth 0, keep searching captures to avoid
      the "horizon effect" (stopping mid-exchange).
- [ ] **Iterative deepening** — search depth 1, then 2, then 3, etc. in the
      same time budget. Lets you use the shallowest result as a fallback.
- [ ] **Transposition table** — cache evaluation results for positions we've
      already seen (identified by a Zobrist hash).
- [ ] **Opening book** — look up the first ~10 moves in a database instead of
      calculating them from scratch.
- [ ] **UCI protocol** — speak the Universal Chess Interface so the engine can
      connect to GUIs like Arena, Lichess, or Chess.com.
- [ ] **Endgame tablebases** — perfect play for positions with 5 or fewer pieces.
- [ ] **NNUE evaluation** — replace the hand-crafted evaluation with a small
      neural network (the technique used in Stockfish).

---

## Resources

- [Chess Programming Wiki](https://www.chessprogramming.org/) — encyclopaedic reference
- [Sebastian Lague's Chess video series](https://www.youtube.com/watch?v=U4ogK0MIzqk) — great visual walkthrough
- [python-chess](https://python-chess.readthedocs.io/) — production-grade Python chess library (good to compare against)
