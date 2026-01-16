import os
import socket
import json
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import ValidationError

from .models import (
    MoveRequest,
    DropRequest,
    ApiStartResponse,
    ApiPlayerLink,
    StateResponse,
)
from .session import SessionManager, Session
from .state_builder import build_state
from bughouse.game.game import Game, PromotionRequired
from bughouse.game.player import Player
from bughouse.game.color import Color
from bughouse.figures import Pawn, Knight, Bishop, Rook, Queen


app = FastAPI()
session_manager = SessionManager()


def get_server_ip():
    """Возвращает локальный IP-адрес сервера."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


@app.get("/")
async def root():
    return RedirectResponse(url="/index.html")


@app.post("/api/start", response_model=ApiStartResponse)
async def start_game(request: Request):
    """Создаёт новую игру и возвращает 4 ссылки для игроков."""
    game = Game()

    player_tokens: Dict[int, str] = {}
    for player_id in [1, 2, 3, 4]:
        token = os.urandom(16).hex()
        player_tokens[player_id] = token

    session = session_manager.create_session(game, player_tokens)
    session.fen_position = json.dumps(game.to_fen_dict())

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

    return ApiStartResponse(sessionId=session.session_id, players=links)


@app.get("/api/state", response_model=StateResponse)
async def get_state(token: str = Query(...)):
    """Возвращает состояние игры по токену"""
    ref = session_manager.get_token_ref(token)
    if ref is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    session = session_manager.get_session(ref.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    game_over = session.game.check_game_over()
    state = build_state(session, ref.player_id)
    if game_over:
        state_dict = state.model_dump()
        state_dict["gameOver"] = game_over
        return JSONResponse(state_dict)

    return state


@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()

    ref = session_manager.get_token_ref(token)
    if ref is None:
        await websocket.close(code=1008, reason="Invalid token")
        return

    session = session_manager.get_session(ref.session_id)
    if session is None:
        await websocket.close(code=1008, reason="Session not found")
        return

    session.attach(websocket)

    try:
        initial_state = build_state(session, ref.player_id)
        await websocket.send_json({
            "type": "state_update",
            "states": {str(ref.player_id): initial_state.model_dump()}
        })

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        session.detach(websocket)


@app.post("/api/move")
async def make_move(request: MoveRequest):
    """Обработка хода игрока"""
    ref = session_manager.get_token_ref(request.token)
    if ref is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    session = session_manager.get_session(ref.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if not request.from_:
        raise HTTPException(status_code=400, detail="Missing 'from' field")

    try:
        session.game.make_move(
            ref.player_id,
            request.from_,
            request.to,
            victim_player_id=request.victim_player_id,
            victim_square=request.victim_square,
        )
        session.version += 1
        session.fen_position = json.dumps(session.game.to_fen_dict())

        game_over = session.game.check_game_over()
        await session.notify_observers(game_over)

        state = build_state(session, ref.player_id)
        if game_over:
            state_dict = state.model_dump()
            state_dict["gameOver"] = game_over
            return JSONResponse(state_dict)

        return state

    except PromotionRequired as pr:
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
        error_msg = str(e)
        print("Move error:", error_msg)
        raise HTTPException(status_code=400, detail=error_msg)


@app.post("/api/drop", response_model=StateResponse)
async def make_drop(request: DropRequest):
    """Обработка дропа фигуры"""
    ref = session_manager.get_token_ref(request.token)
    if ref is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    session = session_manager.get_session(ref.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        session.game.make_drop(ref.player_id, request.piece, request.square)
        session.version += 1
        session.fen_position = json.dumps(session.game.to_fen_dict())

        game_over = session.game.check_game_over()
        await session.notify_observers(game_over)

        state = build_state(session, ref.player_id)
        if game_over:
            state_dict = state.model_dump()
            state_dict["gameOver"] = game_over
            return JSONResponse(state_dict)

        return state

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")