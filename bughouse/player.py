from bughouse.chess_board import ChessBoard
from bughouse.color import Color
from bughouse.pieces_reserve import PiecesReserve


class Player:
    def __init__(self, player_id: int, board: ChessBoard, color: Color, board_name: str):
        self.player_id = player_id
        self.board = board
        self.color = color
        self.board_name = board_name
        self.pieces_reserve = PiecesReserve()
    
    def get_opponent_player_id(self) -> str:
        """Для сообщений: если я 1 → противник 4, если 2 → 3 и т.д."""
        opponent_map = {
            1: "4",
            4: "1",
            2: "3",
            3: "2"
        }
        return opponent_map.get(self.player_id, "?")
    
    def get_partner_id(self) -> int:
        """Возвращает ID партнера по команде"""
        partner_map = {
            1: 3,
            3: 1,
            2: 4,
            4: 2
        }
        partner = partner_map.get(self.player_id)
        if partner is None:
            raise ValueError(f"Неизвестный игрок: {self.player_id}")
        return partner

