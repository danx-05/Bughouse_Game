from enum import Enum


class File(Enum):
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4
    F = 5
    G = 6
    H = 7
    
    @staticmethod
    def from_char(c: str) -> 'File':
        lower = c.lower()
        if not ('a' <= lower <= 'h'):
            raise ValueError(f"Invalid file: {c}")
        return File(ord(lower) - ord('a'))
    
    def to_char(self) -> str:
        return chr(ord('a') + self.value)
    
    def to_index(self) -> int:
        return self.value

