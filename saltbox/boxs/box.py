from abc import ABC
from typing import Union, Mapping, Sequence, Optional, Set
from dataclasses import dataclass, field
from pprint import pformat
from saltbox.utils.file import FileBridge


@dataclass
class BoxBuilder:
    tag: str
    working_directory: str
    files: Sequence[FileBridge] = field(default_factory=list)
    directories: Sequence[FileBridge] = field(default_factory=list)
    commands: Sequence[str] = field(default_factory=list)
    ports: Set[str] = field(default_factory=set)
    proprietary: Mapping[str, object] = field(default_factory=dict)


@dataclass
class CommandReturn:
    output: Union[bytes, str]
    exitcode: int


class Box(ABC):
    def __init__(self, box_builder: BoxBuilder):
        self._open = True
        self._box_builder = box_builder

    def __str__(self):
        return f"{repr(self)}\n{pformat(self._box_builder)}"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self._box_builder.tag}>"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    def is_open(self) -> bool:
        return self._open

    def close(self) -> None:
        self._open = False

    def box_builder(self) -> BoxBuilder:
        return self._box_builder

    def run(self, command: str, detach: bool = False, encoding: str = "utf-8", hard_fail: bool = False) -> Optional[CommandReturn]:
        raise NotImplemented()
