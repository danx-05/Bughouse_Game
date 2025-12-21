from typing import Set, TYPE_CHECKING
from bughouse.coordinate import Coordinate
from bughouse.color import Color
from bughouse.figures.piece import Piece

if TYPE_CHECKING:
    from bughouse.chess_board import ChessBoard


class Bishop(Piece):
    def move_to(self, new_coordinate: Coordinate) -> 'Bishop':
        return Bishop(new_coordinate, self.color)
    
    def get_possible_moves(self, board: 'ChessBoard') -> Set[Coordinate]:
        moves = set()
        
        directions = [-1, 1]
        
        for file_dir in directions:
            for rank_dir in directions:
                for step in range(1, 8):
                    target = Coordinate.try_shift(
                        self.coordinate,
                        file_dir * step,
                        rank_dir * step
                    )
                    
                    if target is None:
                        break
                    
                    piece_at_target = board.get_piece(target)
                    
                    if piece_at_target is None:
                        moves.add(target)
                    else:
                        if piece_at_target.color != self.color:
                            if piece_at_target.color != self.color:
                                moves.add(target)
                        break
        
        return moves

