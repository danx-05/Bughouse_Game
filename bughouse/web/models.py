from typing import Dict, List, Optional
from pydantic import BaseModel, Field


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