import os
import socket
import uuid
import json
import asyncio
from typing import Dict, List, Optional, Set
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Request
from bughouse.game import PromotionRequired
from bughouse.game import Game
from bughouse.player import Player
from bughouse.chess_board import ChessBoard
from bughouse.color import Color
from bughouse.figures import Pawn, Knight, Bishop, Rook, Queen


app = FastAPI()

# Хранилище сессий и токенов
SESSIONS: Dict[str, 'Session'] = {}
TOKENS: Dict[str, 'TokenRef'] = {}
# Хранилище активных WebSocket соединений: session_id -> Set[WebSocket]
WEBSOCKET_CONNECTIONS: Dict[str, Set[WebSocket]] = {}


class TokenRef:
    def __init__(self, session_id: str, player_id: int):
        self.session_id = session_id
        self.player_id = player_id


class Session:
    def __init__(self, session_id: str, game: Game, player_tokens: Dict[int, str]):
        self.session_id = session_id
        self.game = game
        self.player_tokens = player_tokens
        self.version = 1
        self.lock = None
        self.fen_position: Optional[str] = None


async def broadcast_state_update(session_id: str, game_over: Optional[Dict] = None):
    """Отправляет обновление состояния всем подключенным клиентам сессии"""
    if session_id not in WEBSOCKET_CONNECTIONS:
        return
    
    session = SESSIONS.get(session_id)
    if session is None:
        return
    
    states = {}
    for player_id in [1, 2, 3, 4]:
        try:
            state = build_state(session, player_id)
            state_dict = state.model_dump()
            if game_over:
                state_dict["gameOver"] = game_over
            states[str(player_id)] = state_dict
        except Exception:
            pass
    
    disconnected = set()
    for ws in WEBSOCKET_CONNECTIONS[session_id]:
        try:
            await ws.send_json({
                "type": "state_update",
                "states": states,
                "gameOver": game_over
            })
        except Exception:
            disconnected.add(ws)
    
    WEBSOCKET_CONNECTIONS[session_id] -= disconnected
    if not WEBSOCKET_CONNECTIONS[session_id]:
        del WEBSOCKET_CONNECTIONS[session_id]


class MoveRequest(BaseModel):
    token: str
    from_: str = Field(validation_alias="from")
    to: str
    victim_player_id: Optional[int] = Field(default=None, validation_alias="victimPlayerId")
    victim_square: Optional[str] = Field(default=None, validation_alias="victimSquare")
    
    model_config = {
        "populate_by_name": True
    }


class DropRequest(BaseModel):
    token: str
    piece: str
    square: str


class ApiPlayerLink(BaseModel):
    playerId: int
    board: str
    color: str
    token: str
    url: str


class ApiStartResponse(BaseModel):
    sessionId: str
    players: List[ApiPlayerLink]


class BoardState(BaseModel):
    currentPlayer: str
    grid: List[List[str]]
    inCheck: bool
    kingInCheck: Optional[str] = None


class MeState(BaseModel):
    playerId: int
    board: str
    color: str


class StateResponse(BaseModel):
    sessionId: str
    version: int
    me: MeState
    boards: Dict[str, BoardState]
    reserves: Dict[str, str]
    myReserve: Dict[str, int]
    reserveCounts: Dict[str, Dict[str, int]]
    fen: Optional[str] = None




@app.get("/")
async def root():
    """Главная страница"""
    return RedirectResponse(url="/index.html")


