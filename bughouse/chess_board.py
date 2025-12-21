from typing import List, Set, Optional, TYPE_CHECKING
from bughouse.coordinate import Coordinate
from bughouse.color import Color
from bughouse.file import File
from bughouse.figures import Piece, Pawn, Knight, Bishop, Rook, Queen, King

if TYPE_CHECKING:
    from bughouse.pieces_reserve import PiecesReserve


class ChessBoard:
    def __init__(self):
        self.squares: list[list[Optional[Piece]]] = [[None] * 8 for _ in range(8)]
        self.current_player = Color.WHITE
        self.en_passant_target: Optional[Coordinate] = None
    
    def init_standard_position(self):
        self.init_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    
    def init_from_fen(self, fen: str):
        """Инициализирует доску из FEN строки"""
        self._clear()
        self.en_passant_target = None
        parts = fen.split()
        if len(parts) < 1:
            return
            
        board_part = parts[0]
        rows = board_part.split('/')
        for rank_idx, row in enumerate(rows):
            rank = 8 - rank_idx
            file_idx = 0
            
            for char in row:
                if char.isdigit():
                    file_idx += int(char)
                else:
                    file = File(file_idx)
                    color = Color.WHITE if char.isupper() else Color.BLACK
                    
                    piece_char = char.upper()
                    if piece_char == 'P':
                        piece = Pawn(Coordinate(file, rank), color)
                    elif piece_char == 'N':
                        piece = Knight(Coordinate(file, rank), color)
                    elif piece_char == 'B':
                        piece = Bishop(Coordinate(file, rank), color)
                    elif piece_char == 'R':
                        piece = Rook(Coordinate(file, rank), color)
                    elif piece_char == 'Q':
                        piece = Queen(Coordinate(file, rank), color)
                    elif piece_char == 'K':
                        piece = King(Coordinate(file, rank), color)

                    
                    self.place_piece(piece)
                    file_idx += 1

    def _clear(self):
        for f in range(8):
            for r in range(8):
                self.squares[f][r] = None
        self.en_passant_target = None
    
    def place_piece(self, piece: Piece):
        self.squares[piece.coordinate.get_file_index()][piece.coordinate.get_rank_index()] = piece
    
    def get_piece(self, coord: Coordinate) -> Optional[Piece]:
        return self.squares[coord.get_file_index()][coord.get_rank_index()]
    
    def is_empty(self, coord: Coordinate) -> bool:
        return self.get_piece(coord) is None
    
    def get_current_player(self) -> Color:
        return self.current_player

    def is_square_attacked(self, square: Coordinate, attacker_color: Color) -> bool:
        """
        Проверяет, атакуется ли клетка `square` фигурами цвета `attacker_color`.
        Важно: для пешек атака считается по диагонали независимо от занятости клетки.
        """
        for file in File:
            for rank in range(1, 9):
                coord = Coordinate(file, rank)
                piece = self.get_piece(coord)
                if piece is None or piece.color != attacker_color:
                    continue

                if isinstance(piece, Pawn):
                    direction = 1 if piece.color == Color.WHITE else -1
                    for df in (-1, 1):
                        target = Coordinate.try_shift(piece.coordinate, df, direction)
                        if target is not None and target == square:
                            return True
                    continue

                if isinstance(piece, King):
                    file_diff = abs(piece.coordinate.get_file_index() - square.get_file_index())
                    rank_diff = abs(piece.coordinate.rank - square.rank)
                    if file_diff <= 1 and rank_diff <= 1:
                        return True
                    continue

                # Остальные фигуры: используем их возможные ходы
                moves = piece.get_possible_moves(self)
                if square in moves:
                    return True

        return False
    
    def is_king_in_check(self, king_color: Color) -> bool:
        """Проверяет, находится ли король под шахом"""

        king_square = self.find_king(king_color)
        if king_square is None:
            return False
        
        # Проверяем все фигуры противоположного цвета
        opponent_color = king_color.opponent()
        
        for file in File:
            for rank in range(1, 9):
                coord = Coordinate(file, rank)
                piece = self.get_piece(coord)
                
                if piece is not None and piece.color == opponent_color:
                    # Получаем все возможные ходы этой фигуры
                    possible_moves = piece.get_possible_moves(self)
                    # Если король находится среди возможных ходов - это шах
                    if king_square in possible_moves:
                        return True
        return False


    
    def move(self, from_coord: Coordinate, to_coord: Coordinate) -> Optional[Piece]:
        print(f"Ход: {from_coord} → {to_coord}")
        piece = self.get_piece(from_coord)
        if piece is None:
            raise ValueError(f"No piece at {from_coord}")
        if piece.color != self.current_player:
            raise ValueError("Not your turn")
        
        legal_moves = piece.get_possible_moves(self)
        
        if to_coord not in legal_moves:
            raise ValueError(f"Illegal move: {from_coord} → {to_coord}")
        
        # --- ПРОВЕРКА КОРОЛЯ НА ШАХ ПОСЛЕ ХОДА ---
        moving_color = piece.color
        is_castling = isinstance(piece, King) and abs(to_coord.get_file_index() - from_coord.get_file_index()) == 2
        is_pawn = isinstance(piece, Pawn)
        is_en_passant = False
        en_passant_capture_coord: Optional[Coordinate] = None
        if is_pawn and self.en_passant_target is not None:
            # Взятие на проходе
            if to_coord == self.en_passant_target and self.get_piece(to_coord) is None:
                is_en_passant = True
                direction = 1 if piece.color == Color.WHITE else -1
                en_passant_capture_coord = Coordinate(to_coord.file, to_coord.rank - direction)
        
        # Временно выполняем ход для проверки
        original_from = self.get_piece(from_coord)
        original_to = self.get_piece(to_coord)
        original_ep_captured = self.get_piece(en_passant_capture_coord) if en_passant_capture_coord else None
        rook_from: Optional[Coordinate] = None
        rook_to: Optional[Coordinate] = None
        original_rook = None
        
        self.squares[from_coord.get_file_index()][from_coord.get_rank_index()] = None
        moved_piece = piece.move_to(to_coord)
        self.squares[to_coord.get_file_index()][to_coord.get_rank_index()] = moved_piece

        if is_en_passant and en_passant_capture_coord is not None:
            self.squares[en_passant_capture_coord.get_file_index()][en_passant_capture_coord.get_rank_index()] = None

        if is_castling:
            rank = from_coord.rank
            if to_coord.file == File.G:
                rook_from = Coordinate(File.H, rank)
                rook_to = Coordinate(File.F, rank)
            elif to_coord.file == File.C:
                rook_from = Coordinate(File.A, rank)
                rook_to = Coordinate(File.D, rank)
            if rook_from and rook_to:
                original_rook = self.get_piece(rook_from)
                if not isinstance(original_rook, Rook):
                    # Откатываем
                    self.squares[from_coord.get_file_index()][from_coord.get_rank_index()] = original_from
                    self.squares[to_coord.get_file_index()][to_coord.get_rank_index()] = original_to
                    if is_en_passant and en_passant_capture_coord is not None:
                        self.squares[en_passant_capture_coord.get_file_index()][en_passant_capture_coord.get_rank_index()] = original_ep_captured
                    raise ValueError("Недопустимая рокировка: нет ладьи")
                self.squares[rook_from.get_file_index()][rook_from.get_rank_index()] = None
                self.squares[rook_to.get_file_index()][rook_to.get_rank_index()] = original_rook.move_to(rook_to)
        
        king_in_check_after_move = self.is_king_in_check(moving_color)
        
        # Откатываем временный ход
        self.squares[from_coord.get_file_index()][from_coord.get_rank_index()] = original_from
        self.squares[to_coord.get_file_index()][to_coord.get_rank_index()] = original_to
        if is_en_passant and en_passant_capture_coord is not None:
            self.squares[en_passant_capture_coord.get_file_index()][en_passant_capture_coord.get_rank_index()] = original_ep_captured
        if is_castling and rook_from and rook_to:
            self.squares[rook_from.get_file_index()][rook_from.get_rank_index()] = original_rook
            self.squares[rook_to.get_file_index()][rook_to.get_rank_index()] = None
        
        if king_in_check_after_move:
            raise ValueError(f"Недопустимый ход: после хода король остаётся под шахом")
        
        captured = self.get_piece(to_coord)
        
        self.squares[from_coord.get_file_index()][from_coord.get_rank_index()] = None
        moved_piece = piece.move_to(to_coord)
        self.squares[to_coord.get_file_index()][to_coord.get_rank_index()] = moved_piece

        # Рокировка
        if is_castling:
            rank = from_coord.rank
            if to_coord.file == File.G:
                rook_from = Coordinate(File.H, rank)
                rook_to = Coordinate(File.F, rank)
            elif to_coord.file == File.C:
                rook_from = Coordinate(File.A, rank)
                rook_to = Coordinate(File.D, rank)
            if rook_from and rook_to:
                rook_piece = self.get_piece(rook_from)
                if not isinstance(rook_piece, Rook):
                    raise ValueError("Недопустимая рокировка: нет ладьи")
                self.squares[rook_from.get_file_index()][rook_from.get_rank_index()] = None
                self.squares[rook_to.get_file_index()][rook_to.get_rank_index()] = rook_piece.move_to(rook_to)

        if is_en_passant and en_passant_capture_coord is not None:
            captured = self.get_piece(en_passant_capture_coord)
            self.squares[en_passant_capture_coord.get_file_index()][en_passant_capture_coord.get_rank_index()] = None

        self.en_passant_target = None
        if isinstance(piece, Pawn):
            start_rank = 2 if piece.color == Color.WHITE else 7
            if from_coord.rank == start_rank and abs(to_coord.rank - from_coord.rank) == 2:
                mid_rank = (from_coord.rank + to_coord.rank) // 2
                self.en_passant_target = Coordinate(from_coord.file, mid_rank)
        
        # Смена хода
        self.current_player = self.current_player.opponent()
        
        return captured

    
    def drop(self, piece_class: type[Piece], color: Color, coord: Coordinate):
        try:
            from bughouse.figures import Rook, King
            if piece_class == Rook or piece_class == King:
                piece = piece_class(coord, color, has_moved=True)
            else:
                piece = piece_class(coord, color)
            self.place_piece(piece)
            self.en_passant_target = None
            self.current_player = self.current_player.opponent()
        except Exception as e:
            raise RuntimeError(f"Не удалось создать фигуру: {piece_class.__name__}") from e
    
    def __str__(self) -> str:
        lines = []
        for rank in range(8, 0, -1):
            line_parts = []
            for file in File:
                coord = Coordinate(file, rank)
                piece = self.get_piece(coord)
                if piece is None:
                    line_parts.append(". ")
                else:
                    symbol = self._piece_symbol(piece)
                    if piece.color == Color.BLACK:
                        symbol = symbol.lower()
                    line_parts.append(f"{symbol} ")
            lines.append("".join(line_parts))
        return "\n".join(lines)
    
    def _piece_symbol(self, piece: Piece) -> str:
        if isinstance(piece, Pawn):
            return 'P'
        elif isinstance(piece, Knight):
            return 'N'
        elif isinstance(piece, Bishop):
            return 'B'
        elif isinstance(piece, Rook):
            return 'R'
        elif isinstance(piece, Queen):
            return 'Q'
        elif isinstance(piece, King):
            return 'K'
        else:
            return '?'
    
    
    def find_king(self, color: Color) -> Optional[Coordinate]:
        for f in range(8):
            for r in range(8):
                piece = self.squares[f][r]
                if isinstance(piece, King) and piece.color == color:
                    return piece.coordinate
        return None
    

    

    

    
        
    def _file_to_left(self, file: File) -> Optional[File]:
        index = file.value
        return File(index - 1) if index > 0 else None
    
    def _file_to_right(self, file: File) -> Optional[File]:
        index = file.value
        return File(index + 1) if index < 7 else None
    def _find_king_attackers(self, king_pos: Coordinate, attacker_color: Color) -> List['Piece']:
        """Находит все фигуры указанного цвета, которые атакуют короля"""
        attackers = []
        
        for file in File:
            for rank in range(1, 9):
                coord = Coordinate(file, rank)
                piece = self.get_piece(coord)
                
                if piece is not None and piece.color == attacker_color:
                    # Получаем возможные ходы фигуры
                    moves = piece.get_possible_moves(self)
                    
                    # Проверяем, атакует ли эта фигура короля
                    if king_pos in moves:
                        attackers.append(piece)
        
        return attackers


    
    def is_checkmate(self, king_color: Color, reserve: Optional['PiecesReserve'] = None) -> bool:
        """Проверяет, поставлен ли мат королю указанного цвета"""
        if not self.is_king_in_check(king_color):
            return False
        
        king_pos = self.find_king(king_color)
        
        king = self.get_piece(king_pos)
        if not isinstance(king, King):
            return False
        
        king_moves = king.get_possible_moves(self)
        for move in king_moves:
            # Пробуем сделать ход королем
            original_king = self.get_piece(king_pos)
            target_piece = self.get_piece(move)
            
            # Временно делаем ход
            self.squares[king_pos.get_file_index()][king_pos.get_rank_index()] = None
            moved_king = king.move_to(move)
            self.squares[move.get_file_index()][move.get_rank_index()] = moved_king
            
            # Проверяем, остался ли король под шахом после хода
            still_in_check = self.is_king_in_check(king_color)
            
            # Откатываем ход
            self.squares[king_pos.get_file_index()][king_pos.get_rank_index()] = original_king
            self.squares[move.get_file_index()][move.get_rank_index()] = target_piece
            
            if not still_in_check:
                return False
        

        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]

        attacker_color = king_color.opponent()
        attackers = self._find_king_attackers(king_pos, attacker_color)
        
        print(f"    Найдено атакующих фигур: {len(attackers)}")
        for i, attacker in enumerate(attackers, 1):
            file_char = chr(ord('a') + attacker.coordinate.file.value)
            print(f"    {i}. {attacker.__class__.__name__} на {file_char}{attacker.coordinate.rank}")
        

        
        if len(attackers) > 1:
            print(f"Несколько атакующих фигур - нельзя съесть все за один ход")
        else:
            attacker = attackers[0]
            attacker_pos = attacker.coordinate
            
            print(f"    Проверяем защитников для атаки на {attacker_pos}...")
            defenders_found = False
            for file in File:
                for rank in range(1, 9):
                    coord = Coordinate(file, rank)
                    defender = self.get_piece(coord)
                    
                    if (defender is None or defender.color != king_color or 
                        isinstance(defender, King)):
                        continue
                    
                    # Получаем возможные ходы защитника
                    defender_moves = defender.get_possible_moves(self)
                    
                    # Проверяем, может ли защитник съесть атакующую фигуру
                    if attacker_pos in defender_moves:
                        print(f"      {defender.__class__.__name__} на {coord} может съесть атакующую фигуру")
                        

                        original_defender = defender
                        original_attacker = attacker
                        
                        self.squares[coord.get_file_index()][coord.get_rank_index()] = None
                        moved_defender = defender.move_to(attacker_pos)
                        self.squares[attacker_pos.get_file_index()][attacker_pos.get_rank_index()] = moved_defender
                        
                        still_in_check = self.is_king_in_check(king_color)
                        
                        self.squares[coord.get_file_index()][coord.get_rank_index()] = original_defender
                        self.squares[attacker_pos.get_file_index()][attacker_pos.get_rank_index()] = original_attacker
                        
                        if not still_in_check:
                            print(f"Можно съесть атакующую фигуру без шаха → НЕ МАТ")
                            defenders_found = True
                            break
                        else:
                            print(f"Но после взятия король все еще под шахом")
                
                if defenders_found:
                    break
            
            if defenders_found:
                return False
            
            print(f"Нельзя съесть атакующую фигуру или после взятия все еще шах")
        from bughouse.figures import Bishop
        
        test_piece_class = Bishop
        
        for dx, dy in directions:
            try:
                new_file_idx = king_pos.get_file_index() + dx
                new_rank = king_pos.rank + dy
                
                if 0 <= new_file_idx < 8 and 1 <= new_rank <= 8:
                    new_file = File(new_file_idx)
                    drop_square = Coordinate(new_file, new_rank)                    
                    if not self.is_empty(drop_square):
                        continue                    
                    original_piece = None
                    temp_piece = test_piece_class(drop_square, king_color)
                    self.squares[drop_square.get_file_index()][drop_square.get_rank_index()] = temp_piece
                    still_in_check = self.is_king_in_check(king_color)
                    # Откатываем
                    self.squares[drop_square.get_file_index()][drop_square.get_rank_index()] = original_piece
                    if not still_in_check:
                        print(f"Можно закрыться фигурой на {drop_square} → НЕ МАТ")
                        return False
            except (ValueError, IndexError):
                continue
        
        return True
    
    def _find_attackers(self, target: Coordinate, attacker_color: Color) -> list[Piece]:
        """Находит все фигуры указанного цвета, которые атакуют указанную клетку"""
        attackers = []
        for f in range(8):
            for r in range(8):
                piece = self.squares[f][r]
                if piece is not None and piece.color == attacker_color:
                    if self._can_attack_square(piece, target):
                        attackers.append(piece)
        return attackers
    
    def _is_knight_or_adjacent_attack(self, attacker: Piece, king_pos: Coordinate) -> bool:
        """Проверяет, является ли атака от коня или фигуры в упор (соседняя клетка)"""
        if isinstance(attacker, Knight):
            return True
        
        file_diff = abs(attacker.coordinate.get_file_index() - king_pos.get_file_index())
        rank_diff = abs(attacker.coordinate.rank - king_pos.rank)
        
        return file_diff <= 1 and rank_diff <= 1
    
    
    def to_fen(self) -> str:
        """Преобразует позицию доски в FEN формат"""
        ranks = []
        for rank_idx in range(7, -1, -1):
            rank_str = ""
            empty_count = 0
            for file_idx in range(8):
                piece = self.squares[file_idx][rank_idx]
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        rank_str += str(empty_count)
                        empty_count = 0
                    symbol = self._piece_to_fen_symbol(piece)
                    rank_str += symbol
            if empty_count > 0:
                rank_str += str(empty_count)
            ranks.append(rank_str)
        
        position = "/".join(ranks)
        
        active_color = "w" if self.current_player == Color.WHITE else "b"
        
        castling = self._get_castling_rights()
        en_passant = str(self.en_passant_target) if self.en_passant_target is not None else "-"
        halfmove_clock = "0"
        
        fullmove_number = "1"
        
        return f"{position} {active_color} {castling} {en_passant} {halfmove_clock} {fullmove_number}"
    
    def _piece_to_fen_symbol(self, piece: Piece) -> str:
        """Преобразует фигуру в символ FEN"""
        from bughouse.figures import Pawn, Knight, Bishop, Rook, Queen, King
        symbol_map = {
            Pawn: 'P',
            Knight: 'N',
            Bishop: 'B',
            Rook: 'R',
            Queen: 'Q',
            King: 'K'
        }
        symbol = symbol_map.get(type(piece), '?')
        if piece.color == Color.BLACK:
            symbol = symbol.lower()
        return symbol
    
    def _get_castling_rights(self) -> str:
        """Возвращает права на рокировку в формате FEN (KQkq)"""
        rights = []
        
        white_king = self.find_king(Color.WHITE)
        if white_king and white_king.file == File.E and white_king.rank == 1:
            from bughouse.figures import King, Rook
            king = self.get_piece(white_king)
            if isinstance(king, King) and not king.has_moved:
                h1_rook = self.get_piece(Coordinate(File.H, 1))
                if isinstance(h1_rook, Rook) and not h1_rook.has_moved:
                    rights.append('K')
                a1_rook = self.get_piece(Coordinate(File.A, 1))
                if isinstance(a1_rook, Rook) and not a1_rook.has_moved:
                    rights.append('Q')
        
        black_king = self.find_king(Color.BLACK)
        if black_king and black_king.file == File.E and black_king.rank == 8:
            from bughouse.figures import King, Rook
            king = self.get_piece(black_king)
            if isinstance(king, King) and not king.has_moved:
                h8_rook = self.get_piece(Coordinate(File.H, 8))
                if isinstance(h8_rook, Rook) and not h8_rook.has_moved:
                    rights.append('k')
                a8_rook = self.get_piece(Coordinate(File.A, 8))
                if isinstance(a8_rook, Rook) and not a8_rook.has_moved:
                    rights.append('q')
        
        return "".join(rights) if rights else "-"
    
    @staticmethod
    def from_fen(fen: str) -> 'ChessBoard':
        """Создает доску из FEN строки"""
        from bughouse.figures import Pawn, Knight, Bishop, Rook, Queen, King
        
        parts = fen.split()
        if len(parts) < 1:
            raise ValueError("Invalid FEN: missing position")
        
        board = ChessBoard()
        board._clear()
        
        ranks = parts[0].split('/')
        if len(ranks) != 8:
            raise ValueError("Invalid FEN: must have 8 ranks")
        
        for rank_idx, rank_str in enumerate(ranks):
            rank_num = 8 - rank_idx
            file_idx = 0
            for char in rank_str:
                if char.isdigit():
                    file_idx += int(char)
                else:
                    piece = board._fen_symbol_to_piece(char, Coordinate(File(file_idx), rank_num))
                    if piece:
                        board.place_piece(piece)
                    file_idx += 1
        
        if len(parts) > 1:
            active_color = parts[1]
            board.current_player = Color.WHITE if active_color == 'w' else Color.BLACK

        if len(parts) > 3:
            ep = parts[3]
            board.en_passant_target = None if ep == "-" else Coordinate.from_notation(ep)
        
        if len(parts) > 2:
            castling = parts[2]
            if castling != "-":

                white_king = board.find_king(Color.WHITE)
                black_king = board.find_king(Color.BLACK)
                
                if white_king:
                    king = board.get_piece(white_king)
                    if isinstance(king, King):
                        if 'K' not in castling and 'Q' not in castling:
                            board.squares[white_king.get_file_index()][white_king.get_rank_index()] = King(
                                white_king, Color.WHITE, True
                            )
                        else:
                            h1_rook = board.get_piece(Coordinate(File.H, 1))
                            if isinstance(h1_rook, Rook) and 'K' not in castling:
                                board.squares[7][0] = Rook(Coordinate(File.H, 1), Color.WHITE, True)
                            
                            a1_rook = board.get_piece(Coordinate(File.A, 1))
                            if isinstance(a1_rook, Rook) and 'Q' not in castling:
                                board.squares[0][0] = Rook(Coordinate(File.A, 1), Color.WHITE, True)
                
                if black_king:
                    king = board.get_piece(black_king)
                    if isinstance(king, King):
                        if 'k' not in castling and 'q' not in castling:
                            board.squares[black_king.get_file_index()][black_king.get_rank_index()] = King(
                                black_king, Color.BLACK, True
                            )
                        else:
                            h8_rook = board.get_piece(Coordinate(File.H, 8))
                            if isinstance(h8_rook, Rook) and 'k' not in castling:
                                board.squares[7][7] = Rook(Coordinate(File.H, 8), Color.BLACK, True)
                            
                            a8_rook = board.get_piece(Coordinate(File.A, 8))
                            if isinstance(a8_rook, Rook) and 'q' not in castling:
                                board.squares[0][7] = Rook(Coordinate(File.A, 8), Color.BLACK, True)
        
        return board
    
    def _fen_symbol_to_piece(self, symbol: str, coord: Coordinate) -> Optional[Piece]:
        """Преобразует символ FEN в фигуру"""
        from bughouse.figures import Pawn, Knight, Bishop, Rook, Queen, King
        
        is_white = symbol.isupper()
        color = Color.WHITE if is_white else Color.BLACK
        symbol_upper = symbol.upper()
        
        piece_map = {
            'P': Pawn,
            'N': Knight,
            'B': Bishop,
            'R': Rook,
            'Q': Queen,
            'K': King
        }
        
        piece_class = piece_map.get(symbol_upper)
        if piece_class:

            if piece_class == Rook:
                return Rook(coord, color, False)
            elif piece_class == King:
                return King(coord, color, False)
            else:
                return piece_class(coord, color)
        return None