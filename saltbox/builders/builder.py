from typing import Callable, Dict, Optional, Mapping, Type, Tuple, List, Set
from saltbox.boxs import box
from saltbox.builders import dockerbuilder
from functools import partial
from saltbox.error import SaltBoxException
from dataclasses import dataclass, field
from saltbox.utils.file import FileData, FileBridge
from saltbox.utils.command import Command
from os.path import join
from os.path import isfile
import yaml


@dataclass
class SaltFormattedBoxBuilder:
    box_type: str = ""
    tag: str = ""
    master_build: bool = False
    minion_build: bool = False
    master_config: Optional[FileBridge] = None
    minion_config: Optional[FileBridge] = None
    state_files: List[FileBridge] = field(default_factory=list)
    python_packages: List[str] = field(default_factory=list)
    salt: str = "salt"
    salt_ip: Optional[str] = "127.0.0.1"
    salt_port: Optional[str] = None
    copies: List[FileBridge] = field(default_factory=list)
    ports: Set[str] = field(default_factory=set)
    commands: List[str] = field(default_factory=list)
    start_commands: List[Command] = field(default_factory=list)
    runtime_commands: List[Command] = field(default_factory=list)
    master_auto_start: bool = True
    minion_auto_start: bool = True
    proprietary: Dict[str, object] = field(default_factory=dict)


BUILDER_TYPE = Dict[str, Callable[[SaltFormattedBoxBuilder,
                                   box.BoxBuilder,
                                   Optional[int],
                                   Optional[str]], Type[box.Box]]]

DEFAULT_BUILDERS: BUILDER_TYPE = {"docker": dockerbuilder.builder}


