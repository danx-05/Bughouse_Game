from typing import Dict, Type
from bughouse.figures import Piece, Pawn, Knight, Bishop, Rook, Queen, King


class PiecesReserve:
    def __init__(self):
        self.counts: Dict[Type[Piece], int] = {}
    
    def add(self, piece_class: Type[Piece]):
        """Добавляет фигуру в запас"""
        self.counts[piece_class] = self.counts.get(piece_class, 0) + 1
    
    def remove(self, piece_class: Type[Piece]) -> bool:
        """Удаляет фигуру из запаса. Возвращает True, если удаление успешно"""
        current = self.counts.get(piece_class, 0)
        if current <= 0:
            return False
        self.counts[piece_class] = current - 1
        return True
    
    def get_count(self, piece_class: Type[Piece]) -> int:
        """Возвращает количество фигур указанного типа в запасе"""
        return self.counts.get(piece_class, 0)
    
    def is_empty(self) -> bool:
        """Проверяет, пуст ли запас"""
        return all(count <= 0 for count in self.counts.values())
    
    def _symbol_for(self, clazz: Type[Piece]) -> str:
        name = clazz.__name__
        symbol_map = {
            'Pawn': 'P',
            'Knight': 'N',
            'Bishop': 'B',
            'Rook': 'R',
            'Queen': 'Q',
            'King': 'K'
        }
        return symbol_map.get(name, '?')
    
    def to_readable_string(self) -> str:
        parts = []
        for piece_class, count in self.counts.items():
            if count > 0:
                name = piece_class.__name__
                parts.append(f"{name}: {count}")
        return ", ".join(parts) if parts else "<пусто>"
    
    def __str__(self) -> str:
        parts = []
        for piece_class, count in self.counts.items():
            if count > 0:
                sym = self._symbol_for(piece_class)
                parts.append(f"{sym}×{count}")
        return " ".join(parts) if parts else ""

