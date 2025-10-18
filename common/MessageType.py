from enum import Enum

class MessageType(Enum):
    PROPOSE = "PROPOSE"
    VOTE = "VOTE"
    ECHO = "ECHO"