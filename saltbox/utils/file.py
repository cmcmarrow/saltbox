from pathlib import Path
from typing import Optional, Union
from os.path import join
from os.path import basename as os_basename
from shutil import copy2, copytree
from dataclasses import dataclass


@dataclass
class FileData:
    name: str
    data: Union[bytes, str]


@dataclass
class FileBridge:
    src: Union[str, FileData]
    dst: str


def full_path(path: str,
              name: Optional[str] = None,
              extension: Optional[str] = None) -> Union[bytes, str]:
    if name is not None:
        if extension is not None:
            name = f"{name}.{extension}"
        path = join(path, name)
    return path


def make(data: Union[bytes, str, FileData],
         path: str,
         name: Optional[str] = None,
         extension: Optional[str] = None):
    path = full_path(path, name, extension)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, FileData):
        data = data.data
    mode = "w"
    if isinstance(data, bytes):
        mode = "wb"
    with open(path, mode=mode) as file:
        file.write(data)


def copy(path: Union[str, FileData],
         dst_path: str,
         name: Optional[str] = None,
         extension: Optional[str] = None,
         dst_name: Optional[str] = None,
         dst_extension: Optional[str] = None):
    dst = full_path(dst_path, dst_name, dst_extension)
    if isinstance(path, FileData):
        make(path, dst_path, dst_name, dst_extension)
    else:
        src = full_path(path, name, extension)
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        copy2(src, dst, follow_symlinks=False)


def copy_dir(path: str,
             dst_path: str,
             name: Optional[str] = None,
             dst_name: Optional[str] = None):
    if name is not None:
        path = join(path, name)
    if dst_name is not None:
        dst_path = join(dst_path, dst_name)
    copytree(path, dst_path, dirs_exist_ok=True)


def basename(path: Union[str, FileData]) -> str:
    if isinstance(path, str):
        return os_basename(path)
    return path.name
