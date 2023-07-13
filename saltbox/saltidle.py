import sys
from typing import Optional, Union
from saltbox.saltbox import SaltBoxBuilder
from saltbox.orchestration import Orchestration
from pprint import pprint


def run(orchestration: Optional[Union[Orchestration, str]] = None):
    if isinstance(orchestration, Orchestration):
        _shell(orchestration)
    else:
        if orchestration is None:
            build_command = sys.argv[1:]
        else:
            build_command = orchestration.split(" ")
        build_command.reverse()
        boxs = [(1, SaltBoxBuilder("docker",
                                   "build",
                                   master_build=True,
                                   minion_build=True,
                                   salt=build_command.pop()))]
        i = 1
        while build_command:
            salt = build_command.pop()
            count = build_command.pop()
            boxs.append((int(count), SaltBoxBuilder("docker",
                                                    f"m{i}",
                                                    master_build=False,
                                                    minion_build=True,
                                                    salt=salt)))
            i += 1

        with Orchestration(boxs) as o:
            _shell(o)


def _shell(o: Orchestration):
    while True:
        command = input(">>> ").split(" ")
        if command:
            if command[0] == "exit":
                break
            if command[0] == "ls":
                pprint(list(o))
            else:
                box_name = command[0]
                command = " ".join(command[1:])
                if box_name in o:
                    print(o[box_name].run(command).output)
                else:
                    print("Cant find box!")
