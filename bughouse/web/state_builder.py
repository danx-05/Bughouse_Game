import json
from typing import Dict, List
from bughouse.game.chess_board import ChessBoard
from bughouse.game.color import Color
from bughouse.figures import *
from bughouse.game.player import Player
from bughouse.web.models import *
from bughouse.web.session import Session


def build_state(session: Session, me_player_id: int) -> StateResponse:
    """Строит состояние игры для клиента"""
    game = session.game
    me = game.get_player(me_player_id)

    # Проверяем, не завершена ли игра
    game_over = game.check_game_over()
    
    boards: Dict[str, BoardState] = {}
    board_a = game.board_a
    board_b = game.board_b
    
    # Проверяем шах для обоих игроков
    check_a_white = board_a.is_king_in_check(Color.WHITE)
    check_a_black = board_a.is_king_in_check(Color.BLACK)

    current_player_a = board_a.get_current_player()
    check_a = False
    king_a = None
    
    if current_player_a == Color.WHITE:
        check_a = check_a_white
        if check_a:
            king_a = board_a.find_king(Color.WHITE)
    else:
        check_a = check_a_black
        if check_a:
            king_a = board_a.find_king(Color.BLACK)
    
    check_b_white = board_b.is_king_in_check(Color.WHITE)
    check_b_black = board_b.is_king_in_check(Color.BLACK)
    
    current_player_b = board_b.get_current_player()
    check_b = False
    king_b = None
    
    if current_player_b == Color.WHITE:
        check_b = check_b_white
        if check_b:
            king_b = board_b.find_king(Color.WHITE)
    else:
        check_b = check_b_black
        if check_b:
            king_b = board_b.find_king(Color.BLACK)
        
    boards["A"] = BoardState(
        currentPlayer=current_player_a.value,
        grid=board_to_grid(board_a),
        inCheck=check_a,
        kingInCheck=str(king_a) if king_a else None
    )
    boards["B"] = BoardState(
        currentPlayer=current_player_b.value,
        grid=board_to_grid(board_b),
        inCheck=check_b,
        kingInCheck=str(king_b) if king_b else None
    )

    reserves: Dict[str, str] = {}
    for player_id in [1, 2, 3, 4]:
        reserves[str(player_id)] = game.get_player(player_id).pieces_reserve.to_readable_string()
    
    reserve_counts: Dict[str, Dict[str, int]] = {}
    for player_id in [1, 2, 3, 4]:
        reserve_counts[str(player_id)] = reserve_counts_for_player(game.get_player(player_id))
    
    if session.fen_position is None:
        session.fen_position = json.dumps(game.to_fen_dict())
    
    return StateResponse(
        sessionId=session.session_id,
        version=session.version,
        me=MeState(
            playerId=me.player_id,
            board=me.board_name,
            color=me.color.value
        ),
        boards=boards,
        reserves=reserves,
        myReserve=reserve_counts_for_player(me),
        reserveCounts=reserve_counts,
        fen=session.fen_position
    )


def reserve_counts_for_player(player: Player) -> Dict[str, int]:
    """Количества фигур в запасе текущего игрока (для UI дропа)"""
    return {
        "P": player.pieces_reserve.get_count(Pawn),
        "N": player.pieces_reserve.get_count(Knight),
        "B": player.pieces_reserve.get_count(Bishop),
        "R": player.pieces_reserve.get_count(Rook),
        "Q": player.pieces_reserve.get_count(Queen)
    }

def board_to_grid(board: ChessBoard) -> List[List[str]]:
    """Возвращает матрицу 8x8, строки — ранги 8..1, столбцы — файлы a..h"""
    lines = str(board).split("\n")
    grid: List[List[str]] = []
    for line in lines:
        if line.strip():
            tokens = line.strip().split()
            grid.append(tokens)
    return grid