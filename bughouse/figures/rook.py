from typing import Set, TYPE_CHECKING
from bughouse.coordinate import Coordinate
from bughouse.color import Color
from bughouse.figures.piece import Piece

if TYPE_CHECKING:
    from bughouse.chess_board import ChessBoard


class Rook(Piece):
    def __init__(self, coordinate: Coordinate, color: Color, has_moved: bool = False):
        super().__init__(coordinate, color)
        self.has_moved = has_moved  # Для рокировки
    
    def move_to(self, new_coordinate: Coordinate) -> 'Rook':
        return Rook(new_coordinate, self.color, True)
    
    def get_possible_moves(self, board: 'ChessBoard') -> Set[Coordinate]:
        moves = set()
        
        # Ладья ходит по горизонтали и вертикали в 4 направлениях
        # Направления: влево, вправо, вверх, вниз
        
        # Горизонтальные направления (влево и вправо)
        horizontal_dirs = [-1, 1]
        for file_dir in horizontal_dirs:
            for step in range(1, 8):
                target = Coordinate.try_shift(
                    self.coordinate,
                    file_dir * step,
                    0  # rank не меняется
                )
                
                if target is None:
                    # Вышли за пределы доски
                    break
                
                piece_at_target = board.get_piece(target)
                
                if piece_at_target is None:
                    # Клетка пустая - можем сюда пойти
                    moves.add(target)
                else:
                    # Клетка занята
                    if piece_at_target.color != self.color:
                        moves.add(target)
                    # Своя фигура или король противника - не можем сюда пойти и дальше не идем
                    break
        
        # Вертикальные направления (вверх и вниз)
        vertical_dirs = [-1, 1]
        for rank_dir in vertical_dirs:
            for step in range(1, 8):
                target = Coordinate.try_shift(
                    self.coordinate,
                    0,  # file не меняется
                    rank_dir * step
                )
                
                if target is None:
                    # Вышли за пределы доски
                    break
                
                piece_at_target = board.get_piece(target)
                
                if piece_at_target is None:
                    # Клетка пустая - можем сюда пойти
                    moves.add(target)
                else:
                    # Клетка занята
                    if piece_at_target.color != self.color:
                        moves.add(target)
                    break
        
        # Фильтруем ходы, которые приводят к шаху короля
        return moves