def builder(salt_box_builder: "SaltBoxBuilder",
            tag_id: Optional[int] = None,
            working_directory: Optional[str] = None,
            custom_builders: Optional[Mapping[str, BUILDER_TYPE]] = None,
            defaults: bool = True) -> Tuple[SaltFormattedBoxBuilder, Callable[[], box.Box]]:

    tag = salt_box_builder.tag

    if salt_box_builder.master_build:
        tag = f"{tag}_master"

    if tag_id is not None:
        tag = f"{tag}_{tag_id}"

    salt_formatted_box_builder = SaltFormattedBoxBuilder(box_type=salt_box_builder.box_type,
                                                         tag=tag,
                                                         master_build=salt_box_builder.master_build,
                                                         minion_build=salt_box_builder.minion_build,
                                                         python_packages=[p for p in salt_box_builder.python_packages],
                                                         salt=salt_box_builder.salt,
                                                         salt_port=salt_box_builder.salt_port,
                                                         commands=[c for c in salt_box_builder.commands],
                                                         ports=set(salt_box_builder.ports),
                                                         master_auto_start=salt_box_builder.master_auto_start,
                                                         minion_auto_start=salt_box_builder.minion_auto_start,
                                                         proprietary=dict(salt_box_builder.proprietary.items()))

    salt_formatted_box_builder.proprietary.setdefault("os", "linux")
    if "python_alias" not in salt_formatted_box_builder.proprietary:
        salt_formatted_box_builder.proprietary["python_alias"] = "python3"
        if salt_formatted_box_builder.proprietary["os"] == "windows":
            salt_formatted_box_builder.proprietary["python_alias"] = "python"

    master_config = None
    if salt_box_builder.master_build:
        master_config = {}
    if isinstance(salt_box_builder.master_config, Mapping):
        master_config = dict(salt_box_builder.master_config)
    elif isinstance(master_config, str):
        with open(master_config) as master_file:
            master_config = yaml.safe_load(master_file)
    elif isinstance(master_config, FileData):
        master_config = yaml.safe_load(master_config.data)
    if master_config is not None:
        if salt_box_builder.salt_ip is not None:
            master_config["interface"] = salt_formatted_box_builder.salt_ip
        master_config = FileBridge(FileData("master", yaml.dump(master_config)), "/etc/salt/master")
    salt_formatted_box_builder.master_config = master_config

    minion_config = None
    minion_id = None
    if salt_box_builder.minion_build:
        minion_config = {}
    if isinstance(salt_box_builder.minion_config, Mapping):
        minion_config = dict(salt_box_builder.minion_config)
    elif isinstance(minion_config, str):
        with open(minion_config) as minion_file:
            minion_config = yaml.safe_load(minion_file)
    elif isinstance(minion_config, FileData):
        minion_config = yaml.safe_load(minion_config.data)
    if minion_config is not None:
        if salt_box_builder.salt_ip is not None:
            minion_config["master"] = salt_formatted_box_builder.salt_ip
        minion_config = FileBridge(FileData("minion", yaml.dump(minion_config)), "/etc/salt/minion")
        minion_id = FileBridge(FileData("minion_id", tag), "/etc/salt/minion_id")
    salt_formatted_box_builder.minion_config = minion_config

    state_files = []
    for state_bridge in salt_box_builder.state_files:
        if not isinstance(state_bridge, FileBridge):
            state_files.append(FileBridge(state_bridg[0], join("/srv/salt", state_bridge[1])))
        else:
            state_files.append(FileBridge(state_bridge.src, join("/srv/salt", state_bridge.dst)))
    salt_formatted_box_builder.state_files = state_files

    salt_formatted_box_builder.python_packages = [p for p in salt_box_builder.python_packages]

    copies = []
    for file_copy in salt_box_builder.copies:
        if not isinstance(file_copy, FileBridge):
            copies.append(FileBridge(file_copy[0], file_copy[1]))
        else:
            copies.append(file_copy)
    salt_formatted_box_builder.copies = copies

    start_commands = []
    for start_command in salt_formatted_box_builder.start_commands:
        if not isinstance(start_command, Command):
            start_commands.append(Command(start_command))
        else:
            start_commands.append(start_command)
    salt_formatted_box_builder.start_commands = start_commands

    runtime_commands = []
    for runtime_command in salt_formatted_box_builder.runtime_commands:
        if not isinstance(runtime_command, Command):
            start_commands.append(Command(runtime_command))
        else:
            runtime_commands.append(runtime_command)
    salt_formatted_box_builder.runtime_commands = runtime_commands
    box_builder = box.BoxBuilder(salt_formatted_box_builder.tag,
                                 join(working_directory, salt_formatted_box_builder.tag),
                                 proprietary=salt_formatted_box_builder.proprietary)

    files = []
    directories = []
    for c in salt_formatted_box_builder.copies:
        if isinstance(c.src, FileData) or isfile(c.src):
            files.append(c)
        else:
            directories.append(c)

    for c in salt_formatted_box_builder.state_files:
        if isinstance(c.src, FileData) or isfile(c.src):
            files.append(c)
        else:
            directories.append(c)

    if salt_formatted_box_builder.master_config is not None:
        files.append(salt_formatted_box_builder.master_config)
    if salt_formatted_box_builder.minion_config is not None:
        files.append(salt_formatted_box_builder.minion_config)
        files.append(minion_id)

    box_builder.files = files
    box_builder.directories = directories

    commands = salt_formatted_box_builder.commands.copy()
    if salt_formatted_box_builder.salt == "salt":
        commands.append(f"{salt_formatted_box_builder.proprietary['python_alias']} -m pip install salt")
    elif salt_formatted_box_builder.salt == "dev":
        # TODO
        assert False
    else:
        commands.append(f"{salt_formatted_box_builder.proprietary['python_alias']} -m pip install salt=={salt_formatted_box_builder.salt}")
    for package in salt_formatted_box_builder.python_packages:
        commands.append(f"{salt_formatted_box_builder.proprietary['python_alias']} -m pip install {package}")
    box_builder.commands = commands

    ports = set(salt_formatted_box_builder.ports)
    if salt_formatted_box_builder.salt_port is not None:
        ports.add(salt_formatted_box_builder.salt_port)
    box_builder.ports = ports

    if custom_builders is not None and salt_box_builder.box_type in custom_builders:
        build_type = custom_builders[salt_box_builder.box_type]
    elif defaults and salt_box_builder.box_type in DEFAULT_BUILDERS:
        build_type = DEFAULT_BUILDERS[salt_box_builder.box_type]
    else:
        raise SaltBoxException(f"Could not find a builder for {salt_box_builder.box_type}!")
    return salt_formatted_box_builder, \
        partial(build_type(salt_formatted_box_builder, box_builder, tag_id, working_directory), box_builder)
