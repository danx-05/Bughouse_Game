from typing import Dict, Optional, Set
import uuid
from fastapi import WebSocket

from ..game.game import Game

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
        self.fen_position: Optional[str] = None
        self.observers: Set[WebSocket] = set()
    
    def attach(self, ws: WebSocket):
        self.observers.add(ws)

    def detach(self, ws: WebSocket):
        self.observers.discard(ws)

    async def notify_observers(self, game_over: Optional[Dict] = None):
        """Уведомляет всех наблюдателей об изменении состояния"""
        from bughouse.web.state_builder import build_state

        states = {}
        for player_id in [1, 2, 3, 4]:
            try:
                state = build_state(self, player_id)
                state_dict = state.model_dump()
                if game_over:
                    state_dict["gameOver"] = game_over
                states[str(player_id)] = state_dict
            except Exception:
                pass

        disconnected = set()
        for ws in self.observers:
            try:
                await ws.send_json({
                    "type": "state_update",
                    "states": states,
                    "gameOver": game_over
                })
            except Exception:
                disconnected.add(ws)

        for ws in disconnected:
            self.detach(ws)

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.tokens: Dict[str, TokenRef] = {}

    def create_session(self, game: Game, player_tokens: Dict[int, str]) -> Session:
        session_id = str(uuid.uuid4())
        session = Session(session_id, game, player_tokens)
        self.sessions[session_id] = session
        for pid, token in player_tokens.items():
            self.tokens[token] = TokenRef(session_id, pid)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self.sessions.get(session_id)

    def get_token_ref(self, token: str) -> Optional[TokenRef]:
        return self.tokens.get(token)