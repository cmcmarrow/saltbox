import sys
from typing import Optional
from saltbox.saltbox import SaltBoxBuilder
from saltbox.orchestration import Orchestration
from pprint import pprint


def run(build_command: Optional[str] = None):
    if build_command is None:
        build_command = sys.argv[1:]
    else:
        build_command = build_command.split(" ")
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
        while True:
            command = input(">>> ").split(" ")
            if command:
                if command[0] == "exit":
                    break
                if command[0] == "ls":
                    pprint(list(o))
                else:
                    box_name = command[0]
                    command = " ".join(command)
                    if box_name in o:
                        print(o[box_name].run(command).output)
                    else:
                        print("Cant find box!")
