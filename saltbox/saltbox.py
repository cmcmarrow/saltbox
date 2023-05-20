from dataclasses import dataclass, field
from typing import Sequence, Optional, Mapping, Union, Set
from saltbox.utils.file import FileData, FileBridge
from saltbox.utils.command import Command
from saltbox.builders import builder
from saltbox.boxs import box
from saltbox import error
from pprint import pformat


@dataclass
class SaltBoxBuilder:
    box_type: str
    tag: str
    master_build: bool = False
    minion_build: bool = False
    master_config: Optional[Union[str, Mapping, FileData]] = None
    minion_config: Optional[Union[str, Mapping, FileData]] = None
    state_files: Sequence[Union[Sequence[str], FileBridge]] = field(default_factory=list)
    python_packages: Sequence[str] = field(default_factory=list)
    salt: str = "salt"
    salt_ip: Optional[str] = "127.0.0.1"
    salt_port: Optional[str] = "4505"
    copies: Sequence[Union[Sequence[str], FileBridge]] = field(default_factory=list)
    ports: Set[str] = field(default_factory=set)
    commands: Sequence[str] = field(default_factory=list)
    start_commands: Sequence[Union[str, Command]] = field(default_factory=list)
    runtime_commands: Sequence[Union[str, Command]] = field(default_factory=list)
    master_auto_start: bool = True
    minion_auto_start: bool = True
    proprietary: Mapping[str, object] = field(default_factory=dict)


class SaltBox:
    def __init__(self,
                 salt_box_builder: SaltBoxBuilder,
                 tag_id: Optional[int] = None,
                 working_directory: Optional[str] = None,
                 run_runtime: bool = True):
        self._box = None
        self._formatted_box, partial_box = builder.builder(salt_box_builder, tag_id, working_directory)
        self._box = partial_box()
        if self._formatted_box.master_auto_start or self._formatted_box.minion_auto_start:
            ret = self._box.run("salt-call --local test.ping")
            if ret.exitcode != 0:
                raise error.SaltBoxException("Salt failed to ping it self!")
        if self._formatted_box.master_auto_start:
            self._box.run("salt-master -l debug", detach=True)
        if self._formatted_box.master_auto_start:
            self._box.run("salt-minion -l debug", detach=True)
        for command in self._formatted_box.start_commands:
            self._box.run(command.command, command.detach)
        if run_runtime:
            for command in self._formatted_box.runtime_commands:
                self._box.run(command.command, command.detach)

    def __str__(self):
        return f"{repr(self)}\n{pformat(self.box_builder())}"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {repr(self._box)}>"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    def is_open(self) -> bool:
        return self._box.is_open()

    def close(self) -> None:
        if self._box is not None:
            self._box.close()

    def box_builder(self) -> box.BoxBuilder:
        return self._box.box_builder()

    def formatted_box_builder(self) -> builder.SaltFormattedBoxBuilder:
        return self._formatted_box

    def run(self, command: str, detach: bool = False, encoding: str = "utf-8") -> Optional[box.CommandReturn]:
        return self._box.run(command, detach, encoding)
