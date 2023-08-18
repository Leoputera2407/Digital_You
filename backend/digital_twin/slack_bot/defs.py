from enum import Enum
from typing import Collection, Mapping, Sequence, Union, cast


class ChannelType(str, Enum):
    PUBLIC_CHANNEL = "public_channel"
    PRIVATE_CHANNEL = "private_channel"
    DM = "im"
    GROUP_DM = "mpim"


BLOCK_TYPE = Mapping[str, bool | Collection[str | Collection[str]]]
VIEW_TYPE = Mapping[str, Union[str, BLOCK_TYPE, Sequence[BLOCK_TYPE]]]
