from typing import Optional, Type
from saltbox.boxs import box, dockerbox
from saltbox.utils import package


def builder(salt_formatted_box_builder: "SaltFormattedBoxBuilder",
            box_builder: box.BoxBuilder,
            tag_id: Optional[int] = None,
            working_directory: Optional[str] = None, ) -> Type[box.Box]:
    if "from" not in salt_formatted_box_builder.proprietary:
        python_version = package.get_salt_python_version(salt_formatted_box_builder.salt)
        salt_formatted_box_builder.proprietary["from"] = f"python:{python_version}"
    return dockerbox.DockerBox
