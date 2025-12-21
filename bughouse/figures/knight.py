from typing import Set, TYPE_CHECKING
from bughouse.coordinate import Coordinate
from bughouse.color import Color
from bughouse.figures.piece import Piece

if TYPE_CHECKING:
    from bughouse.chess_board import ChessBoard


class Knight(Piece):
    def move_to(self, new_coordinate: Coordinate) -> 'Knight':
        return Knight(new_coordinate, self.color)
    
    def get_possible_moves(self, board: 'ChessBoard') -> Set[Coordinate]:
        moves = set()
        
        dx = [-1, -1, 1, 1, 2, 2, -2, -2]
        dy = [-2, 2, -2, 2, -1, 1, -1, 1]
        
        for i in range(8):
            target = Coordinate.try_shift(self.coordinate, dx[i], dy[i])
            if target is not None:
                dest_piece = board.get_piece(target)
                if dest_piece is None or dest_piece.color != self.color:
                    moves.add(target)
        
        return moves

