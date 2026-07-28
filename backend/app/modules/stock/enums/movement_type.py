from enum import Enum


class MovementType(str, Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"

    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"

    ADJUSTMENT = "ADJUSTMENT"