def get_server_ip():
    """Функция для получения IP сервера"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

@app.post("/api/start", response_model=ApiStartResponse)
async def start_game(request: Request):
    """Создать сессию и 4 ссылки"""
    session_id = str(uuid.uuid4())
    game = Game()
    
    player_tokens: Dict[int, str] = {}
    for player_id in [1, 2, 3, 4]:
        token = uuid.uuid4().hex
        player_tokens[player_id] = token
        TOKENS[token] = TokenRef(session_id, player_id)
    
    session = Session(session_id, game, player_tokens)
    session.fen_position = json.dumps(game.to_fen_dict())
    SESSIONS[session_id] = session

    port = request.url.port or 8000
    
    server_ip = get_server_ip()
    base_url = f"http://{server_ip}:{port}"
    
    links = []
    for player_id in [1, 2, 3, 4]:
        player = game.get_player(player_id)
        token = player_tokens[player_id]
        url = f"{base_url}/player.html?token={token}"
        links.append(ApiPlayerLink(
            playerId=player.player_id,
            board=player.board_name,
            color=player.color.value,
            token=token,
            url=url
        ))
    
    return ApiStartResponse(sessionId=session_id, players=links)



@app.get("/api/state", response_model=StateResponse)
async def get_state(token: str = Query(...)):
    """Состояние по токену (видно две доски, но "me" определяет права)"""
    ref = TOKENS.get(token)
    if ref is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    session = SESSIONS.get(ref.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return build_state(session, ref.player_id)


@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket соединение для получения обновлений состояния в реальном времени"""
    await websocket.accept()
    
    ref = TOKENS.get(token)
    if ref is None:
        print(f"WebSocket: Invalid token: {token}")
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    session = SESSIONS.get(ref.session_id)
    if session is None:
        print(f"WebSocket: Session not found: {ref.session_id}")
        await websocket.close(code=1008, reason="Session not found")
        return
    
    if ref.session_id not in WEBSOCKET_CONNECTIONS:
        WEBSOCKET_CONNECTIONS[ref.session_id] = set()
    WEBSOCKET_CONNECTIONS[ref.session_id].add(websocket)
    
    try:
        try:
            initial_state = build_state(session, ref.player_id)
            await websocket.send_json({
                "type": "state_update",
                "states": {
                    str(ref.player_id): initial_state.model_dump()
                }
            })
        except Exception as e:
            print(f"WebSocket: Error sending initial state: {e}")
            import traceback
            traceback.print_exc()
            await websocket.close(code=1011, reason=f"Error: {str(e)}")
            return
        
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                print(f"WebSocket: Client disconnected normally")
                break
            except Exception as e:
                print(f"WebSocket: Error receiving message: {e}")
                break
    except WebSocketDisconnect:
        print(f"WebSocket: Client disconnected")
    except Exception as e:
        print(f"WebSocket: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Удаляем соединение при отключении
        if ref.session_id in WEBSOCKET_CONNECTIONS:
            WEBSOCKET_CONNECTIONS[ref.session_id].discard(websocket)
            if not WEBSOCKET_CONNECTIONS[ref.session_id]:
                del WEBSOCKET_CONNECTIONS[ref.session_id]


@app.post("/api/move")
async def make_move(request: MoveRequest):
    """Ход: только своей доской и своим цветом"""
    try:
        pass
    except Exception as e:
        print(f"Error logging request: {e}")
    
    if not request.token:
        raise HTTPException(status_code=400, detail="Missing token")
    
    ref = TOKENS.get(request.token)
    if ref is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    session = SESSIONS.get(ref.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        from_square = request.from_
        if not from_square:
            raise HTTPException(status_code=400, detail="Missing 'from' field")
        
        session.game.make_move(
            ref.player_id,
            from_square,
            request.to,
            victim_player_id=request.victim_player_id,
            victim_square=request.victim_square,
        )
        session.version += 1
        # Сохраняем позицию после каждого хода
        session.fen_position = json.dumps(session.game.to_fen_dict())
        
        # Проверяем, завершена ли игра
        game_over = session.game.check_game_over()
        
        # Отправляем обновление всем подключенным клиентам
        await broadcast_state_update(ref.session_id, game_over)
        
        state = build_state(session, ref.player_id)
        if game_over:
            # Добавляем информацию о завершении игры в ответ
            state_dict = state.model_dump()
            state_dict["gameOver"] = game_over
            return state_dict
        
        return state
    except PromotionRequired as pr:
        # Требуется выбор фигуры для превращения пешки. Позицию НЕ меняем.
        return JSONResponse(
            status_code=409,
            content={
                "error": "promotion_required",
                "promotion": {
                    "victimPlayerId": pr.victim_player_id,
                    "options": pr.options,
                },
            },
        )
    except Exception as e:
        # Выводим только сообщение об ошибке без полного traceback
        error_msg = str(e)
        print(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)


@app.post("/api/drop", response_model=StateResponse)
async def make_drop(request: DropRequest):
    """Дроп фигуры"""
    if not request.token:
        raise HTTPException(status_code=400, detail="Missing token")
    
    ref = TOKENS.get(request.token)
    if ref is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    session = SESSIONS.get(ref.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session.game.make_drop(ref.player_id, request.piece, request.square)
        session.version += 1
        # Сохраняем позицию после каждого хода
        session.fen_position = json.dumps(session.game.to_fen_dict())
        
        # Проверяем, завершена ли игра
        game_over = session.game.check_game_over()
        
        # Отправляем обновление всем подключенным клиентам
        await broadcast_state_update(ref.session_id, game_over)
        
        state = build_state(session, ref.player_id)
        if game_over:
            # Добавляем информацию о завершении игры в ответ
            state_dict = state.model_dump()
            state_dict["gameOver"] = game_over
            return state_dict
        
        return state
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/fen")
async def get_fen(token: str = Query(...)):
    """Получить текущую позицию в формате FEN"""
    ref = TOKENS.get(token)
    if ref is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    session = SESSIONS.get(ref.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    fen_dict = session.game.to_fen_dict()
    return {"fen": json.dumps(fen_dict)}


@app.post("/api/load-fen")
async def load_fen(request: dict):
    """Загрузить позицию из формата FEN"""
    token = request.get("token")
    fen_json = request.get("fen")
    
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")
    if not fen_json:
        raise HTTPException(status_code=400, detail="Missing fen")
    
    ref = TOKENS.get(token)
    if ref is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    session = SESSIONS.get(ref.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        fen_dict = json.loads(fen_json)
        session.game.from_fen_dict(fen_dict)
        session.version += 1
        session.fen_position = fen_json
        # Отправляем обновление всем подключенным клиентам
        await broadcast_state_update(ref.session_id)
        return build_state(session, ref.player_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid FEN: {str(e)}")

def build_state(session: Session, me_player_id: int) -> StateResponse:
    """Строит состояние игры для клиента"""
    game = session.game
    me = game.get_player(me_player_id)

    # Проверяем, не завершена ли игра (мат)
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
    """Количества фигур в запасе ИМЕННО текущего игрока (для UI дропа)"""
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

if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
