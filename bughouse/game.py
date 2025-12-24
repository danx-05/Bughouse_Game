from typing import Dict, Optional, List, Any
from bughouse.chess_board import ChessBoard
from bughouse.color import Color
from bughouse.coordinate import Coordinate
from bughouse.player import Player
from bughouse.pieces_reserve import PiecesReserve
from bughouse.figures import Piece, Pawn, Knight, Bishop, Rook, Queen, King


class PromotionRequired(Exception):
    """Специальная ошибка: требуется выбор фигуры для превращения пешки."""

    def __init__(self, victim_player_id: int, options: List[Dict[str, Any]]):
        super().__init__("promotion_required")
        self.victim_player_id = victim_player_id
        self.options = options


class Game:
    def __init__(self):
        self.board_a = ChessBoard()
        self.board_b = ChessBoard()
        self.players: Dict[int, Player] = {}
        
        fen1 = "r4rk1/p1pq1p1p/BN1b1B1n/1p1pp1p1/PP1P3P/1nNbP3/2P2PP1/RQ2K2R b KQ - 1 15"
        fen2 = "rnbqkbnr/pp1p3p/2p5/3PppB1/2P1P3/6p1/PP3PPP/RN1QKBNR w KQkq - 1 9"
        fen3 = "3b2bk/5ppp/1b6/3n4/4n3/8/5PPP/R6K w - - 0 1"
        fen4 = "3qb3/pppp4/1p2k3/8/PP2K2R/2PPPPPP/3Q4/8 w HAha - 0 1"
        fen5 = "3r3k/5ppp/1q6/8/7B/7n/6PP/5R1K w - - 0 1"

        # self.board_a.init_from_fen(fen5)
        # self.board_b.init_from_fen(fen5)
        self.board_a.init_standard_position()
        self.board_b.init_standard_position()
        
        # Регистрируем роли игроков
        self.players[1] = Player(1, self.board_a, Color.WHITE, "A")
        self.players[4] = Player(4, self.board_a, Color.BLACK, "A")
        self.players[2] = Player(2, self.board_b, Color.WHITE, "B")
        self.players[3] = Player(3, self.board_b, Color.BLACK, "B")

        self._initialize_starting_reserves()

    
    def _initialize_starting_reserves(self):
        STANDARD_STARTING_RESERVE = {
            Pawn: 0,
            Knight: 0,
            Bishop: 0,
            Rook: 0,
            Queen: 0
        }
        
        reserve_config = STANDARD_STARTING_RESERVE
        
        
        for player_id, player in self.players.items():            
            for piece_class, count in reserve_config.items():
                for _ in range(count):
                    player.pieces_reserve.add(piece_class)


    def get_player(self, player_id: int) -> Player:
        """Получает игрока по ID"""
        player = self.players.get(player_id)
        if player is None:
            raise ValueError(f"Нет игрока {player_id}")
        return player
    
    def _parse_piece_symbol(self, symbol: str) -> type[Piece]:
        """Парсит символ фигуры и возвращает класс"""
        symbol_map = {
            "P": Pawn,
            "N": Knight,
            "B": Bishop,
            "R": Rook,
            "Q": Queen,
            "K": King
        }
        piece_class = symbol_map.get(symbol.upper())
        if piece_class is None:
            raise ValueError(f"Неизвестная фигура: {symbol} (используй: P, N, B, R, Q, K)")
        return piece_class
    
    def _get_opponent_teammate_id(self, player_id: int) -> int:
        player = self.get_player(player_id)
        partner_id = player.get_partner_id()
        partner = self.get_player(partner_id)
        return int(partner.get_opponent_player_id())

    def _list_stealable_pieces(self, victim_player_id: int) -> List[Dict[str, Any]]:
        victim = self.get_player(victim_player_id)
        board = victim.board

        def removal_exposes_check(victim_coord: Coordinate) -> bool:
            """Проверяет, откроется ли шах королю жертвы, если убрать фигуру с клетки."""
            original = board.get_piece(victim_coord)
            if original is None:
                return False
            board.squares[victim_coord.get_file_index()][victim_coord.get_rank_index()] = None
            try:
                return board.is_king_in_check(victim.color)
            finally:
                board.squares[victim_coord.get_file_index()][victim_coord.get_rank_index()] = original

        options: List[Dict[str, Any]] = []
        for file in range(8):
            for rank_idx in range(8):
                piece = board.squares[file][rank_idx]
                if piece is None:
                    continue
                if piece.color != victim.color:
                    continue
                if isinstance(piece, (King, Pawn)):
                    continue


                victim_coord = piece.coordinate
                exposes_check = removal_exposes_check(victim_coord)
                if exposes_check and board.get_current_player() != victim.color:
                    continue

                options.append({
                    "square": str(piece.coordinate),
                    "piece": board._piece_symbol(piece),
                    "pieceName": piece.__class__.__name__,
                    "opensCheck": exposes_check,
                })
        options.sort(key=lambda x: (x["piece"], x["square"]))
        return options

    def _create_promoted_piece(self, piece_symbol: str, coord: Coordinate, color: Color) -> Piece:
        """Создаёт фигуру для превращения (в цвет превращающегося), с корректными флагами."""
        piece_class = self._parse_piece_symbol(piece_symbol)
        if piece_class in (King, Pawn):
            raise ValueError("Нельзя превращаться в короля или пешку")
        if piece_class == Rook:
            return Rook(coord, color, True)
        return piece_class(coord, color)

    def make_move(
        self,
        player_id: int,
        from_square: str,
        to_square: str,
        victim_player_id: Optional[int] = None,
        victim_square: Optional[str] = None,
    ):
        """Выполняет ход фигурой"""
        game_over = self.check_game_over()
        if game_over:
            raise ValueError(f"Игра завершена: {game_over.get('reason', 'Мат на одной из досок')}. Ходы больше невозможны.")
        
        player = self.get_player(player_id)
        board = player.board
        
        if board.get_current_player() != player.color:
            raise ValueError(f"Сейчас ход игрока {player.get_opponent_player_id()}")
        
        from_coord = Coordinate.from_notation(from_square)
        to_coord = Coordinate.from_notation(to_square)

        # Превращение пешки
        moving_piece = board.get_piece(from_coord)
        is_pawn_promotion = False
        if isinstance(moving_piece, Pawn):
            if (player.color == Color.WHITE and to_coord.rank == 8) or (player.color == Color.BLACK and to_coord.rank == 1):
                is_pawn_promotion = True

        if is_pawn_promotion and (victim_player_id is None or victim_square is None):
            test_board = ChessBoard.from_fen(board.to_fen())
            _ = test_board.move(from_coord, to_coord)

            # Возвращаем список фигур для выбора
            expected_victim_id = self._get_opponent_teammate_id(player_id)
            options = self._list_stealable_pieces(expected_victim_id)
            if not options:
                raise ValueError("Нельзя провести пешку: у оппонента сокомандника нет доступных фигур для обмена")
            raise PromotionRequired(expected_victim_id, options)
        
        captured = board.move(from_coord, to_coord)
        
        if captured is not None:
            partner_id = player.get_partner_id()
            partner = self.players[partner_id]
            partner.pieces_reserve.add(captured.__class__)

        if is_pawn_promotion:
            expected_victim_id = self._get_opponent_teammate_id(player_id)
            if victim_player_id != expected_victim_id:
                raise ValueError("Неверный игрок-жертва для превращения")
            if victim_square is None:
                raise ValueError("Не выбрана фигура для превращения")

            victim = self.get_player(expected_victim_id)
            victim_coord = Coordinate.from_notation(victim_square)
            victim_piece = victim.board.get_piece(victim_coord)
            if victim_piece is None:
                raise ValueError("Выбранная фигура отсутствует")
            if victim_piece.color != victim.color:
                raise ValueError("Нельзя забрать чужую фигуру с этой доски")
            if isinstance(victim_piece, (King, Pawn)):
                raise ValueError("Нельзя забрать короля или пешку")


            original = victim.board.get_piece(victim_coord)
            victim.board.squares[victim_coord.get_file_index()][victim_coord.get_rank_index()] = None
            try:
                exposes_check = victim.board.is_king_in_check(victim.color)
            finally:
                victim.board.squares[victim_coord.get_file_index()][victim_coord.get_rank_index()] = original

            if exposes_check and victim.board.get_current_player() != victim.color:
                raise ValueError("Нельзя забрать эту фигуру: после снятия откроется шах, а сейчас ход не жертвы")

            victim.board.squares[victim_coord.get_file_index()][victim_coord.get_rank_index()] = None

            victim.pieces_reserve.add(Pawn)

            new_piece = self._create_promoted_piece(
                piece_symbol=victim.board._piece_symbol(victim_piece),
                coord=to_coord,
                color=player.color,
            )
            board.squares[to_coord.get_file_index()][to_coord.get_rank_index()] = new_piece
    
    def make_drop(self, player_id: int, piece_symbol: str, square: str):
        """Выполняет дроп фигуры"""
        game_over = self.check_game_over()
        if game_over:
            raise ValueError(f"Игра завершена: {game_over.get('reason', 'Мат на одной из досок')}. Дропы больше невозможны.")
        
        player = self.get_player(player_id)
        board = player.board
        
        if board.get_current_player() != player.color:
            raise ValueError(f"Сейчас ход игрока {player.get_opponent_player_id()}")
        
        piece_class = self._parse_piece_symbol(piece_symbol)
        
        if player.pieces_reserve.get_count(piece_class) <= 0:
            piece_name = piece_class.__name__
            raise ValueError(f"У игрока {player_id} нет фигуры {piece_name}")
        
        coord = Coordinate.from_notation(square)
        
        if not board.is_empty(coord):
            raise ValueError(f"Клетка {coord} занята")
        
        if piece_class == Pawn:
            rank = coord.rank
            if rank == 1 or rank == 8:
                raise ValueError("Нельзя ставить пешку на ранг 1 или 8")
        

        from bughouse.figures import Rook, King
        if piece_class == Rook or piece_class == King:
            temp_piece = piece_class(coord, player.color, has_moved=True)
        else:
            temp_piece = piece_class(coord, player.color)
        board.place_piece(temp_piece)
        
        opponent_color = player.color.opponent()
        opponent_player_id_str = player.get_opponent_player_id()
        opponent_player_id = int(opponent_player_id_str)
        opponent = self.players[opponent_player_id]
        
        # Проверяем, создает ли дроп мат для противника
        creates_checkmate = board.is_checkmate(opponent_color, opponent.pieces_reserve)
        
        if creates_checkmate:
            # Откатываем
            board.squares[coord.get_file_index()][coord.get_rank_index()] = None
            raise ValueError(f"Нельзя поставить фигуру: дроп создает мат для противника")
        
        # Если мата нет, продолжаем
        board.current_player = board.current_player.opponent()
        player.pieces_reserve.remove(piece_class)
    
    def check_game_over(self) -> Optional[Dict]:
        """Проверяет, завершена ли игра (мат). Возвращает информацию о победителе или None"""
        from bughouse.pieces_reserve import PiecesReserve
        # Команда 1
        checkmate_1_white = self.board_a.is_checkmate(Color.WHITE, self.players[1].pieces_reserve)
        checkmate_1_black = self.board_b.is_checkmate(Color.BLACK, self.players[3].pieces_reserve)
        team1_lost = checkmate_1_white or checkmate_1_black
        
        # Команда 2
        checkmate_2_white = self.board_b.is_checkmate(Color.WHITE, self.players[2].pieces_reserve)
        checkmate_2_black = self.board_a.is_checkmate(Color.BLACK, self.players[4].pieces_reserve)
        team2_lost = checkmate_2_white or checkmate_2_black
        
        if team1_lost and not team2_lost:
            return {
                "winner": "team2",
                "team": [2, 4],
                "reason": "Мат команде 1"
            }
        elif team2_lost and not team1_lost:
            return {
                "winner": "team1",
                "team": [1, 3],
                "reason": "Мат команде 2"
            }
        return None
    
    def to_fen_dict(self) -> Dict:
        """Сохраняет текущую позицию в формате, включающем FEN обеих досок и запасы"""
        reserves = {}
        for player_id in [1, 2, 3, 4]:
            player = self.players[player_id]
            reserves[str(player_id)] = {
                "P": player.pieces_reserve.get_count(Pawn),
                "N": player.pieces_reserve.get_count(Knight),
                "B": player.pieces_reserve.get_count(Bishop),
                "R": player.pieces_reserve.get_count(Rook),
                "Q": player.pieces_reserve.get_count(Queen)
            }
        
        return {
            "boardA": self.board_a.to_fen(),
            "boardB": self.board_b.to_fen(),
            "reserves": reserves
        }
    
    def from_fen_dict(self, fen_dict: Dict):
        """Загружает позицию из формата с FEN обеих досок и запасами"""
        if "boardA" in fen_dict:
            self.board_a = ChessBoard.from_fen(fen_dict["boardA"])
        if "boardB" in fen_dict:
            self.board_b = ChessBoard.from_fen(fen_dict["boardB"])
        
        self.players[1].board = self.board_a
        self.players[4].board = self.board_a
        self.players[2].board = self.board_b
        self.players[3].board = self.board_b
        
        if "reserves" in fen_dict:
            reserves = fen_dict["reserves"]
            for player_id_str, counts in reserves.items():
                player_id = int(player_id_str)
                player = self.players[player_id]
                player.pieces_reserve = PiecesReserve()
                for piece_symbol, count in counts.items():
                    piece_class = self._parse_piece_symbol(piece_symbol)
                    for _ in range(count):
                        player.pieces_reserve.add(piece_class)