from dataclasses import dataclass


@dataclass
class CopybookField:
    level: str
    field_name: str
    pic: str
    usage: str
    type: str
    length: int
    decimals: int
    signed: bool
    occurs: int = 1
    redefines: str = ""
