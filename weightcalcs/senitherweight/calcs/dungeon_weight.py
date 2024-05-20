import math
from senitherweight.constants import dungeon_weights, dungeons_level50_experience
from senitherweight.utils import get_cata_lvl


def dungeon_weight(weight_type: str, level: int, experience: int, with_overflow: bool = True):
    """Calculates the dungeon weight of a specific thing.

    Parameters
    -----------
    weight_type: str
        The type of dungeon weight to calculate, can be one of the following:
        - catacombs
        - healer
        - mage
        - berserk
        - archer
        - tank

    level: int
        The level of the dungeon type.

    experience: int
        The experience of the dungeon type.

    with_overflow: bool
        Whether or not to include the overflow weight in the calculation.

    Returns
    -------
    float
        The amount of weight from catacombs.

    Example
    -------
    >>> dungeon_weight('catacombs', 0, 0)
    >>> 0.0
    """

    percentage_modifier = dungeon_weights[weight_type]

    # Calculates the base weight using the players level
    base = math.pow(level, 4.5) * percentage_modifier

    # If the dungeon XP is below the requirements for a level 50 dungeon we'll
    # just return our weight right away.
    if experience <= dungeons_level50_experience:
        return base

    # Calculates the XP above the level 50 requirement, and the splitter
    # value, weight given past level 50 is given at 1/4 the rate.
    remaining = experience - dungeons_level50_experience
    splitter = (4 * dungeons_level50_experience) / base

    # Calculates the dungeon overflow weight and returns it to the weight object builder.
    return math.floor(base) + math.pow(remaining / splitter, 0.968) if with_overflow else math.floor(base)


def total_dungeon_weight(player_classes: dict, catacombs_xp: int, with_overflow: bool = True):
    """Calculates the dungeon weight of the player.

    Parameters
    -----------
    player_classes: dict
        The players class levels.

    catacombs_xp: int
        The players catacombs experience.

    with_overflow: bool
        Whether or not to include the overflow weight in the calculation.

    Returns
    -------
    float
        The amount of weight from dungeons.

    Example
    -------
    >>> total_dungeon_weight({'healer': 0, 'mage': 0, 'berserk': 0, 'archer': 0, 'tank': 0}, 0)
    >>> 0.0
    """

    catacombs_level = get_cata_lvl(catacombs_xp)
    return sum(
        dungeon_weight(cls_data, get_cata_lvl(exp.get("experience", 0)), exp.get("experience", 0), with_overflow)
        for cls_data, exp in player_classes.items()
    ) + dungeon_weight("catacombs", catacombs_level, catacombs_xp, with_overflow)
