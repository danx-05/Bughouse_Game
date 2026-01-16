from typing import Set, TYPE_CHECKING
from bughouse.game.coordinate import Coordinate
from bughouse.game.color import Color
from bughouse.figures.piece import Piece

if TYPE_CHECKING:
    from bughouse.game.chess_board import ChessBoard


class Rook(Piece):
    def __init__(self, coordinate: Coordinate, color: Color, has_moved: bool = False):
        super().__init__(coordinate, color)
        self.has_moved = has_moved  # Для рокировки
    
    def move_to(self, new_coordinate: Coordinate) -> 'Rook':
        return Rook(new_coordinate, self.color, True)
    
    def get_possible_moves(self, board: 'ChessBoard') -> Set[Coordinate]:
        moves = set()
        
        horizontal_dirs = [-1, 1]
        for file_dir in horizontal_dirs:
            for step in range(1, 8):
                target = Coordinate.try_shift(
                    self.coordinate,
                    file_dir * step,
                    0
                )
                
                if target is None:
                    break
                
                piece_at_target = board.get_piece(target)
                
                if piece_at_target is None:
                    moves.add(target)
                else:
                    if piece_at_target.color != self.color:
                        moves.add(target)
                    break
        
        vertical_dirs = [-1, 1]
        for rank_dir in vertical_dirs:
            for step in range(1, 8):
                target = Coordinate.try_shift(
                    self.coordinate,
                    0,  # file не меняется
                    rank_dir * step
                )
                
                if target is None:
                    break
                
                piece_at_target = board.get_piece(target)
                
                if piece_at_target is None:
                    moves.add(target)
                else:
                    if piece_at_target.color != self.color:
                        moves.add(target)
                    break
        
        return moves

