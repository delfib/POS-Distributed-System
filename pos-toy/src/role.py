from enum import Enum

class Role(Enum):
    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    DOWN = "down"
