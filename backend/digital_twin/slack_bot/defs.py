from enum import Enum

class ChannelType(str, Enum):
    PUBLIC_CHANNEL = "public_channel"
    PRIVATE_CHANNEL = "private_channel"
    DM = "im"
    GROUP_DM = "mpim"