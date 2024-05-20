import math
from senitherweight.constants import slayer_weights


def slayer_weight(weight_type: str, experience: int, with_overflow: bool = True):
    """Calculates the slayer weight of the player.

    Parameters
    -----------
    weight_type: str
        The type of slayer weight to calculate, can be one of the following:
        - spider
        - zombie
        - wolf
        - enderman
        - blaze

    experience: int
        The experience of the slayer type.

    with_overflow: bool
        Whether or not to include the overflow weight in the calculation.

    Returns
    -------
    float
        The amount of weight from slayer.

    Example
    -------
    >>> slayer_weight('zombie', 0)
    >>> 0.0
     """
    
    if weight_type in ["blaze", "vampire"]:
        return 0
    
    _slayer_weight = slayer_weights.get(weight_type)
    if not _slayer_weight:
        return 0

    if experience <= 1000000:
        return 0 if experience <= 0 else experience / _slayer_weight["divider"]

    base = 1000000 / _slayer_weight["divider"]
    remaining = experience - 1000000

    modifier = _slayer_weight["modifier"]
    overflow = 0

    while remaining > 0:
        left = min(remaining, 1000000)

        overflow += math.pow(left / (_slayer_weight["divider"] * (1.5 + modifier)), 0.942)
        modifier += _slayer_weight["modifier"]
        remaining -= left

    return base + overflow if with_overflow else base


def total_slayer_weight(slayer_bosses: dict, with_overflow: bool = True):
    """Calculates the slayer weight of the player.

    Parameters
    -----------
    slayer_bosses: dict
        A dictionary containing the experience of each slayer.
        With slayer type as key and experience as value in another dict with as key xp.


    with_overflow: bool
        Whether or not to include the overflow weight in the calculation.

    Returns
    -------
    float
        The amount of weight from slayer.

    Example
    -------
    >>> total_slayer_weight(
    >>>    {'zombie': {'xp':0}, 'spider': {'xp':0}, 'wolf': {'xp':0}, 'enderman': {'xp':0}, 'blaze': {'xp':0}}
    >>> )
    >>> 0.0

    """
    return sum(
        slayer_weight(slayer_type, slayer_bosses.get(slayer_type, {}).get("xp", 0), with_overflow)
        for slayer_type in slayer_weights.keys()
    )
