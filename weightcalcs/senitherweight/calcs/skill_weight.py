import math
from senitherweight.constants import skill_weights, skills_level60_experience, skills_level50_experience, \
    skill_weight_groups
from senitherweight.utils import get_skill_lvl


def skill_weight(weight_type: str, level: int, experience: int, with_overflow: bool = True):
    """Calculates the skill weight of a specific skill.

    Parameters
    -----------
    weight_type: str
        The type of skill weight to calculate, can be one of the following:
        - mining
        - combat
        - foraging
        - fishing
        - enchanting
        - alchemy
        - taming
        - farming
        - carpentry
        - runecrafting

    level: int
        The level of the skill type.

    experience: int
        The experience of the skill type.

    with_overflow: bool
        Whether or not to include the overflow weight in the calculation.

    Returns
    -------
    float
        The amount of weight from skill.

    Example
    -------
    >>> skill_weight('mining', 0, 0)
    >>> 0.0
    """
    _skill_weight = skill_weights.get(weight_type)
    if not _skill_weight or _skill_weight["divider"] == 0 or _skill_weight["exponent"] == 0:
        return 0

    # Gets the XP required to max out the skill.
    max_skill_level_xp = skills_level60_experience if _skill_weight["maxLevel"] == 60 else skills_level50_experience

    # Calculates the base weight using the players level, if the players level
    # is 50/60 we'll round off their weight to get a nicer looking number.
    base = math.pow(level * 10, 0.5 + _skill_weight["exponent"] + level / 100) / 1250
    if experience > max_skill_level_xp:
        base = round(base)

    # If the skill XP is below the requirements for a level 50/60 skill we'll
    # just return our weight to the weight object builder right away.
    if experience <= max_skill_level_xp:
        return base

    # Calculates the skill overflow weight and returns it to the weight object builder.
    return base + math.pow((experience - max_skill_level_xp) / _skill_weight["divider"], 0.968) if with_overflow \
        else base


def total_skill_weight(skill_experience_dict: dict, with_overflow: bool = True):
    """Calculates the skill weight of the player.

    Parameters
    -----------
    skill_experience_dict: dict
        A dictionary containing the experience of each skill.
        With skill type as key and experience as value.

    with_overflow: bool
        Whether or not to include the overflow weight in the calculation.

    Returns
    -------
    float
        The total amount of weight from skills.
    """
    total_weight = 0
    for skill_type, experience in skill_experience_dict.items():
        if skill_type not in skill_weight_groups:
            continue

        total_weight += skill_weight(skill_type, get_skill_lvl(skill_type, experience), experience, with_overflow)

    return total_weight
