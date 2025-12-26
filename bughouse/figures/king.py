from typing import Set, TYPE_CHECKING
from bughouse.coordinate import Coordinate
from bughouse.color import Color
from bughouse.file import File
from bughouse.figures.piece import Piece

if TYPE_CHECKING:
    from bughouse.chess_board import ChessBoard


class King(Piece):
    def __init__(self, coordinate: Coordinate, color: Color, has_moved: bool = False):
        super().__init__(coordinate, color)
        self.has_moved = has_moved
    
    def move_to(self, new_coordinate: Coordinate) -> 'King':
        return King(new_coordinate, self.color, True)
    
    def get_possible_moves(self, board: 'ChessBoard') -> Set[Coordinate]:
        moves = set()
        
        opponent_color = self.color.opponent()
        enemy_king_pos = board.find_king(opponent_color)
        
        directions = [-1, 0, 1]
        for file_dir in directions:
            for rank_dir in directions:
                if file_dir == 0 and rank_dir == 0:
                    continue
                
                target = Coordinate.try_shift(self.coordinate, file_dir, rank_dir)
                if target is None:
                    continue
                
                piece_at_target = board.get_piece(target)
                
                if piece_at_target is None or piece_at_target.color != self.color:
                    if piece_at_target is None or not isinstance(piece_at_target, King):

                        if enemy_king_pos is not None:
                            file_diff = abs(target.get_file_index() - enemy_king_pos.get_file_index())
                            rank_diff = abs(target.rank - enemy_king_pos.rank)
                            if file_diff <= 1 and rank_diff <= 1:
                                continue
                        
                        moves.add(target)

        if not self.has_moved:
            if self._can_castle_kingside(board):
                target = Coordinate(File.G, self.coordinate.rank)
                moves.add(target)
            if self._can_castle_queenside(board):
                target = Coordinate(File.C, self.coordinate.rank)
                moves.add(target)

        return moves
    
    def _can_castle_kingside(self, board: 'ChessBoard') -> bool:
        if self.coordinate.rank != 1 and self.coordinate.rank != 8:
            return False
        if self.coordinate.file != File.E:
            return False
        
        f1 = Coordinate(File.F, self.coordinate.rank)
        g1 = Coordinate(File.G, self.coordinate.rank)
        h1 = Coordinate(File.H, self.coordinate.rank)
        
        if not board.is_empty(f1) or not board.is_empty(g1):
            return False
        
        from bughouse.figures.rook import Rook
        rook = board.get_piece(h1)
        if not isinstance(rook, Rook) or rook.color != self.color:
            return False
        
        if rook.has_moved:
            return False
        
        if board.is_square_attacked(self.coordinate, self.color.opponent()):
            return False
        if board.is_square_attacked(f1, self.color.opponent()):
            return False
        if board.is_square_attacked(g1, self.color.opponent()):
            return False
        return True

    def _can_castle_queenside(self, board: 'ChessBoard') -> bool:
        if self.coordinate.rank != 1 and self.coordinate.rank != 8:
            return False
        if self.coordinate.file != File.E:
            return False

        d1 = Coordinate(File.D, self.coordinate.rank)
        c1 = Coordinate(File.C, self.coordinate.rank)
        b1 = Coordinate(File.B, self.coordinate.rank)
        a1 = Coordinate(File.A, self.coordinate.rank)

        if not board.is_empty(d1) or not board.is_empty(c1) or not board.is_empty(b1):
            return False

        from bughouse.figures.rook import Rook
        rook = board.get_piece(a1)
        if not isinstance(rook, Rook) or rook.color != self.color:
            return False
        if rook.has_moved:
            return False

        if board.is_square_attacked(self.coordinate, self.color.opponent()):
            return False
        if board.is_square_attacked(d1, self.color.opponent()):
            return False
        if board.is_square_attacked(c1, self.color.opponent()):
            return False
        return True


