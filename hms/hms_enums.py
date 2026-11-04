from enum import Enum


class MessageType(str, Enum):
    REQUEST = "REQUEST"
    STATUS = "STATUS"
    INVENTORY = "INVENTORY"


class Status(str, Enum):
    OK = "OK"
    FAULT = "FAULT"
    SUSPECT = "SUSPECT"
    OFFLINE = "OFFLINE"
