from dataclasses import dataclass


@dataclass
class Command:
    command: str
    detach: bool = False
