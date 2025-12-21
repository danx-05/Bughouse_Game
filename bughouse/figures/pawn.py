from typing import Set, TYPE_CHECKING
from bughouse.coordinate import Coordinate
from bughouse.color import Color
from bughouse.file import File
from bughouse.figures.piece import Piece

if TYPE_CHECKING:
    from bughouse.chess_board import ChessBoard


class Pawn(Piece):
    def move_to(self, new_coordinate: Coordinate) -> 'Pawn':
        return Pawn(new_coordinate, self.color)
    
    def get_possible_moves(self, board: 'ChessBoard') -> Set[Coordinate]:
        moves = set()
        direction = 1 if self.color == Color.WHITE else -1
        start_rank = 2 if self.color == Color.WHITE else 7
        

        new_rank1 = self.coordinate.rank + direction
        if self._is_valid_rank(new_rank1):
            forward1 = Coordinate(self.coordinate.file, new_rank1)
            if board.is_empty(forward1):
                moves.add(forward1)
                
                if self.coordinate.rank == start_rank:
                    new_rank2 = self.coordinate.rank + 2 * direction
                    if self._is_valid_rank(new_rank2):
                        forward2 = Coordinate(self.coordinate.file, new_rank2)
                        if board.is_empty(forward2):
                            moves.add(forward2)
        

        left_file = self._file_to_left(self.coordinate.file)
        if left_file is not None:
            new_rank = self.coordinate.rank + direction
            if self._is_valid_rank(new_rank):
                left_capture = Coordinate(left_file, new_rank)
                target = board.get_piece(left_capture)
                if target is not None and target.color != self.color:
                    moves.add(left_capture)
                if target is None and getattr(board, "en_passant_target", None) == left_capture:
                    side = Coordinate(left_file, self.coordinate.rank)
                    side_piece = board.get_piece(side)
                    if isinstance(side_piece, Pawn) and side_piece.color != self.color:
                        moves.add(left_capture)
        
        right_file = self._file_to_right(self.coordinate.file)
        if right_file is not None:
            new_rank = self.coordinate.rank + direction
            if self._is_valid_rank(new_rank):
                right_capture = Coordinate(right_file, new_rank)
                target = board.get_piece(right_capture)
                if target is not None and target.color != self.color:
                    moves.add(right_capture)
                if target is None and getattr(board, "en_passant_target", None) == right_capture:
                    side = Coordinate(right_file, self.coordinate.rank)
                    side_piece = board.get_piece(side)
                    if isinstance(side_piece, Pawn) and side_piece.color != self.color:
                        moves.add(right_capture)
        
        return moves
    
    def _is_valid_rank(self, rank: int) -> bool:
        return 1 <= rank <= 8
    
    def _file_to_left(self, file: File) -> File | None:
        index = file.value
        return File(index - 1) if index > 0 else None
    
    def _file_to_right(self, file: File) -> File | None:
        index = file.value
        return File(index + 1) if index < 7 else None

