from abc import ABC, abstractmethod
from typing import Set
from bughouse.coordinate import Coordinate
from bughouse.color import Color


class Piece(ABC):
    def __init__(self, coordinate: Coordinate, color: Color):
        self.coordinate = coordinate
        self.color = color
    
    @abstractmethod
    def move_to(self, new_coordinate: Coordinate) -> 'Piece':
        """Возвращает КОПИЮ фигуры с новой координатой (immutable-style)"""
        pass
    
    @abstractmethod
    def get_possible_moves(self, board: 'ChessBoard') -> Set[Coordinate]:
        """Возвращает множество возможных ходов"""
        pass
    
    def __eq__(self, other):
        if not isinstance(other, Piece):
            return False
        return self.coordinate == other.coordinate and self.color == other.color
    
    def __hash__(self):
        return hash((self.coordinate, self.color))
