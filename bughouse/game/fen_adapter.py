from typing import TYPE_CHECKING, Dict
from bughouse.game.chess_board import ChessBoard
from bughouse.figures import Pawn, Knight, Bishop, Rook, Queen
if TYPE_CHECKING:
    from bughouse.game.game import Game
class FenGameAdapter:
    @staticmethod
    def to_fen_dict(game: 'Game') -> Dict:
        """Преобразует игру в словарь с FEN-представлением"""
        reserves = {}
        for player_id in [1, 2, 3, 4]:
            player = game.players[player_id]
            reserves[str(player_id)] = {
                "P": player.pieces_reserve.get_count(Pawn),
                "N": player.pieces_reserve.get_count(Knight),
                "B": player.pieces_reserve.get_count(Bishop),
                "R": player.pieces_reserve.get_count(Rook),
                "Q": player.pieces_reserve.get_count(Queen)
            }
        
        return {
            "boardA": game.board_a.to_fen(),
            "boardB": game.board_b.to_fen(),
            "reserves": reserves
        }

    @staticmethod
    def from_fen_dict(game: 'Game', fen_dict: Dict):
        """Загружает игру из FEN-словаря"""
        if "boardA" in fen_dict:
            game.board_a = ChessBoard.from_fen(fen_dict["boardA"])
        if "boardB" in fen_dict:
            game.board_b = ChessBoard.from_fen(fen_dict["boardB"])
        
        game.players[1].board = game.board_a
        game.players[4].board = game.board_a
        game.players[2].board = game.board_b
        game.players[3].board = game.board_b
        
        if "reserves" in fen_dict:
            from .pieces_reserve import PiecesReserve
            reserves = fen_dict["reserves"]
            for player_id_str, counts in reserves.items():
                player_id = int(player_id_str)
                player = game.players[player_id]
                player.pieces_reserve = PiecesReserve()
                for piece_symbol, count in counts.items():
                    piece_class = game._parse_piece_symbol(piece_symbol)
                    for _ in range(count):
                        player.pieces_reserve.add(piece_class)