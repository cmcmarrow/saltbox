from typing import Dict, Iterable, Tuple
from saltbox import saltbox
from saltbox import error
import tempfile
from time import sleep


class Orchestration:
    def __init__(self, salt_boxs: Iterable[Tuple[int, saltbox.SaltBoxBuilder]]):
        self._working_dir = tempfile.TemporaryDirectory()
        self._salt_boxs: Dict[str, saltbox.SaltBox] = {}
        self._open = True
        running_minions = set()
        for count, builder in salt_boxs:
            for tag_id in range(1, count + 1):
                if count == 1:
                    tag_id = None
                salt_box = saltbox.SaltBox(builder, tag_id, self._working_dir.name, False)
                salt_box_name = salt_box.box_builder().tag
                fsalt_builder = salt_box.formatted_box_builder()
                if fsalt_builder.minion_build and fsalt_builder.minion_auto_start:
                    running_minions.add(salt_box.box_builder().tag)
                if salt_box_name in self._salt_boxs:
                    raise error.SaltBoxException(f"Tag collection: {repr(salt_box_name)}!")
                self._salt_boxs[salt_box_name] = salt_box
        masters = self.masters()
        if len(masters) == 1:
            master_box = masters[next(iter(masters))]
            for _ in range(24):
                master_box.run("salt-key -A -y")
                ret = master_box.run("salt '*' test.ping --summary")
                if "minions with errors: 0" in ret.output:
                    for minion in running_minions:
                        if minion + ":" not in ret.output.split():
                            break
                    else:
                        break
                    sleep(5)
            else:
                raise error.SaltBoxException("Could not connect all minions!")
        for _, b in self._salt_boxs.items():
            for command in b.formatted_box_builder().runtime_commands:
                b.run(command.command, command.detach)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    def __len__(self):
        return len(self._salt_boxs)

    def __contains__(self, item):
        return item in self._salt_boxs

    def __iter__(self):
        return iter(self._salt_boxs)

    def __getitem__(self, item):
        return self._salt_boxs[item]

    def is_open(self) -> bool:
        return self._open

    def close(self):
        if self._open:
            self._open = False
            for _, salt_box in self._salt_boxs.items():
                salt_box.close()
            self._working_dir.cleanup()

    def masters(self):
        return {key: b for key, b in self._salt_boxs.items() if b.formatted_box_builder().master_build}

    def minions(self):
        return {key: b for key, b in self._salt_boxs.items() if b.formatted_box_builder().minion_build}
