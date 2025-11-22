from enum import Enum


class MomStatusEnum(str, Enum):
    pregnant = "pregnant"
    new_mom = "new_mom"
    toddler_mom = "toddler_mom"
    mixed = "mixed"