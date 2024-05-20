import aiohttp

from .calcs.dungeon_weight import total_dungeon_weight
from .calcs.skill_weight import total_skill_weight
from .calcs.slayer_weight import total_slayer_weight

from .utils import get_profile, get_uuid

from .constants import skill_weight_groups


class SenitherWeight:
    def __init__(self, api_key: str, session: aiohttp.ClientSession = None):
        self.api_key = api_key
        self.session = session

    @staticmethod
    def get_weight_raw(
            skill_experience_dict: dict, player_classes: dict, catacombs_xp: int, slayer_bosses: dict,
            with_overflow: bool = True
    ) -> dict:
        skill_weight = total_skill_weight(skill_experience_dict, with_overflow)
        dungeon_weight = total_dungeon_weight(player_classes, catacombs_xp, with_overflow)
        slayer_weight = total_slayer_weight(slayer_bosses, with_overflow)
        return {
            "total": skill_weight + dungeon_weight + slayer_weight,
            "skill_weight": skill_weight,
            "dungeon_weight": dungeon_weight,
            "slayer_weight": slayer_weight
        }

    async def get_weight(self, uuid: str, profile: str = None) -> dict:
        """Calculates the dungeon completion weight of the player.

        Parameters
        -----------
        uuid: str
            The uuid of the player.

        profile: Optional[str]
            The profile name of the player. If not provided the profile with the latest save date will be used.

        Returns
        -------
        dict
            A dictionary containing weight

        Example
        -------
        >>> get_weight('bf8794f505124d7da30ae238a1efb4c2', 'Mango')
        """
        # Get the player profile data from the hypixel api
        if not self.session:
            self.session = aiohttp.ClientSession()

        profile = await get_profile(uuid, self.api_key, self.session, profile)

        # Catacombs XP
        try:
            cata_xp = profile["dungeons"]["dungeon_types"]["catacombs"]["experience"]
        except:
            cata_xp = 0

        # Skills
        skill_experience_dict = {}
        if profile:
            for skill_type in skill_weight_groups:
                experience = profile.get(f"experience_skill_{skill_type}", 0)  # Get the experience of the skill
                skill_experience_dict[skill_type] = experience  # Add the experience to the experience skill dict

        return self.get_weight_raw(
            skill_experience_dict, profile.get("dungeons", {}).get("player_classes", {}), cata_xp,
            profile.get("slayer_bosses"),
        )

    async def get_weight_from_uuid(self, uuid: str, profile: str = None) -> dict:
        """Calculates the dungeon completion weight of the player.

        Parameters
        -----------
        uuid: str
            The uuid of the player.

        profile: Optional[str]
            The profile name of the player. If not provided the profile with the latest save date will be used.

        Returns
        -------
        dict
            A dictionary containing weight

        Example
        -------
        >>> get_weight_from_uuid('bf8794f505124d7da30ae238a1efb4c2', 'Mango')
        """
        return await self.get_weight(uuid, profile)

    async def get_weight_from_name(self, name: str, profile: str = None) -> dict:
        """Calculates the dungeon completion weight of the player.

        Parameters
        -----------
        name: str
            The name of the player.

        profile: Optional[str]
            The profile name of the player. If not provided the profile with the latest save date will be used.

        Returns
        -------
        dict
            A dictionary containing weight

        Example
        -------
        >>> get_weight_from_uuid('timnoot', 'Mango')
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        uuid = await get_uuid(name, self.session)
        return await self.get_weight(uuid, profile)
