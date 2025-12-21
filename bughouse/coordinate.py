from dataclasses import dataclass
from bughouse.file import File


@dataclass(frozen=True)
class Coordinate:
    file: File
    rank: int
    
    def __post_init__(self):
        if not (1 <= self.rank <= 8):
            raise ValueError("Rank must be 1–8")
    
    @staticmethod
    def from_notation(notation: str) -> 'Coordinate':
        if not notation or len(notation) != 2:
            raise ValueError(f"Invalid coordinate notation: {notation}")
        file_char = notation[0]
        rank_char = notation[1]
        file = File.from_char(file_char)
        rank = int(rank_char)
        if not (1 <= rank <= 8):
            raise ValueError("Rank must be 1–8")
        return Coordinate(file, rank)
    
    def get_file_index(self) -> int:
        return self.file.to_index()
    
    def get_rank_index(self) -> int:
        return self.rank - 1
    
    def __str__(self) -> str:
        return f"{self.file.to_char()}{self.rank}"
    
    @staticmethod
    def try_shift(from_coord: 'Coordinate', delta_file: int, delta_rank: int) -> 'Coordinate | None':
        new_file_index = from_coord.file.to_index() + delta_file
        new_rank = from_coord.rank + delta_rank
        
        if 0 <= new_file_index <= 7 and 1 <= new_rank <= 8:
            new_file = File(new_file_index)
            return Coordinate(new_file, new_rank)
        return None

