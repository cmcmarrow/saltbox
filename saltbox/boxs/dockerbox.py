from . import box
from saltbox.utils import file
from saltbox import error
from logging import getLogger

LOG = getLogger("salt-box")

try:
    import docker
    HAS_DOCKER = True
except ImportError:
    LOG.warning("Missing docker import!")
    HAS_DOCKER = False


class DockerBox(box.Box):
    def __init__(self, box_builder: box.BoxBuilder):
        self._container = None
        self._image = None
        super().__init__(box_builder)
        if not HAS_DOCKER:
            raise ImportError("Missing docker import!")
        LOG.debug("Docker: Making DockerFile.")
        docker_file = [f"FROM {box_builder.proprietary['from']}"]
        for port in box_builder.ports:
            docker_file.append(f"EXPOSE {port}")
        file_object_id = 1
        for bridge in box_builder.files:
            new_src = f"{file_object_id}_{file.basename(bridge.src)}"
            file_object_id += 1
            file.copy(bridge.src, file.full_path(box_builder.working_directory, new_src))
            docker_file.append(f"COPY {new_src} {bridge.dst}")
        for bridge in box_builder.directories:
            new_src = f"{file_object_id}_{file.basename(bridge.src)}"
            file_object_id += 1
            file.copy_dir(bridge.src, file.full_path(box_builder.working_directory, new_src))
            docker_file.append(f"COPY {new_src} {bridge.dst}")
        for command in box_builder.commands:
            docker_file.append(f"RUN {command}")
        file.make("\n".join(docker_file) + "\n", box_builder.working_directory, "Dockerfile")
        LOG.debug(f"Docker: Making Image {repr(box_builder.tag)}.")
        docker_env = docker.from_env()
        self._image = docker_env.images.build(path=box_builder.working_directory, tag=box_builder.tag)
        # TODO while ture sleep 86400
        LOG.debug(f"Docker: Starting Container {repr(box_builder.tag)}.")
        self._container = docker_env.containers.run(box_builder.tag, command="sleep 86400", network="host", detach=True)

    def close(self):
        if self.is_open():
            if self._container is not None:
                try:
                    LOG.debug(f"Docker: Stopping Container {repr(self._box_builder.tag)}.")
                    self._container.kill()
                except docker.errors.APIError:
                    pass
            if self._image is not None:
                LOG.debug(f"Docker: Cleaning Up Image {repr(self._box_builder.tag)}.")
                docker_env = docker.from_env()
                docker_env.images.remove(self._box_builder.tag, force=True)
        super().close()

    def run(self, command: str, detach: bool = False, encoding: str = "utf-8", hard_fail: bool = False):
        LOG.debug(f"Docker: Running command {repr(command)}")
        try:
            ret = self._container.exec_run(command, detach=detach)
            if detach is True:
                return
            output = ret.output
            exit_code = ret.exit_code
        except (docker.errors.APIError,) as e:
            if hard_fail:
                raise error.SaltBoxException(e)
            if detach is True:
                return
            if encoding is None:
                output = bytes(str(e), encoding="utf-8")
            else:
                output = bytes(str(e), encoding=encoding)
            exit_code = 0
        if encoding is not None:
            output = str(output, encoding)
        return box.CommandReturn(output, exit_code)
