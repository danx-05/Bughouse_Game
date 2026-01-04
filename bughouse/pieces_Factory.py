from typing import Optional
from bughouse.color import Color
from bughouse.coordinate import Coordinate
from bughouse.figures import *
from bughouse.figures.piece import Piece


class PieceFactory:
    piece_map = {
        'P': Pawn,
        'N': Knight,
        'B': Bishop,
        'R': Rook,
        'Q': Queen,
        'K': King
    }
    @staticmethod
    def create_from_fen_symbol(symbol: str, coord: Coordinate) -> Optional[Piece]:
        is_white = symbol.isupper()
        color = Color.WHITE if is_white else Color.BLACK
        symbol_upper = symbol.upper()

        piece_class = PieceFactory.piece_map.get(symbol_upper)
        if not piece_class:
            return None

        if piece_class == Rook:
            return Rook(coord, color, has_moved=False)
        elif piece_class == King:
            return King(coord, color, has_moved=False)
        else:
            return piece_class(coord, color)
    @staticmethod
    def create_piece(symbol: str, coord: Coordinate, color: Color) -> Piece:
        symbol_upper = symbol.upper()
        print(symbol)
        piece_class = PieceFactory.piece_map.get(symbol_upper)
        
        if piece_class == Rook:
            return Rook(coord, color, has_moved=False)
        elif piece_class == King:
            return King(coord, color, has_moved=False)
        else:
            return piece_class(coord, color)