import discord
from discord.ext import tasks
from discord.ui import View, select, button

from skyblockparser.profile import SkyblockParser, Profile, Pet
from skyblockparser.constants import pet_levels, rarity_offset
from skyblockparser.levels import revenant, spider, sven, enderman, blaze, vampire

from numerize.numerize import numerize
from datetime import datetime

from util.profile_autocomplete import gamemode_to_emoji, gamemode_to_gamemode, gamemode_to_emoji_autocomplete
from .embed import generate_embed_networth_field
from .formatting import count
from .hotm import get_hotm_emojis
from .timeout import timeout_view
from .embed import get_embed
from .progress import get_progress_bar
from .profile_autocomplete import get_uuid
from .cache_util import get_data_from_cache
from .footer import get_footer
from constants import (HOTM_TREE_MAPPING, HOTM_TREE_EMOJIS, 
                       SPECIAL_HOTM_TYPES, RARITY_EMOJIS, 
                       RARITY_ORDER, RIFT_EMOJIS,
                       TIMECHARM_NAMES, TIMECHARM_ORDER,
                       HYPIXEL_API_KEY, SLAYER_NAMES,
                       SLAYER_EMOJIS, MEDAL_DATA)



class NetworthProfileSelector(View):
    def __init__(self, user_id, username, bot, parser: SkyblockParser, selected_profile_cutename, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.bot = bot
        self.interaction = interaction

        self.profiles = parser.get_profiles()
        self.emojis = bot.emojis
        self.selected_cutename = selected_profile_cutename
        self.embed_cutename = selected_profile_cutename
        self.user_id = user_id

        options = []
        for profile in self.profiles:
            _profile = parser.select_profile(profile)
            profile_type = _profile.profile_type

            emoji = getattr(self.emojis, profile.lower())
            if profile == selected_profile_cutename:
                options.append(discord.SelectOption(
                    label=profile, value=profile, emoji=emoji, default=True, description=gamemode_to_gamemode(profile_type)))
                continue

            options.append(discord.SelectOption(
                label=profile, value=profile, emoji=emoji, description=gamemode_to_gamemode(profile_type)))

        self.children[0].options = options

        self.counter = 0
        self.trigger_timeout.start()
        self.username = username
        self.soulbound = None

    @tasks.loop(seconds=180)
    async def trigger_timeout(self):
        await timeout_view(self)

    async def create_embed(self):

        profile_data = await get_data_from_cache(self)

        networth = profile_data.networth_data
        embed = discord.Embed(color=discord.Color.blue(
        ), url=f"https://sky.noemt.dev/stats/{profile_data.uuid}/{profile_data.cute_name.replace(' ','%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{profile_data.uuid}/left")

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        networth_total = networth.get("networth", 0)
        unsoulbound_total = networth.get("unsoulboundNetworth", 0)

        if self.soulbound is True:
            embed.title = f"{formatted_username} Soulbound Networth on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"
            embed.description = f"Networth: **{format(int(networth_total-unsoulbound_total), ',d')}** (**{numerize(networth_total-unsoulbound_total)}**)"

        elif self.soulbound is False:
            embed.title = f"{formatted_username} Unsoulbound Networth on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"
            embed.description = f"Networth: **{format(int(unsoulbound_total), ',d')}** (**{numerize(unsoulbound_total)}**)"

        else:
            embed.title = f"{formatted_username} Networth on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"
            embed.description = f"Networth: **{format(int(networth_total), ',d')}** (**{numerize(networth_total)}**)"

        purse = networth.get("purse", 0)
        bank = networth.get("bank", 0)

        networth_types = networth.get("types")
        if not networth_types:
            networth_types = {}

        sacks = networth_types.get("sacks", 0)
        essence = networth_types.get("essence", 0)

        if self.soulbound is True:
            embed.add_field(
                name=f"{self.emojis.gold_ingot} Coins",
                value="`Not Soulbound`",
            )

            embed.add_field(
                name=f"{self.emojis.sacks} Sacks",
                value="`Not Soulbound`",
            )

            embed.add_field(
                name=f"{self.emojis.wither_essence} Essence",
                value="`Not Soulbound`",
            )

        else:
            embed.add_field(
                name=f"{self.emojis.gold_ingot} Coins",
                value=numerize(purse + bank),
            )

            embed.add_field(
                name=f"{self.emojis.sacks} Sacks",
                value=numerize(sacks["total"]),
            )

            embed.add_field(
                name=f"{self.emojis.wither_essence} Essence",
                value=numerize(essence["total"]),
            )

        item_categories = {"armor": ["equipment", "wardrobe", "armor"],
                           "items": ["inventory", "enderchest", "storage", "personal_vault"],
                           "pets": ["pets"],
                           "accessories": ["accessories"],
                           "museum": ["museum"]}

        # possible types: "armor", "equipment", "wardrobe", "inventory", "enderchest", "storage", "personal_vault", "pets", "museum", "fishing_bag", "potion_bag", "candy_inventory", "essence", "sacks"

        item_emojis = {
            "armor": self.emojis.equipment,
            "items": self.emojis.chest,
            "pets": self.emojis.pets,
            "accessories": self.emojis.talismans,
            "museum": "🏛️"
        }

        for category, items in item_categories.items():
            total_value = 0
            _items = []
            emoji = item_emojis[category]

            for _type in items:
                type_data = networth_types[_type]
                type_items = type_data.get("items", [])

                if self.soulbound is True:
                    total_value += type_data.get("total", 0) - \
                        type_data.get("unsoulboundTotal", 0)
                    for item in type_items:
                        if item.get("soulbound", False):
                            _items.append(item)

                elif self.soulbound is False:
                    total_value += type_data.get("unsoulboundTotal", 0)
                    for item in type_items:
                        if not item.get("soulbound", False):
                            _items.append(item)

                elif self.soulbound is None:
                    total_value += type_data.get("total", 0)
                    _items += type_items

            field = generate_embed_networth_field(
                _items, total_value, category.replace("_", " ").title(), emoji, self.emojis, self.bot.item_emojis)

            if field:
                embed.add_field(**field)

        embed.set_footer(
            text=get_footer("nom")
        )

        return embed

    @select(row=0)
    async def select_profile(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.defer()

        for option in select.options:
            option.default = False
            if option.value == select.values[0]:
                option.default = True

        self.embed_cutename = select.values[0]
        embed = await self.create_embed()
        
        if interaction.user.id != self.user_id:
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            await interaction.edit_original_response(embed=embed, view=self)


    @select(
        custom_id="item_type_switcher",
        options=[
            discord.SelectOption(label="All", value="normal", emoji="<:bankitem:1236756044588253184>"),
            discord.SelectOption(
                label="Soulbound", value="soulbound", emoji="❌"),
            discord.SelectOption(label="Unsoulbound", value="unsoulbound",
                                 emoji="<:gold_ingot:1236755670628307017>"),
        ],
        placeholder="Select the Type of Items to Display.",
    )
    async def switch_item_type(self, select: discord.ui.Select, interaction: discord.Interaction):

        if not self.user_id == interaction.user.id:
            return await interaction.response.defer()
        
        if select.values[0] == "soulbound":
            self.soulbound = True

        elif select.values[0] == "unsoulbound":
            self.soulbound = False

        else:
            self.soulbound = None

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        

    @button(label="View Breakdown", style=discord.ButtonStyle.grey)
    async def view_breakdown(self, button: discord.ui.Button, interaction: discord.Interaction):
        profile_data = await get_data_from_cache(self)

        interaction = await interaction.response.send_message(content="\u200b", ephemeral=True)
        view = TypeSwitcherView(self.bot, profile_data,
                                self.username, self.soulbound, interaction)
        
        embed = await view.create_embed()

        await interaction.edit_original_response(content=None, embed=embed, view=view)

class TypeSwitcherView(View):
    def __init__(self, bot, profile: Profile, username, soulbound, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.profile = profile
        self.uuid = profile.uuid
        self.cute_name = profile.cute_name
        self.soulbound = soulbound
        self.category = "armor"
        self.username = username
        self.counter = 0
        self.trigger_timeout.start()
        self.interaction = interaction

    @tasks.loop(seconds=180)
    async def trigger_timeout(self):
        await timeout_view(self)


    async def create_embed(self):

        item_categories = {"armor": ["equipment", "wardrobe", "armor"],
                           "items": ["inventory", "enderchest", "storage", "personal_vault"],
                           "pets": ["pets"],
                           "accessories": ["accessories"],
                           "museum": ["museum"]}

        # possible types: "armor", "equipment", "wardrobe", "inventory", "enderchest", "storage", "personal_vault", "pets", "museum", "fishing_bag", "potion_bag", "candy_inventory", "essence", "sacks"

        item_emojis = {
            "armor": self.bot.emojis.equipment,
            "items": self.bot.emojis.chest,
            "pets": self.bot.emojis.pets,
            "accessories": self.bot.emojis.talismans,
            "museum": "🏛️"
        }

        await self.bot.handle_data(self.profile.uuid, self.profile, self.username)

        networth = self.profile.networth_data
        networth_types = networth.get("types")
        if not networth_types:
            networth_types = {}

        total_value = 0
        _items = []
        emoji = item_emojis[self.category]

        _networth_types = item_categories[self.category]
        for _type in _networth_types:

            type_data = networth_types[_type]
            type_items = type_data.get("items", [])

            if self.soulbound is True:
                total_value += type_data.get("total", 0) - \
                    type_data.get("unsoulboundTotal", 0)
                for item in type_items:
                    if item.get("soulbound", False):
                        _items.append(item)

            elif self.soulbound is False:
                total_value += type_data.get("unsoulboundTotal", 0)
                for item in type_items:
                    if not item.get("soulbound", False):
                        _items.append(item)

            elif self.soulbound is None:
                total_value += type_data.get("total", 0)
                _items += type_items

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        profile_type = self.profile.profile_type
        profile_type = gamemode_to_emoji(profile_type)

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        embed = discord.Embed(color=discord.Color.blue(
        ), url=f"https://sky.noemt.dev/stats/{self.uuid}/{self.cute_name.replace(' ', '%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{self.uuid}/left")

        if self.soulbound is True:
            embed.title = f"{formatted_username} Soulbound {self.category.title()} {emoji} on {self.cute_name}{suffix}{getattr(self.bot.emojis, self.cute_name.lower())}"
            embed.description = f"Value: **{format(int(total_value), ',d')}** (**{numerize(total_value)}**)\n"

        elif self.soulbound is False:
            embed.title = f"{formatted_username} Unsoulbound {self.category.title()} {emoji} on {self.cute_name}{suffix}{getattr(self.bot.emojis, self.cute_name.lower())}"
            embed.description = f"Value: **{format(int(total_value), ',d')}** (**{numerize(total_value)}**)\n"

        else:
            embed.title = f"{formatted_username} {self.category.title()} {emoji} on {self.cute_name}{suffix}{getattr(self.bot.emojis, self.cute_name.lower())}"
            embed.description = f"Value: **{format(int(total_value), ',d')}** (**{numerize(total_value)}**)\n"

        items_string = "\n"
        for item in enumerate(_items):
            if item[0] == 25:
                items_string += f"... **{len(_items) - 25} more**"
                break

            super_suffix = None
            suffix = ""
            for calc in item[1]["calculation"]:
                if calc["id"] == "RECOMBOBULATOR_3000":
                    suffix += " "+self.bot.emojis.recombobulator_3000


            item_emoji = self.bot.item_emojis.get(item[1]["id"].upper())
            if not item_emoji:
                if item[1]["id"].startswith("starred_"):
                    item[1]["id"] = item[1]["id"][8:]
                    item_emoji = self.bot.item_emojis.get(item[1]["id"].upper())

            if item[1].get("type"):
                if item[1].get("skin") is None:
                    item_emoji = self.bot.item_emojis.get("PET_"+item[1]["type"].upper())

                else:
                    item_emoji = self.bot.item_emojis.get("PET_SKIN_"+item[1].get("skin").upper())

                if item[1].get("heldItem"):
                    supersuffix_emoji = self.bot.item_emojis.get(item[1].get("heldItem").upper())
                    emoji_url = supersuffix_emoji["url"]
                    emoji_id = supersuffix_emoji["id"]
                    emoji_name = supersuffix_emoji["name"]

                    if ".gif" in emoji_url:
                        emoji_prefix = "<a:"
                    
                    else:
                        emoji_prefix = "<:"

                    held_item_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}>"
                    super_suffix = f"{held_item_emoji}"


            if item_emoji:
                emoji_url = item_emoji["url"]
                emoji_id = item_emoji["id"]
                emoji_name = item_emoji["name"]

                if ".gif" in emoji_url:
                    emoji_prefix = "<a:"
                
                else:
                    emoji_prefix = "<:"

                item_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}> "

            else:
                if "_skinned_" in item[1]["id"]:
                    item_emoji_name = item[1]["id"].split("_skinned_")[1]
                    item_emoji = self.bot.item_emojis.get(item_emoji_name.upper())
                    if item_emoji:
                        emoji_url = item_emoji["url"]
                        emoji_id = item_emoji["id"]
                        emoji_name = item_emoji["name"]

                        if ".gif" in emoji_url:
                            emoji_prefix = "<a:"
                        
                        else:
                            emoji_prefix = "<:"

                        item_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}> "
                    
                    else:
                        print(item[1]["id"])
                        item_emoji = ""

                else:
                    print(item[1]["id"])
                    item_emoji = ""

            items_string += f"↳ {item_emoji}{count(item[1], super_suffix)}{suffix} (**{numerize(item[1]['price'])}**)\n"

        embed.description += items_string

        embed.set_footer(
            text=get_footer("nom")
        )
        
        return embed

    @select(
        custom_id="category_switcher",
        options=[
            discord.SelectOption(label="Armor", value="armor", emoji="<:armor:1238171181249466398>"),
            discord.SelectOption(label="Items", value="items",
                                 emoji="<:chest:1236755795505451059>"),
            discord.SelectOption(label="Pets", value="pets",
                                 emoji="<:pets:1236755498657910864>"),
            discord.SelectOption(label="Accessories", value="accessories",
                                 emoji="<:talismans:1236755177818816702>"),
            discord.SelectOption(label="Museum", value="museum", emoji="🏛️"),
        ],
        row=0,
        placeholder="Select the Category of Items to Display.",
    )
    async def switch_category(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.category = select.values[0]

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @select(
        custom_id="item_type_switcher",
        options=[
            discord.SelectOption(label="All", value="normal",
                                 emoji="<:bankitem:1236756044588253184>"),
            discord.SelectOption(
                label="Soulbound", value="soulbound", emoji="❌"),
            discord.SelectOption(label="Unsoulbound", value="unsoulbound",
                                 emoji="<:gold_ingot:1236755670628307017>"),
        ],
        row=1,
        placeholder="Select the Type of Items to Display.",
    )
    async def switch_item_type(self, select: discord.ui.Select, interaction: discord.Interaction):
        if select.values[0] == "soulbound":
            self.soulbound = True

        elif select.values[0] == "unsoulbound":
            self.soulbound = False

        else:
            self.soulbound = None

        for option in select.options:
            option.default = False
            if option.value == select.values[0]:
                option.default = True

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)


class ProfileCommandProfileSelector(discord.ui.View):
    def __init__(self, user_id, username, bot, parser: SkyblockParser, selected_profile_cutename, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.bot = bot
        self.interaction = interaction

        self.profiles = parser.get_profiles()
        self.emojis = bot.emojis
        self.selected_cutename = selected_profile_cutename
        self.embed_cutename = selected_profile_cutename
        self.user_id = user_id

        options = []
        for profile in self.profiles:
            _profile = parser.select_profile(profile)
            profile_type = _profile.profile_type

            emoji = getattr(self.emojis, profile.lower())
            if profile == selected_profile_cutename:
                options.append(discord.SelectOption(
                    label=profile, value=profile, emoji=emoji, default=True, description=gamemode_to_gamemode(profile_type)))
                continue

            options.append(discord.SelectOption(
                label=profile, value=profile, emoji=emoji, description=gamemode_to_gamemode(profile_type)))

        self.children[0].options = options

        self.counter = 0
        self.trigger_timeout.start()
        self.username = username
        self.soulbound = None

    @tasks.loop(seconds=180)
    async def trigger_timeout(self):
        await timeout_view(self)

    async def create_embed(self):

        profile_data = await get_data_from_cache(self)

        networth = profile_data.networth_data
        embed = discord.Embed(color=discord.Color.blue(
        ), url=f"https://sky.noemt.dev/stats/{profile_data.uuid}/{profile_data.cute_name.replace(' ','%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{profile_data.uuid}/left")

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name
        await profile_data.get_coop_names()

        created_at = profile_data.created_at//1000
        coops_string = "; ".join(profile_data.coop_names)

        selected = profile_data.selected
        if selected:
            selected_string = "**Yes**"
        else:
            selected_string = "**No**"

        description = f"""
Created At: **<t:{created_at}:d>**
Selected: {selected_string}
Co-op: {coops_string}"""
        
        embed.description = description
        

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        embed.title = f"{formatted_username} {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())} Profile"

        skills = profile_data.skill_data
        total_skill_levels = 0

        for skill in skills:
            if skill in ["runecrafting", "social"]:
                continue

            total_skill_levels += skills[skill]["level"]
        
        skill_average = total_skill_levels / 9
        sblevel = profile_data.skyblock_level

        embed.add_field(
            name=f"{self.emojis.level} SkyBlock Level",
            value=f"{sblevel}"
        )

        catacombs = profile_data.dungeon_data
        catacombs_level = round(catacombs.get("level", 0), 2)

        embed.add_field(
            name=f"{self.emojis.mort} Catacombs Level",
            value=f"{catacombs_level}"
        )

        embed.add_field(
            name=f"{self.emojis.skills} Skill Average",
            value=f"{round(skill_average, 2)}"
        )

        networth_data = profile_data.networth_data
        networth = networth_data.get("networth", 0)
        unsoulbound_networth = networth_data.get("unsoulboundNetworth", 0)
        soulbound_networth = networth-unsoulbound_networth

        purse = networth_data.get("purse", 0)
        bank = networth_data.get("bank", 0)
        coins = purse+bank

        embed.add_field(
            name=f"{self.emojis.bankitem} Networth",
            value=f"{numerize(networth)}",
            inline=True
        )

        embed.add_field(
            name=f":x: Soulbound Networth",
            value=f"{numerize(soulbound_networth)}",
            inline=True
        )

        embed.add_field(
            name=f"{self.emojis.gold_ingot} Coins",
            value=f"{numerize(coins)}",
            inline=True
        )

        hotm_data = profile_data.mining_data
        hotm = hotm_data.get("hotm", {})

        level = hotm.get("level", 0)
        xp = hotm.get("experience", 0)


        powder = hotm.get("powder", {})
        gemstone = powder.get("gemstone", {})
        gemstone_total = gemstone.get("total", 0)

        mithril = powder.get("mithril", {})
        mithril_total = mithril.get("total", 0)

        glacite = powder.get("glacite", {})
        glacite_total = glacite.get("total", 0)

        embed.add_field(
            name=f"{self.emojis.hotm} Heart of the Mountain",
            value=f"{level} (**{numerize(xp)} EXP**)"
        )

        embed.add_field(
            name=f"{self.emojis.greendye} Powders {self.emojis.pinkdye}",
            value=f"**{numerize(mithril_total)}**/**{numerize(gemstone_total)}**/**{numerize(glacite_total)}**"
        )

        slayer_data = profile_data.slayer_data

        slayer_string = ""
        for slayer in slayer_data:
            if slayer == "raw":
                continue

            slayer_string += f"{int(slayer_data[slayer]['level'])}/"

        embed.add_field(
            name=f"{self.emojis.revenant_horror} Slayer",
            value=slayer_string[:-1]
        )

        embed.set_footer(
            text=get_footer("nom")
        )

        return embed


    @select(row=0)
    async def select_profile(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.defer()

        for option in select.options:
            option.default = False
            if option.value == select.values[0]:
                option.default = True

        self.embed_cutename = select.values[0]
        embed = await self.create_embed()
        
        if interaction.user.id != self.user_id:
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            await interaction.edit_original_response(embed=embed, view=self)

    @select(
        row=1,
        options=[
            discord.SelectOption(label="Networth", value="networth", emoji="<:bankitem:1236756044588253184>"),
            discord.SelectOption(label="HotM", value="mining", emoji="<:hotm:1236755608494149735>"),
            discord.SelectOption(label="Farming", value="farming", emoji="<:golden_hoe:1236755672264212481>"),
            discord.SelectOption(label="Skills", value="skills", emoji="<:skills:1236755374254850099>"),
            discord.SelectOption(label="Pets", value="pets", emoji="<:taming:1236755128871161989>"),
            discord.SelectOption(label="Rift", value="rift", emoji="<a:mirrorverse_timecharm:1236747535582756894>"),
            discord.SelectOption(label="Slayers", value="slayers", emoji="<:revenant_horror:1236755427165999186>"), 

        ],
        placeholder="Select a Statistic to View."
    )
    async def show_sub_stats(self, select: discord.ui.Select, interaction: discord.Interaction):
        value = select.values[0]
        message = await interaction.response.send_message(content="\u200b", ephemeral=True)

        if value == "mining":
            view = HotmProfileSelector(self.user_id, self.username, self.bot, self.parser, self.selected_cutename, interaction)

        elif value == "farming":
            view = FarmingProfileSelector(self.user_id, self.username, self.bot, self.parser, self.selected_cutename, interaction)

        elif value == "skills":
            view = SkillsView(self.user_id, self.username, self.bot, self.parser, self.selected_cutename, interaction)

        elif value == "pets":
            view = PetsProfileSelector(self.user_id, self.username, self.bot, self.parser, self.selected_cutename, interaction)

        elif value == "rift":
            view = RiftProfileSelector(self.user_id, self.username, self.bot, self.parser, self.selected_cutename, interaction)

        elif value == "networth":
            view = NetworthProfileSelector(self.user_id, self.username, self.bot, self.parser, self.selected_cutename, interaction)

        elif value == "slayers":
            view = SlayersView(self.user_id, self.username, self.bot, self.parser, self.selected_cutename, interaction)

        embed = await view.create_embed()
        await message.edit_original_response(embed=embed, view=view)


class HotmProfileSelector(discord.ui.View):
    def __init__(self, user_id, username, bot, parser: SkyblockParser, selected_profile_cutename, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.bot = bot
        self.interaction = interaction

        self.profiles = parser.get_profiles()
        self.emojis = bot.emojis
        self.selected_cutename = selected_profile_cutename
        self.embed_cutename = selected_profile_cutename
        self.user_id = user_id

        options = []
        for profile in self.profiles:
            _profile = parser.select_profile(profile)
            profile_type = _profile.profile_type

            emoji = getattr(self.emojis, profile.lower())
            if profile == selected_profile_cutename:
                options.append(discord.SelectOption(
                    label=profile, value=profile, emoji=emoji, default=True, description=gamemode_to_gamemode(profile_type)))
                continue

            options.append(discord.SelectOption(
                label=profile, value=profile, emoji=emoji, description=gamemode_to_gamemode(profile_type)))

        self.children[0].options = options

        self.counter = 0
        self.trigger_timeout.start()
        self.username = username
        self.soulbound = None

    @tasks.loop(seconds=180)
    async def trigger_timeout(self):
        await timeout_view(self)

    async def create_embed(self):

        profile_data = await get_data_from_cache(self)

        embed = discord.Embed(color=discord.Color.blue(
        ), url=f"https://sky.noemt.dev/stats/{profile_data.uuid}/{profile_data.cute_name.replace(' ','%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{profile_data.uuid}/left")

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        embed.title = f"{formatted_username} Heart of the Mountain on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"

        hotm_data = profile_data.mining_data
        hotm = hotm_data.get("hotm", {})
        nodes = hotm.get("nodes", {})
        selected_ability = hotm.get("selected_ability", "none")
        powders = hotm.get("powder", {})
        gemstone = powders.get("gemstone", {})
        mithril = powders.get("mithril", {})
        glacite = powders.get("glacite", {})

        embed.description = f"""
{self.bot.emojis.hotm} Level: **{hotm.get("level", 0)}** (**{format(int(hotm.get("experience", 0)), ',d')} EXP**)
{self.bot.emojis.iron_nugget} **{hotm.get("tokens", 0)-hotm.get("tokens_spent", 0)}** (of **{hotm.get("tokens", 0)}** Total)
{self.bot.emojis.greendye} **{numerize(mithril.get("total", 0))}** / {self.bot.emojis.pinkdye}**{numerize(gemstone.get("total", 0))}** / <:NIIKu8ruVsED7AGY:1236464465009049722> **{numerize(glacite.get("total", 0))}**

\u200b"""

        embed.description += get_hotm_emojis(nodes, selected_ability)

        perk_field_value = ""
        for perk in nodes:
            for list in HOTM_TREE_MAPPING:
                for item in list:

                    if item["type"] == perk:
                        if perk in SPECIAL_HOTM_TYPES:
                            if perk == "special_0":
                                emoji = HOTM_TREE_EMOJIS["peak"]
                            
                            elif perk == selected_ability:
                                emoji = HOTM_TREE_EMOJIS["selected_ability"]
                            
                            else:
                                emoji = HOTM_TREE_EMOJIS["ability"]

                        else:
                            if nodes[perk] == item["maxLevel"]:
                                emoji = HOTM_TREE_EMOJIS["maxed_path"]
                            
                            else:
                                emoji = HOTM_TREE_EMOJIS["unlocked_path"]
                                    
                        perk_field_value += f"{emoji} {item['name']}: **{nodes[perk]}**/**{item['maxLevel']}**\n"
                        break

        crystal_data = hotm.get("crystals", {})
        crystal_field_value = ""
        for crystal in crystal_data:
            state = crystal_data[crystal].get("state", None)
            if not state:
                continue
            state = state.lower().replace("_", " ").title()

            try:
                emoji = getattr(self.emojis, crystal)+" "
            except:
                emoji = ""

            crystal_field_value += f"{emoji}{crystal.replace('_', ' ').title()}: **{state}**\n"

        embed.add_field(
            name="Crystals",
            value=crystal_field_value if len(crystal_field_value) != 0 else "Player has never found a crystal."
        )

        embed.set_footer(
            text=get_footer("nom")
        )
        
        return embed


    @select(row=0)
    async def select_profile(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.defer()

        for option in select.options:
            option.default = False
            if option.value == select.values[0]:
                option.default = True

        self.embed_cutename = select.values[0]
        embed = await self.create_embed()
        
        if interaction.user.id != self.user_id:
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            await interaction.edit_original_response(embed=embed, view=self)

class SkillsView(discord.ui.View):
    def __init__(self, user_id, username, bot, parser: SkyblockParser, selected_profile_cutename, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.bot = bot
        self.interaction = interaction

        self.profiles = parser.get_profiles()
        self.emojis = bot.emojis
        self.selected_cutename = selected_profile_cutename
        self.embed_cutename = selected_profile_cutename
        self.user_id = user_id

        options = []
        for profile in self.profiles:
            _profile = parser.select_profile(profile)
            profile_type = _profile.profile_type

            emoji = getattr(self.emojis, profile.lower())
            if profile == selected_profile_cutename:
                options.append(discord.SelectOption(
                    label=profile, value=profile, emoji=emoji, default=True, description=gamemode_to_gamemode(profile_type)))
                continue

            options.append(discord.SelectOption(
                label=profile, value=profile, emoji=emoji, description=gamemode_to_gamemode(profile_type)))

        self.children[0].options = options

        self.counter = 0
        self.trigger_timeout.start()
        self.username = username
        self.soulbound = None

    @tasks.loop(seconds=180)
    async def trigger_timeout(self):
        await timeout_view(self)

    async def create_embed(self):

        profile_data = await get_data_from_cache(self)

        embed = discord.Embed(color=discord.Color.blue(
        ), url=f"https://sky.noemt.dev/stats/{profile_data.uuid}/{profile_data.cute_name.replace(' ','%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{profile_data.uuid}/left")

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        embed.title = f"{formatted_username} Skills on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"

        skills = profile_data.skill_data
        total_skill_levels = 0
        skill_exp = 0

        skill_emojis = {
            "farming": self.emojis.golden_hoe,
            "mining": self.emojis.stonepickaxe,
            "combat": self.emojis.combat,
            "foraging": self.emojis.foraging,
            "fishing": self.emojis.fishing,
            "enchanting": self.emojis.enchanting,
            "alchemy": self.emojis.alchemy,
            "taming": self.emojis.taming,
            "carpentry": self.emojis.carpentry,
            "runecrafting": self.emojis.runecrafting,
            "social": self.emojis.social,
        }

        for skill in skills:
            level = skills[skill]["level"]
            if type(level) != int:
                level = round(level, 2)

            embed.add_field(
                name=f"{skill_emojis[skill]} {skill.title()}",
                value=f"**{level}** ({numerize(skills[skill]['experience'])} XP)"
            )
            if skill in ["runecrafting", "social"]:
                continue

            total_skill_levels += skills[skill]["level"]
            skill_exp += skills[skill]["experience"]

        skill_average = total_skill_levels / 9

        embed.description = f"""
{self.emojis.skills} Skill Average: **{round(skill_average, 2)}**
{self.emojis.taming} Total Experience: **{numerize(skill_exp)}**"""

        catacombs = profile_data.dungeon_data
        catacombs_level = round(catacombs.get("level", 0), 2)
        catacombs_xp = round(catacombs.get("experience", 0), 2)

        embed.add_field(
            name=f"{self.emojis.mort} Dungoneering",
            value=f"**{catacombs_level}** ({numerize(catacombs_xp)} XP)"
        )

        embed.set_footer(
            text=get_footer("nom")
        )

        return embed


    @select(row=0)
    async def select_profile(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.defer()

        for option in select.options:
            option.default = False
            if option.value == select.values[0]:
                option.default = True

        self.embed_cutename = select.values[0]
        embed = await self.create_embed()
        
        if interaction.user.id != self.user_id:
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            await interaction.edit_original_response(embed=embed, view=self)

    @select(
        row=1,
        options=[
            discord.SelectOption(label="Mining", value="mining", emoji="<:stonepickaxe:1236755172139728997>"),
            discord.SelectOption(label="Farming", value="farming", emoji="<:golden_hoe:1236755672264212481>")
        ],
        placeholder="Select a Statistic to View."
    )
    async def show_sub_stats(self, select: discord.ui.Select, interaction: discord.Interaction):
        value = select.values[0]

        message = await interaction.response.send_message(content="\u200b", ephemeral=True)

        if value == "mining":
            view = HotmProfileSelector(self.user_id, self.username, self.bot, self.parser, self.selected_cutename, interaction)


        elif value == "farming":
            view = FarmingProfileSelector(self.user_id, self.username, self.bot, self.parser, self.selected_cutename, interaction)

        embed = await view.create_embed()
        await message.edit_original_response(embed=embed, view=view)

class FarmingProfileSelector(discord.ui.View):
    def __init__(self, user_id, username, bot, parser: SkyblockParser, selected_profile_cutename, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.bot = bot
        self.interaction = interaction

        self.profiles = parser.get_profiles()
        self.emojis = bot.emojis
        self.selected_cutename = selected_profile_cutename
        self.embed_cutename = selected_profile_cutename
        self.user_id = user_id

        options = []
        for profile in self.profiles:
            _profile = parser.select_profile(profile)
            profile_type = _profile.profile_type

            emoji = getattr(self.emojis, profile.lower())
            if profile == selected_profile_cutename:
                options.append(discord.SelectOption(
                    label=profile, value=profile, emoji=emoji, default=True, description=gamemode_to_gamemode(profile_type)))
                continue

            options.append(discord.SelectOption(
                label=profile, value=profile, emoji=emoji, description=gamemode_to_gamemode(profile_type)))

        self.children[0].options = options

        self.counter = 0
        self.trigger_timeout.start()
        self.username = username
        self.soulbound = None

    @tasks.loop(seconds=180)
    async def trigger_timeout(self):
        await timeout_view(self)

    async def create_embed(self):

        profile_data = await get_data_from_cache(self)

        embed = discord.Embed(color=discord.Color.blue(
        ), url=f"https://sky.noemt.dev/stats/{profile_data.uuid}/{profile_data.cute_name.replace(' ','%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{profile_data.uuid}/left")

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        embed.title = f"{formatted_username} Farming Stats on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"

        farming_data = profile_data.farming_data
        medals = farming_data.get("medals", {})
        brackets = farming_data.get("unique_brackets", {})
        perks = farming_data.get("perks", {})

        unique_golds = brackets.get("gold", {})
        unique_platinum = brackets.get("platinum", {})
        unique_diamond = brackets.get("diamond", {})

        mappings = {
            "INK_SACK:3": {"name": "Cocoa Beans", "emoji": self.emojis.cocoa_beans},
            "CARROT_ITEM": {"name": "Carrot", "emoji": self.emojis.carrot},
            "POTATO_ITEM": {"name": "Potato", "emoji": self.emojis.potato},
            "SUGAR_CANE": {"name": "Sugar Cane", "emoji": self.emojis.sugar_cane},
            "CACTUS": {"name": "Cactus", "emoji": self.emojis.cactus},
            "WHEAT": {"name": "Wheat", "emoji": self.emojis.wheat},
            "PUMPKIN": {"name": "Pumpkin", "emoji": self.emojis.pumpkin},
            "MELON": {"name": "Melon", "emoji": self.emojis.melon},
            "NETHER_STALK": {"name": "Nether Wart", "emoji": self.emojis.nether_wart},
            "MUSHROOM_COLLECTION": {"name": "Mushroom", "emoji": self.emojis.red_mushroom},
        }

        done = []

        unique_golds_string = ""
        for gold in unique_golds:
            if gold in mappings:
                bracket_data = mappings[gold]
                done.append(gold)
                unique_golds_string += f"{bracket_data['emoji']} {bracket_data['name']}\n"

        for platinum in unique_platinum:
            if platinum in done:
                continue
            if platinum in mappings:
                bracket_data = mappings[platinum]
                done.append(platinum)
                unique_golds_string += f"{bracket_data['emoji']} {bracket_data['name']}\n"

        for diamond in unique_diamond:
            if diamond in done:
                continue
            if diamond in mappings:
                bracket_data = mappings[diamond]
                done.append(diamond)
                unique_golds_string += f"{bracket_data['emoji']} {bracket_data['name']}\n"

        embed.add_field(
            name=f"Unique Gold Medals ({len(done)})",
            value=unique_golds_string if len(unique_golds_string) != 0 else "Player has no Unique Gold Medals."
        )

        contests = farming_data.get("contests", {})
        total_medals_claimed = {}
        for contest in contests:
            contest_data = contests[contest]
            medal = contest_data.get("claimed_medal")
            if medal is None:
                continue

            medal_data = MEDAL_DATA[medal]
            for reward in medal_data:
                if reward not in total_medals_claimed:
                    total_medals_claimed[reward] = 0

                total_medals_claimed[reward] += medal_data[reward]

        bronze_medals_t = total_medals_claimed.get("bronze", 0)
        silver_medals_t = total_medals_claimed.get("silver", 0)
        gold_medals_t = total_medals_claimed.get("gold", 0)
        all_medals = bronze_medals_t+silver_medals_t+gold_medals_t

        
        pelts = farming_data.get("pelts", 0)

        bronze_medals = medals.get("bronze", 0)
        silver_medals = medals.get("silver", 0)
        gold_medals = medals.get("gold", 0)
        total_medals = bronze_medals+silver_medals+gold_medals

        embed.description = f"""
{self.emojis.jacobs_medal} Contests: **{len(contests)}**
{self.emojis.pelts} Pelts: **{pelts}**"""
        
        embed.add_field(
            name=f"Medals: {total_medals} (**{all_medals}**)",
            value=f"""
{self.emojis.gold_ingot} Gold **{gold_medals}** (**{gold_medals_t}**)
{self.emojis.iron_ingot} Silver **{silver_medals}** (**{silver_medals_t}**)
{self.emojis.brick} Bronze **{bronze_medals}** (**{bronze_medals_t}**)""" 
        )

        embed.add_field(
            name="Farming Perks",
            value=f"""
{self.emojis.hay_bale} Farming Level Cap: **{perks.get("farming_level_cap", 0)}** / 10
{self.emojis.wheat} Extra Farming Drops: **☘ {perks.get("double_drops", 0)*4}** / ☘ 60
<:7MfDLLTROQyjP5kr:1236437778976210994> Personal Bests: **{perks.get("personal_bests", False)}**""",
            inline=False
        )

        embed.set_footer(
            text=get_footer("nom")
        )
        
        return embed
    
    async def create_embed_contest_display(self):
        
        profile_data = await get_data_from_cache(self)

        embed = discord.Embed(color=discord.Color.blue(
        ), url=f"https://sky.noemt.dev/stats/{profile_data.uuid}/{profile_data.cute_name.replace(' ','%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{profile_data.uuid}/left")

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        embed.title = f"{formatted_username} Best Contests on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"

        farming_data = profile_data.farming_data
        contests = farming_data.get("contests", {})
        if len(contests) == 0:
            embed.description = "Player has not participated in a Jacob's Contests."

            embed.set_footer(
                text=get_footer("nom")
            )
        
            return embed
        
        mappings = {
            "INK_SACK:3": {"name": "Cocoa Beans", "emoji": self.emojis.cocoa_beans},
            "CARROT_ITEM": {"name": "Carrot", "emoji": self.emojis.carrot},
            "POTATO_ITEM": {"name": "Potato", "emoji": self.emojis.potato},
            "SUGAR_CANE": {"name": "Sugar Cane", "emoji": self.emojis.sugar_cane},
            "CACTUS": {"name": "Cactus", "emoji": self.emojis.cactus},
            "WHEAT": {"name": "Wheat", "emoji": self.emojis.wheat},
            "PUMPKIN": {"name": "Pumpkin", "emoji": self.emojis.pumpkin},
            "MELON": {"name": "Melon", "emoji": self.emojis.melon},
            "NETHER_STALK": {"name": "Nether Wart", "emoji": self.emojis.nether_wart},
            "MUSHROOM_COLLECTION": {"name": "Mushroom", "emoji": self.emojis.red_mushroom},
        }

        contest_data = {}

        for contest in contests:
            _contest = contest
            for mapping in mappings:
                contest = contest.replace(mapping, mappings[mapping]["name"])

            contest_type = contest.split(":")[-1]

            if contest_type not in contest_data:
                contest_data[contest_type] = {}

            pos = contest_data[contest_type].get("claimed_position", -1)
            if pos != -1:
                if pos < contests[_contest].get("claimed_position", 10e10):
                    continue

                else:
                    contest_data[contest_type] = contests[_contest]

            else:
                contest_data[contest_type] = contests[_contest]

        medal_emojis = {
            "diamond": self.emojis.diamond_medal,
            "platinum": self.emojis.platinum_medal,
            "gold": self.emojis.gold_ingot,
            "silver": self.emojis.iron_ingot,
            "bronze": self.emojis.brick,
            "none": self.emojis.empty
        }
        
        for contest in enumerate(contest_data):
            index = contest[0]
            contest = contest[1]

            for mapping in mappings:
                mapping_name = mappings[mapping]["name"]
                if mapping_name == contest:
                    contest_data[contest]["name"] = mappings[mapping]["name"]
                    contest_data[contest]["emoji"] = mappings[mapping]["emoji"]

            data = contest_data[contest]
            position = data.get("claimed_position", "Not detected")
            if type(position) == int:
                position_string = f"#{position+1}"
            else:
                position_string = position

            if index % 2 == 0 and index != 0:
                embed.add_field(
                    name="\u200b", value="\u200b"
                )

            embed.add_field(
                name=f"{data['emoji']} {data['name']}",
                value=f"""
{self.emojis.jacobs_medal} Position: **{position_string}**
{medal_emojis[data.get('claimed_medal', 'none')]} Medal: **{data.get('claimed_medal', 'None').title()}**
<:8ASHktnMmjcBdY5T:1236485633334050856> Collected: **{numerize(data['collected'])}**""",
            )

        if (len(embed.fields) + 1) % 3 == 0:
            embed.add_field(
                name="\u200b", value="\u200b"
            )

        embed.set_footer(
            text=get_footer("nom")
        )
        
        return embed


    @select(row=0)
    async def select_profile(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.defer()

        for option in select.options:
            option.default = False
            if option.value == select.values[0]:
                option.default = True

        self.embed_cutename = select.values[0]
        embed = await self.create_embed()
        
        if interaction.user.id != self.user_id:
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            await interaction.edit_original_response(embed=embed, view=self)

    @button(row=1, label="Best Contests", style=discord.ButtonStyle.secondary)
    async def best_contests(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        embed = await self.create_embed_contest_display()
        await interaction.followup.send(embed=embed, ephemeral=True)


class PetsProfileSelector(discord.ui.View):
    def __init__(self, user_id, username, bot, parser: SkyblockParser, selected_profile_cutename, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.bot = bot
        self.interaction = interaction

        self.profiles = parser.get_profiles()
        self.emojis = bot.emojis
        self.selected_cutename = selected_profile_cutename
        self.embed_cutename = selected_profile_cutename
        self.user_id = user_id

        options = []
        for profile in self.profiles:
            _profile = parser.select_profile(profile)
            profile_type = _profile.profile_type

            emoji = getattr(self.emojis, profile.lower())
            if profile == selected_profile_cutename:
                options.append(discord.SelectOption(
                    label=profile, value=profile, emoji=emoji, default=True, description=gamemode_to_gamemode(profile_type)))
                continue

            options.append(discord.SelectOption(
                label=profile, value=profile, emoji=emoji, description=gamemode_to_gamemode(profile_type)))

        self.children[0].options = options

        self.counter = 0
        self.trigger_timeout.start()
        self.username = username
        self.soulbound = None

        self.page = 0
        self.page_count = 0

    @tasks.loop(seconds=180)
    async def trigger_timeout(self):
        await timeout_view(self)
            
    async def create_select(self, pets:list[Pet]):
        options = []
        if len(pets) == 0:
            self.children[1].options = [discord.SelectOption(label="No Pets Found.", value="0", emoji="❓")]
            self.children[1].disabled = True
            return
    
        else:
            self.children[1].disabled = False
 
        for pet in pets:
            pet:Pet
            pet_name = pet.type.replace("_", " ").title()

            if not pet.skin:
                pet_emoji_data = self.bot.item_emojis.get(f"PET_{pet.type}")
                if pet_emoji_data:

                    emoji_url = pet_emoji_data["url"]
                    emoji_id = pet_emoji_data["id"]
                    emoji_name = pet_emoji_data["name"]

                    if ".gif" in emoji_url:
                        emoji_prefix = "<a:"
                    
                    else:
                        emoji_prefix = "<:"

                    pet_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}>"

                else:
                    pet_emoji = "❓"

            else:
                pet_emoji_data = self.bot.item_emojis.get(f"PET_SKIN_{pet.skin}")
                if pet_emoji_data:

                    emoji_url = pet_emoji_data["url"]
                    emoji_id = pet_emoji_data["id"]
                    emoji_name = pet_emoji_data["name"]

                    if ".gif" in emoji_url:
                        emoji_prefix = "<a:"
                    
                    else:
                        emoji_prefix = "<:"

                    pet_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}>"
                
                else:
                    pet_emoji = "❓"



            options.append({
                "label": f"[Lvl {pet.level}] {pet_name}", "value": str(pets.index(pet)), "emoji": pet_emoji
            })

        self.children[1].options = [*[discord.SelectOption(label=option["label"], value=option["value"], emoji=option["emoji"]) for option in options], discord.SelectOption(label="Return to Pets", value="back", emoji="🔙")]


    async def create_embed(self):

        profile_data = await get_data_from_cache(self)

        embed = discord.Embed(color=discord.Color.blue(
        ), url=f"https://sky.noemt.dev/stats/{profile_data.uuid}/{profile_data.cute_name.replace(' ','%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{profile_data.uuid}/left")

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        embed.title = f"{formatted_username} Pets on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"

        emojis = self.bot.item_emojis

        pets:list[Pet] = profile_data.pets
        pets.sort(key=lambda x: x.level, reverse=True)
        pets.sort(key=lambda x: RARITY_ORDER.index(x.tier))

        try:
            pets = [pets[i:i + 20] for i in range(0, len(pets), 20)]
            self.page_count = len(pets)
            pet_chunk = pets[self.page]

        except:
            self.page_count = 1
            await self.update_paginator_button()
            embed.description = "No Pets Found."
            await self.create_select([])
            embed.set_footer(
                text=get_footer("nom")
            )
        
            return embed
        
        await self.update_paginator_button()
        
        pet_string = ""

        for pet in pet_chunk:
            pet:Pet
            pet_emoji = "❓"

            if not pet.skin:
                pet_emoji_data = emojis.get(f"PET_{pet.type}")
                if pet_emoji_data:

                    emoji_url = pet_emoji_data["url"]
                    emoji_id = pet_emoji_data["id"]
                    emoji_name = pet_emoji_data["name"]

                    if ".gif" in emoji_url:
                        emoji_prefix = "<a:"
                    
                    else:
                        emoji_prefix = "<:"

                    pet_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}>"


            else:

                pet_emoji_data = emojis.get(f"PET_SKIN_{pet.skin}")
                if pet_emoji_data:
                    emoji_url = pet_emoji_data["url"]
                    emoji_id = pet_emoji_data["id"]
                    emoji_name = pet_emoji_data["name"]

                    if ".gif" in emoji_url:
                        emoji_prefix = "<a:"
                    
                    else:
                        emoji_prefix = "<:"

                    pet_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}>"


            held_item_emoji = ""
            held_item = pet.held_item
            if held_item:
                pet_item_data = emojis.get(held_item)
                if pet_item_data:

                    emoji_url = pet_item_data["url"]
                    emoji_id = pet_item_data["id"]
                    emoji_name = pet_item_data["name"]

                    if ".gif" in emoji_url:
                        emoji_prefix = "<a:"
                    
                    else:
                        emoji_prefix = "<:"

                    held_item_emoji = f" {emoji_prefix}{emoji_name}:{emoji_id}>"

            rarity_emoji = RARITY_EMOJIS[pet.tier]
            pet_name = pet.type.replace("_", " ").title()
        
            pet_string += f"{pet_emoji} [Lvl {pet.level}] {pet_name}{held_item_emoji} {rarity_emoji}\n"

        embed.description = pet_string

        await self.create_select(pet_chunk)
        embed.set_footer(text=f"Page {self.page+1}/{self.page_count} | made by nom")
        return embed


    @select(row=1)
    async def select_profile(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.defer()

        for option in select.options:
            option.default = False
            if option.value == select.values[0]:
                option.default = True
        self.embed_cutename = select.values[0]
        self.page = 0
        embed = await self.create_embed()
        
        if interaction.user.id != self.user_id:
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            await interaction.edit_original_response(embed=embed, view=self)

    @select(row=2, placeholder="Select a Pet to View.")
    async def select_pet(self, select:discord.ui.Select, interaction: discord.Interaction):
        value = select.values[0]
        if value == "back":
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed)
            return
        
        pet_index = int(value)

        for option in select.options:
            option.default = False
            if option.value == value:
                option.default = True

        profile_data = await get_data_from_cache(self)

        embed = discord.Embed(color=discord.Color.blue(
        ), url=f"https://sky.noemt.dev/stats/{profile_data.uuid}/{profile_data.cute_name.replace(' ','%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{profile_data.uuid}/left")

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        pets:list[Pet] = profile_data.pets
        pets.sort(key=lambda x: x.level, reverse=True)
        pets.sort(key=lambda x: RARITY_ORDER.index(x.tier))

        pets = [pets[i:i + 20] for i in range(0, len(pets), 20)]
        self.page_count = len(pets)

        pet_chunk = pets[self.page]
        pet:Pet = pet_chunk[pet_index]
        pet_name = pet.type.replace("_", " ").title()
        embed.title = f"{formatted_username} {pet_name} Pet on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"
        emojis = self.bot.item_emojis


        pet_item = pet.held_item
        pet_item_emoji = "**None**"

        if pet_item not in ["", None]:
            pet_item_data = emojis.get("PET_ITEM_"+pet_item)
            if not pet_item_data:
                pet_item_data = emojis.get(pet_item)
                if not pet_item_data:
                    pet_item_emoji = "❓"
                    
            try:
                emoji_url = pet_item_data["url"]
                emoji_id = pet_item_data["id"]
                emoji_name = pet_item_data["name"]

                if ".gif" in emoji_url:
                    emoji_prefix = "<a:"
                
                else:
                    emoji_prefix = "<:"

                pet_item_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}>"
            except:
                pass

        
        pet_emoji_data = emojis.get(f"PET_{pet.type}")
        if pet_emoji_data:

            emoji_url = pet_emoji_data["url"]
            emoji_id = pet_emoji_data["id"]
            emoji_name = pet_emoji_data["name"]

            if ".gif" in emoji_url:
                emoji_prefix = "<a:"
            
            else:
                emoji_prefix = "<:"

            pet_emoji = f"{emoji_prefix}{emoji_name}:{emoji_id}>"

        else:
            pet_emoji = "❓"

        pet_skin = "**None**"

        pet_skin_data = emojis.get(f"PET_SKIN_{pet.skin}", None)
        if pet_skin_data:

            emoji_url = pet_skin_data["url"]
            emoji_id = pet_skin_data["id"]
            emoji_name = pet_skin_data["name"]

            if ".gif" in emoji_url:
                emoji_prefix = "<a:"
            
            else:
                emoji_prefix = "<:"

            pet_skin = f"{emoji_prefix}{emoji_name}:{emoji_id}>"

        pet_rarity = pet.tier
        offset = rarity_offset[pet_rarity]

        if pet.level == pet.max_level:
            next_xp = 0

        else:
            next_xp = pet_levels[pet.level+offset]

        pet_xp_sum_lower = sum([pet_levels[i] for i in range(offset, pet.level+offset-1)])

        if next_xp == 0:
            current_xp_percentage = "∞"
        else:
            current_xp_percentage = round(((pet.exp - pet_xp_sum_lower) / next_xp) * 100, 2)

            
        embed.description = f"""
Name: {pet_emoji} **{pet_name}**
Rarity: **{pet.tier.title()}** {RARITY_EMOJIS[pet_rarity]}
Level: **{pet.level}** / {pet.max_level}
Held Item: {pet_item_emoji}
Skin: {pet_skin}

Current XP: **{format(int(pet.exp - pet_xp_sum_lower), ',d')}** / {format(int(next_xp), ',d')} (**{current_xp_percentage}%**)
Total XP: **{format(int(pet.exp), ',d')}** / {format(int(pet.max_xp), ',d')} (**{round((pet.exp / pet.max_xp) * 100, 2)}%**)"""
        
        if self.user_id == interaction.user.id:
            await interaction.response.edit_message(embed=embed)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True, view=self)
        
    async def update_paginator_button(self):
        if self.page_count == 1:
            self.children[-1].disabled = True
            self.children[-2].disabled = True
            return
        
        if self.page == 0:
            self.children[-2].disabled = True
            self.children[-1].disabled = False

        elif self.page == self.page_count-1:
            self.children[-1].disabled = True
            self.children[-2].disabled = False

        else:
            self.children[-1].disabled = False
            self.children[-2].disabled = False


    @button(
        label="<",
        style=discord.ButtonStyle.blurple,
        row=3,
        disabled=True
    )
    async def previous_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page -= 1
        if self.page == 0:
            button.disabled = True

        if self.page != self.page_count-1:
            self.children[-1].disabled = False

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @button(
        label=">",
        style=discord.ButtonStyle.blurple,
        row=3
    )
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page += 1
        if self.page != 0:
            self.children[-2].disabled = False

        if self.page == self.page_count-1:
            button.disabled = True

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

class RiftProfileSelector(discord.ui.View):
    def __init__(self, user_id, username, bot, parser: SkyblockParser, selected_profile_cutename, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.bot = bot
        self.interaction = interaction

        self.profiles = parser.get_profiles()
        self.emojis = bot.emojis
        self.selected_cutename = selected_profile_cutename
        self.embed_cutename = selected_profile_cutename
        self.user_id = user_id

        options = []
        for profile in self.profiles:
            _profile = parser.select_profile(profile)
            profile_type = _profile.profile_type

            emoji = getattr(self.emojis, profile.lower())
            if profile == selected_profile_cutename:
                options.append(discord.SelectOption(
                    label=profile, value=profile, emoji=emoji, default=True, description=gamemode_to_gamemode(profile_type)))
                continue

            options.append(discord.SelectOption(
                label=profile, value=profile, emoji=emoji, description=gamemode_to_gamemode(profile_type)))

        self.children[0].options = options

        self.counter = 0
        self.trigger_timeout.start()
        self.username = username
        self.soulbound = None

    @tasks.loop(seconds=180)
    async def trigger_timeout(self):
        await timeout_view(self)

    async def create_embed(self):

        profile_data = await get_data_from_cache(self)

        embed = discord.Embed(color=discord.Color.blue(
        ), url=f"https://sky.noemt.dev/stats/{profile_data.uuid}/{profile_data.cute_name.replace(' ','%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{profile_data.uuid}/left")

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        embed.title = f"{formatted_username} Rift on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"

        rift = profile_data.rift
        currencies = profile_data.currencies
        if rift == {}:
            embed.description = "Player has never entered the Rift."
            embed.set_footer(
                text=get_footer("nom")
            )
            return embed
        
        motes = currencies.get("motes_purse", 0)

        enigma = rift.get("enigma", {})
        souls = len(enigma.get("found_souls", []))

        gallery = rift.get("gallery", {})
        secured_timecharms = gallery.get("secured_trophies", [])
        secured_timecharms.sort(key=lambda x: TIMECHARM_ORDER.index(x["type"]), reverse=True)
        secured_timecharms_amount = len(secured_timecharms)

        wither_cage = rift.get("wither_cage", {})
        killed_eyes = wither_cage.get("killed_eyes", [])
        killed_eyes_amount = len(killed_eyes)

        castle = rift.get("castle", {})
        grubber_stacks = castle.get("grubber_stacks", 0)


        general_stats = profile_data.general_stats
        rift = general_stats.get("rift", {})
        lifetime_motes_earned = rift.get("lifetime_motes_earned", 0)


        embed.description = f"""
{RIFT_EMOJIS["motes"]} Motes: **{numerize(motes)}** ({numerize(lifetime_motes_earned)} lifetime)
{RIFT_EMOJIS["enigma_soul"]} Enigma Souls: **{souls}** / 42 (**{round((souls/42)*100, 2)}%**)
{RIFT_EMOJIS["timecharms"]} Timecharms: **{secured_timecharms_amount}** / 7
{RIFT_EMOJIS["eye"]} Eyes Unlocked: **{killed_eyes_amount}** / 6
{RIFT_EMOJIS["burger"]} Burgers Eaten: **{grubber_stacks}** / 5"""
        
        timecharm_field_value = ""
        
        for timecharm_data in secured_timecharms:
            type = timecharm_data["type"]
            timestamp = int(timecharm_data["timestamp"]/1000)
            timestamp_discord = f"<t:{timestamp}:d>"

            timecharm_name = TIMECHARM_NAMES[type]
            emoji = RIFT_EMOJIS[type]

            timecharm_field_value += f"{emoji} {timecharm_name} {timestamp_discord}\n"

        if len(timecharm_field_value) == 0:
            timecharm_field_value = "Player has not secured any Timecharms."

        embed.add_field(
            name="Secured Timecharms",
            value=timecharm_field_value
        )

        embed.set_footer(
            text=get_footer("nom")
        )
        
        return embed


    @select(row=0)
    async def select_profile(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.defer()

        for option in select.options:
            option.default = False
            if option.value == select.values[0]:
                option.default = True

        self.embed_cutename = select.values[0]
        embed = await self.create_embed()
        
        if interaction.user.id != self.user_id:
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            await interaction.edit_original_response(embed=embed, view=self)


class LeaderboardView(discord.ui.View):
    def __init__(self, user_id, bot, stat, pretty_stat, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stat = stat
        self.bot = bot
        self.page = 0
        count = self.bot.collection.count_documents({})
        if type(count/25) == int:
            self.page_count = count/25

        else:
            self.page_count = count//25+1

        if self.page_count == 1:
            self.children[-1].disabled=True

        self.pretty_statistic = pretty_stat
        self.user_id = user_id


    @tasks.loop(seconds=180)
    async def trigger_timeout(self):
        await timeout_view(self)

    async def create_embed(self):
        leaderboard_data = await self.bot.get_leaderboard(self.stat, self.page)
        options = []

        leaderboard_string = ""
        for profile in enumerate(leaderboard_data):
            position = self.page*25+profile[0]+1
            profile = profile[1]

            data_stat = profile["data"]
            cute_name_emoji = getattr(self.bot.emojis, profile["cute_name"].lower(), None)

            gamemode = data_stat["profile_type"]
            gamemode_emoji = gamemode_to_emoji_autocomplete(gamemode)
                
            path = self.stat.split(".")
            for i in path:
                data_stat = data_stat[i]

            position_emoji = None
            if position == 1:
                position_emoji = self.bot.emojis.gold_ingot+" "
            elif position == 2:
                position_emoji = self.bot.emojis.iron_ingot+" "
            elif position == 3:
                position_emoji = self.bot.emojis.brick+" "

            options.append(discord.SelectOption(
                label=f"#{position} {profile['username']} - {format(int(data_stat), ',d')} on {profile['cute_name']}",
                value=f"{profile['username']}-{profile['cute_name']}",
                emoji=position_emoji
            ))

            leaderboard_string += f"{position_emoji if position_emoji else ''}**#{position} {profile['username']}** - **{numerize(data_stat)}** on {profile['cute_name']} {gamemode_emoji}{cute_name_emoji}\n"

    
        embed = discord.Embed(
            title=f"{self.pretty_statistic} Leaderboard",
            color=discord.Color.blue(),
            description=leaderboard_string
        )

        embed.set_footer(text=f"Page {self.page+1}/{self.page_count} | made by nom")

        self.children[0].options = options
        
        return embed


    @select(row=0, placeholder="Select a User to View.")
    async def view_user(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        select_value = select.values[0]
        select_value_split = select_value.split("-")

        name = select_value_split[0]
        profile = select_value_split[1]

        _uuid = await get_uuid(self.bot.session, name, True)
        if _uuid == "Invalid username.":
            return await interaction.response.send_message("Please run any command with this user again, as the Username in the Database became invalid.")

        uuid = _uuid["id"]
        username = _uuid["name"]

        cached_data = self.bot.cache.get(uuid, {})

        if cached_data is not {}:
            async with self.bot.session.get(f"https://api.hypixel.net/v2/skyblock/profiles?key={HYPIXEL_API_KEY}&uuid={uuid}") as request:
                data = await request.json()
                if data["success"] is False:
                    return await interaction.response.send_message(embed=get_embed("Something went wrong.", self.bot))

                if data["profiles"] is None:
                    return await interaction.response.send_message(embed=get_embed("No profiles found.", self.bot))

            parser = SkyblockParser(data, uuid, HYPIXEL_API_KEY)
            self.bot.cache[uuid] = {"parser": parser}

        else:
            parser = cached_data["parser"]

        if self.bot.cache.get(uuid) is None:
            self.bot.cache[uuid] = {"parser": parser}

        profile.replace(" 🏝", "").replace(" ♻", "").replace(" 🎲", "")
        if profile.endswith(" "):
            profile = profile[:-1]

        if cached_data.get(profile):
            profile_data = cached_data[profile]
        
        else:
            profile_data = parser.select_profile(profile)
            await profile_data.init()
            if self.bot.cache.get(uuid) is None:
                self.bot.cache[uuid] = {}
            self.bot.cache[uuid][profile_data.cute_name] = profile_data
            if profile == "selected":
                if self.bot.cache.get(uuid) is None:
                    self.bot.cache[uuid] = {}
                self.bot.cache[uuid]["selected"] = profile_data

        cute_name = profile_data.cute_name

        interaction = await interaction.followup.send("\u200b", ephemeral=True)
        view = ProfileCommandProfileSelector(self.user_id, username, self.bot, parser, cute_name, interaction)
        embed = await view.create_embed()
        await interaction.edit(embed=embed, view=view)

    @button(
        label="<",
        style=discord.ButtonStyle.blurple,
        row=1,
        disabled=True
    )
    async def previous_page(self, button: discord.ui.Button, interaction: discord.Interaction):

        if not self.user_id == interaction.user.id:
            return await interaction.response.defer()
        
        self.page -= 1
        if self.page == 0:
            button.disabled = True

        if self.page != self.page_count-1:
            self.children[-1].disabled = False

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @button(
        label=">",
        style=discord.ButtonStyle.blurple,
        row=1
    )
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):

        if not self.user_id == interaction.user.id:
            return await interaction.response.defer()
        
        self.page += 1
        if self.page != 0:
            self.children[-2].disabled = False

        if self.page == self.page_count-1:
            button.disabled = True

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)


class SlayersView(discord.ui.View):
    def __init__(self, user_id, username, bot, parser: SkyblockParser, selected_profile_cutename, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.bot = bot
        self.interaction = interaction

        self.profiles = parser.get_profiles()
        self.emojis = bot.emojis
        self.selected_cutename = selected_profile_cutename
        self.embed_cutename = selected_profile_cutename
        self.user_id = user_id

        options = []
        for profile in self.profiles:
            _profile = parser.select_profile(profile)
            profile_type = _profile.profile_type

            emoji = getattr(self.emojis, profile.lower())
            if profile == selected_profile_cutename:
                options.append(discord.SelectOption(
                    label=profile, value=profile, emoji=emoji, default=True, description=gamemode_to_gamemode(profile_type)))
                continue

            options.append(discord.SelectOption(
                label=profile, value=profile, emoji=emoji, description=gamemode_to_gamemode(profile_type)))

        self.children[0].options = options

        self.counter = 0
        self.trigger_timeout.start()
        self.username = username
        self.soulbound = None

    @tasks.loop(seconds=180)
    async def trigger_timeout(self):
        await timeout_view(self)

    async def create_embed(self):

        profile_data = await get_data_from_cache(self)

        embed = discord.Embed(color=discord.Color.blue(
        ), url=f"https://sky.noemt.dev/stats/{profile_data.uuid}/{profile_data.cute_name.replace(' ','%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{profile_data.uuid}/left")

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        embed.title = f"{formatted_username} Slayers on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"

        slayers_data = profile_data.slayer_data
        total_xp = 0
        slayer_string = ""
        for slayer in enumerate(slayers_data):
            index = slayer[0]
            slayer = slayer[1]

            if slayer == "raw":
                continue

            slayer_data = slayers_data[slayer]

            slayer_level = round(slayer_data.get("level", 0), 2)
            slayer_string += f"**{slayer_level}**/"
            slayer_xp = slayer_data.get("experience", 0)
            total_xp += slayer_xp

            if slayer == "zombie":
                slayer_xps = revenant

            elif slayer == "spider":
                slayer_xps = spider

            elif slayer == "wolf":
                slayer_xps = sven

            elif slayer == "enderman":
                slayer_xps = enderman

            elif slayer == "blaze":
                slayer_xps = blaze

            elif slayer == "vampire":
                slayer_xps = vampire

            max_xp = slayer_xps[str(len(slayer_xps)-1)]

            progress = (slayer_xp / max_xp)
            progress = get_progress_bar(progress, 5)

            embed.add_field(
                name=f"{SLAYER_NAMES[slayer]} {int(slayer_level)} {SLAYER_EMOJIS[slayer]}",
                value=f"""
Level: **{round(slayer_level, 2)}**
XP: **{numerize(slayer_xp)}**
{progress}"""
            )

            if index % 2 == 0:
                embed.add_field(name="\u200b", value="\u200b")

        embed.description = f"""
Total XP: **{numerize(total_xp)}**
{slayer_string[:-1]}"""
        
        embed.set_footer(
            text=get_footer("nom")
        )
    
        return embed


    @select(row=0)
    async def select_profile(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.defer()

        for option in select.options:
            option.default = False
            if option.value == select.values[0]:
                option.default = True

        self.embed_cutename = select.values[0]
        embed = await self.create_embed()
        
        if interaction.user.id != self.user_id:
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            await interaction.edit_original_response(embed=embed, view=self)
    
    @select(row=1, placeholder="Select a Slayer to View.",
            options=[
                discord.SelectOption(label="Revenant", value="zombie", emoji=SLAYER_EMOJIS["zombie"]),
                discord.SelectOption(label="Tarantula", value="spider", emoji=SLAYER_EMOJIS["spider"]),
                discord.SelectOption(label="Sven", value="wolf", emoji=SLAYER_EMOJIS["wolf"]),
                discord.SelectOption(label="Enderman", value="enderman", emoji=SLAYER_EMOJIS["enderman"]),
                discord.SelectOption(label="Blaze", value="blaze", emoji=SLAYER_EMOJIS["blaze"]),
                discord.SelectOption(label="Vampire", value="vampire", emoji=SLAYER_EMOJIS["vampire"]),
                discord.SelectOption(label="Return to previous Menu.", value="back", emoji="🔙")
            ])
    
    async def select_slayer(self, select:discord.ui.Select, interaction: discord.Interaction):

        value = select.values[0]
        if value == "back":
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed)
            return
        
        for option in select.options:
            option.default = False
            if option.value == value:
                option.default = True

        slayer = select.values[0]

        profile_data = await get_data_from_cache(self)

        embed = discord.Embed(color=discord.Color.blue(
        ), url=f"https://sky.noemt.dev/stats/{profile_data.uuid}/{profile_data.cute_name.replace(' ','%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{profile_data.uuid}/left")

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"
        
        embed.title = f"{formatted_username} {SLAYER_NAMES[slayer]} Slayer on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"

        slayer_data = profile_data.slayer_data[slayer]
        slayer_level = slayer_data.get("level", 0)
        slayer_xp = slayer_data.get("experience", 0)

        if slayer == "zombie":
            slayer_xps = revenant

        elif slayer == "spider":
            slayer_xps = spider

        elif slayer == "wolf":
            slayer_xps = sven

        elif slayer == "enderman":
            slayer_xps = enderman

        elif slayer == "blaze":
            slayer_xps = blaze

        elif slayer == "vampire":
            slayer_xps = vampire

        max_xp = slayer_xps[str(len(slayer_xps)-1)]

        if slayer_xp >= max_xp:
            xp_next_level = 0
            sum_of_previous_levels = 0
        
        else:
            xp_next_level = slayer_xps[str(int(slayer_level)+1)]
            sum_of_previous_levels = sum([slayer_xps[str(i)] for i in range(int(slayer_level))])

        current_xp = slayer_xp

        try:
            progress_next_level = ((current_xp - sum_of_previous_levels) / (xp_next_level - sum_of_previous_levels))
        except ZeroDivisionError:
            progress_next_level = 1

        progress_next = get_progress_bar(progress_next_level, 10)

        progress_max_level = current_xp / max_xp
        progress_max = get_progress_bar(progress_max_level, 10)

        embed.description = f"""
Level: **{round(slayer_level, 2)}**
XP: **{numerize(slayer_xp)}** / {numerize(xp_next_level)}

Progress to Next Level ({numerize(xp_next_level)}): 
{progress_next} (**{round(progress_next_level*100, 2)}%**)

Progress to Max Level ({numerize(max_xp)}): 
{progress_max} (**{round(progress_max_level*100, 2)}%**)"""
        
        boss_kills_field = ""

        raw_data = profile_data.slayer_data["raw"] # this is hypixel api's raw output
        raw_slayer = raw_data.get(slayer, {})
        for i in range(5):
            tier_kills = raw_slayer.get(f"boss_kills_tier_{i}", 0)
            if tier_kills != 0:
                boss_kills_field += f"Tier {i+1}: **{numerize(tier_kills)}**\n"

        if len(boss_kills_field) == 0:
            boss_kills_field = "No Bossed killed."

        embed.add_field(
            name="Bosses Killed",
            value=boss_kills_field
        )

        if self.user_id == interaction.user.id:
            await interaction.response.edit_message(embed=embed)

        else:
            await interaction.followup.send(embed=embed, ephemeral=True, view=self)


class ChocoFactorySelector(discord.ui.View):
    def __init__(self, user_id, username, bot, parser: SkyblockParser, selected_profile_cutename, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.bot = bot
        self.interaction = interaction

        self.profiles = parser.get_profiles()
        self.emojis = bot.emojis
        self.selected_cutename = selected_profile_cutename
        self.embed_cutename = selected_profile_cutename
        self.user_id = user_id

        options = []
        for profile in self.profiles:
            _profile = parser.select_profile(profile)
            profile_type = _profile.profile_type

            emoji = getattr(self.emojis, profile.lower())
            if profile == selected_profile_cutename:
                options.append(discord.SelectOption(
                    label=profile, value=profile, emoji=emoji, default=True, description=gamemode_to_gamemode(profile_type)))
                continue

            options.append(discord.SelectOption(
                label=profile, value=profile, emoji=emoji, description=gamemode_to_gamemode(profile_type)))

        self.children[0].options = options

        self.counter = 0
        self.trigger_timeout.start()
        self.username = username
        self.soulbound = None
        self.cookie = True

    @tasks.loop(seconds=180)
    async def trigger_timeout(self):
        await timeout_view(self)

    async def create_embed(self):

        profile_data = await get_data_from_cache(self)
        profile_data.get_items()

        embed = discord.Embed(color=discord.Color.blue(), url=f"https://sky.noemt.dev/stats/{profile_data.uuid}/{profile_data.cute_name.replace(' ','%20')}").set_thumbnail(url=f"https://mc-heads.net/body/{profile_data.uuid}/left")

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = " "
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        embed.title = f"{formatted_username} Chocolate Factory on {cute_name}{suffix}{getattr(self.emojis, cute_name.lower())}"

        event_data = profile_data.events
        easter_event = event_data.get("easter", {})

        chocolate_amount = easter_event.get("chocolate", 0)
        since_prestige = easter_event.get("chocolate_since_prestige", 0)
        total_chocolate = easter_event.get("total_chocolate", 0)

        employee_data = easter_event.get("employees", {})

        rabbit_order = ["rabbit_bro", "rabbit_cousin", "rabbit_sis", "rabbit_father", "rabbit_grandma"]

        try:
            employee_data = {k: employee_data[k] for k in rabbit_order}
        except:
            embed.description = "This user doesn't have a chocolate factory."
            return embed

        employee_names = {
            "rabbit_bro": "Rabbit Bro",
            "rabbit_sis": "Rabbit Sis",
            "rabbit_father": "Rabbit Daddy",
            "rabbit_grandma": "Rabbit Granny",
            "rabbit_cousin": "Rabbit Cousin",
        }

        chocolate_per_second = 0
        chocolate_per_second_multiplier = 0

        talisman_adders = {
            "NIBBLE_CHOCOLATE_STICK": 10,
            "SMOOTH_CHOCOLATE_BAR": 20,
            "RICH_CHOCOLATE_CHUNK": 30,
            "GANACHE_CHOCOLATE_SLAB": 40,
            "PRESTIGE_CHOCOLATE_REALM": 50,
            "": 0
        }

        rabbit_tiers = {
            "MYTHIC": 0.05
        }

        best = ""
        for item in profile_data.talisman_bag:
            if item._id in talisman_adders:
                if best == "":
                    best = item._id
                                                           
                if talisman_adders[item._id] > talisman_adders[best]:
                    best = item._id
            
        chocolate_per_second = talisman_adders[best]

        mythic_rabbit = False
        for pet in profile_data.pets:
            if pet.type == "RABBIT":
                adder = rabbit_tiers.get(pet.tier, 0)
                if adder != 0:
                    chocolate_per_second_multiplier += adder
                    rabbit = True
                    break

        rarities = ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "MYTHIC"]
        rarity_increases = {
            "COMMON": {
                "cps": 1,
                "cpsm": 0.002
            },
            "UNCOMMON": {
                "cps": 2,
                "cpsm": 0.003
            },
            "RARE": {
                "cps": 4,
                "cpsm": 0.004
            },
            "EPIC": {
                "cps": 10,
                "cpsm": 0.005
            },
            "LEGENDARY": {
                "cps": 0,
                "cpsm": 0.02
            },
            "MYTHIC": {
                "cps": 0,
                "cpsm": 0
            }
        }

        time_tower_cooldown = 28800000

        rabbit_data:dict = easter_event.get("rabbits", {})
        rabbit_data.pop("collected_eggs", None)

        unique_rabbits = len(rabbit_data)
        rabbit_rarities_count = {}

        for rabbit in set(rabbit_data):
            rabbit_name = rabbit.replace("_", " ").title()
            for rarity in rarities:
                rarity_rabbits = self.bot.chocofactory["rarities"][rarity]

                if rabbit_name in rarity_rabbits:
                    chocolate_per_second += rarity_increases[rarity]["cps"]
                    chocolate_per_second_multiplier += rarity_increases[rarity]["cpsm"]
                    if rarity not in rabbit_rarities_count:
                        rabbit_rarities_count[rarity] = 0

                    rabbit_rarities_count[rarity] += 1

                    if rarity == "MYTHIC":
                        if rabbit_name == "Dante":
                            chocolate_per_second += 50
                        
                        elif rabbit_name == "Einstein":
                            time_tower_cooldown = 3600*7

                        elif rabbit_name == "Galaxy":
                            chocolate_per_second_multiplier += 0.05

                        elif rabbit_name == "Zest Zephyr":
                            chocolate_per_second_multiplier += 0.03
                            chocolate_per_second += 30

                    break

        rabbit_rarities_count = {k: rabbit_rarities_count[k] for k in rarities if k in rabbit_rarities_count}
            
        prestige_level = easter_event.get("chocolate_level", 0)
        rbcl = easter_event.get("rabbit_barn_capacity_level", 0)

        time_tower_data = easter_event.get("time_tower", {})
        activation_time = time_tower_data.get("activation_time", 0)
        
        last_viewed_chocolate_factory = easter_event.get("last_viewed_chocolate_factory", 0)
        remaining_seconds_time_tower = datetime.now().timestamp()*1000-3600000-activation_time

        seconds_since_last_view = (datetime.now().timestamp()*1000-last_viewed_chocolate_factory)//1000

        if remaining_seconds_time_tower < 0:
            seconds_time_tower = 0

        else:
            seconds_time_tower = remaining_seconds_time_tower//1000


        time_tower_level = time_tower_data.get("level", 0)
        time_tower_charges = time_tower_data.get("charges", 0)
        last_charge_time = time_tower_data.get("last_charge_time", 0)

        active = ""
        if activation_time > datetime.now().timestamp()*1000-3600000:
            active = " (**ACTIVE**)"
        
        if time_tower_charges != 0:
            timestamp = "next charge: **READY**"
        else:
            timestamp = f"next charge: **<t:{last_charge_time//1000+time_tower_cooldown/1000}:R>**"


        shrine_level = easter_event.get("rabbit_rarity_upgrades", 0)
        click_level = easter_event.get("click_upgrades", 0)+1
        jackrabbit = easter_event.get("chocolate_multiplier_upgrades", 0)

        jackrabbit_multi = round(jackrabbit*0.1, 1)

        factory_emojis = {
            "rabbit_bro": "<:rabbit_bro:1238171792774791168>",
            "rabbit_sis": "<:rabbit_sis:1238171789146718331>",
            "rabbit_cousin": "<:rabbit_cousin:1238171791084621905>",
            "rabbit_father": "<:rabbit_daddy:1238171786579804212>",
            "rabbit_grandma": "<:rabbit_granny:1238171784889634888>",
            "time_tower": "<:clock:1238167916688445511>",
            "time_tower": "<:clock:1238167916688445511>",
            "shrine_l": "<:Oe4fpme34QtzjRKV:1236464631741157477>",
            "rabbit_click": "<:3TN2zsLY0DkjcLm9:1236447255045738600>",
            "barn_c": "<:QVTSEwIiILaYH4Aq:1236464687475068979>",
            "choc": "<:cocoa_beans:1236753057375588442>",
            "u_rab": "<:k3lRCZru6q8xcTvc:1236489557411631125>",
            "fac_lvl": "<:o52WYARvMZ2BAad5:1236435448767709245>",
            "charge": "<:c05DPj7786irRKw7:1236487569739612291>",
            "best": "<:up_arrow:1238191665345331300>",
            "JackRabbitUpgrade": "<:JackRabbitUpgrade:1238197548540366918>"
        }

        cps_data = {}
        cookies_per_second_employees = {
            "rabbit_bro": 1,
            "rabbit_cousin": 2,
            "rabbit_sis": 3,
            "rabbit_father": 4,
            "rabbit_grandma": 5,
        }

        cost_data = {}

        for employee in employee_data:
            level = employee_data[employee]
            
            if level+1 > 120+(prestige_level-1)*20:
                next_level_cost = 0

            else:
                next_level_cost = self.bot.chocofactory[employee]["factory_"+str(prestige_level)][level+1]

            cost_data[employee] = next_level_cost

            if next_level_cost > 0:
                cps_data[employee] = next_level_cost/(cookies_per_second_employees[employee])


        best_employee = None
        if len(cps_data) == 0:
            pass

        else:
            for employee in cps_data:
                if best_employee is None:
                    best_employee = employee

                elif cps_data[employee] < cps_data[best_employee]:
                    best_employee = employee        

        upgrades_string = ""
        for employee in employee_data:
            emoji = factory_emojis[employee]
            addition = ""
            if best_employee == employee:
                addition = f" {factory_emojis['best']}"

            cost = cost_data[employee]
            if cost == 0:
                cost_string = "**MAXED**"
            
            else:
                cost_string = f"Next Level: **{numerize(cost)}**"

            chocolate_per_second += employee_data[employee]*cookies_per_second_employees[employee]

            upgrades_string += f"\n{emoji} {employee_names[employee]}: **{employee_data[employee]}**/{120+(prestige_level-1)*20} ({cost_string}){addition}"


        upgrades_string += f"\n\n{factory_emojis['barn_c']} Barn Capacity level: **{rbcl}** ({unique_rabbits}/**{18+(2*rbcl)}**)"
        upgrades_string += f"\n{factory_emojis['rabbit_click']} Chocolate Per Click: **{click_level}**/10"

        if prestige_level >= 3:
            upgrades_string += f"\n{factory_emojis['shrine_l']} Shrine level: **{shrine_level}**/20 (**{shrine_level}%** increased chance)"

        if prestige_level >= 4:
            upgrades_string += f"\n{factory_emojis['JackRabbitUpgrade']} Coach Jackrabbit: **{jackrabbit}**/20 (+**{round(jackrabbit*0.1, 1)}x** multiplier)"

        embed.add_field(
            name="Upgrades",
            value=upgrades_string,
            inline=False
        )

        factory_level_multis = {
            1: 0,
            2: 0.1,
            3: 0.25,
            4: 0.5,
            5: 1
        }

        cookie_mult = 0
        if self.cookie:
            cookie_mult = .25

        tt_string = ""
        time_tower_multiplier = 0
        if len(active) != 0:
            time_tower_multiplier = 0.1*time_tower_level
            tt_string = " (**TIME TOWER ACTIVE**)"


        _chocolate_per_second_no_time_tower = chocolate_per_second*(1+(chocolate_per_second_multiplier+factory_level_multis[prestige_level]+cookie_mult+jackrabbit_multi))
        _chocolate_per_second = chocolate_per_second*(1+(chocolate_per_second_multiplier+factory_level_multis[prestige_level]+cookie_mult+time_tower_multiplier+jackrabbit_multi))

        chocolate_since_view = _chocolate_per_second_no_time_tower*(seconds_since_last_view-seconds_time_tower) + _chocolate_per_second*(seconds_time_tower)

        embed.description = f"""
{factory_emojis['choc']} Chocolate: **{numerize(chocolate_amount+chocolate_since_view)}** (**{numerize(since_prestige+chocolate_since_view)}** since Prestige)
{factory_emojis['choc']} Lifetime Chocolate: **{numerize(total_chocolate+chocolate_since_view)}**
{factory_emojis['choc']} Chocolate per Second: **{format(int(_chocolate_per_second), ',d')}**{tt_string}

{factory_emojis['u_rab']} Unique Rabbits: **{unique_rabbits}**
{factory_emojis['fac_lvl']} Factory Level: **{prestige_level}**"""

        if prestige_level >= 2:
            time_tower_string = ""        
            time_tower_string += f"\n{factory_emojis['time_tower']} Level: **{time_tower_level}**/15 (+**{round(0.1*time_tower_level, 1)}x** multiplier)"
            time_tower_string += f"\n{factory_emojis['charge']} Charges: **{time_tower_charges}**/3 ({timestamp}){active}"

            embed.add_field(
                name="Time Tower",
                value=time_tower_string,
                inline=False
            )

        unique_rabbits_string = ""
        for rarity in rarities:
            if rarity in rabbit_rarities_count:
                unique_rabbits_string += f"{RARITY_EMOJIS[rarity]} {rarity.title()}: **{rabbit_rarities_count[rarity]}**\n"

        if len(unique_rabbits_string) == 0:
            unique_rabbits_string = "No Rabbits :("

        embed.add_field(
            name="Rabbit Rarities",
            value=unique_rabbits_string
        )

        talisman_emojis = {
            "NIBBLE_CHOCOLATE_STICK": "<:GOD01z5DTzXeSh3r:1236497543714570301>",
            "SMOOTH_CHOCOLATE_BAR": "<:UmtTOHUyHYPXChQu:1236497557765619783>",
            "RICH_CHOCOLATE_CHUNK": "<:TRWzhgUu87k49LkV:1238415489621819425>",
            "GANACHE_CHOCOLATE_SLAB": "<:e8t8PaUlLFJZS07z:1236428501813297255>",
            "PRESTIGE_CHOCOLATE_REALM": "<:e8t8PaUlLFJZS07z:1236428501813297255>"
        }

        items_string = f"""
<:e8t8PaUlLFJZS07z:1236428501813297255> Mythic Rabbit: **{mythic_rabbit}**
{talisman_emojis[best]} Best Talisman: **{best.replace('_', ' ').title()}**"""
        
        embed.add_field(
            name="Items",
            value=items_string,
            inline=False
        )

        embed.set_footer(
            text=get_footer("nom")
        )
    
        return embed
    
    
    @select(row=0)
    async def select_profile(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.defer()

        for option in select.options:
            option.default = False
            if option.value == select.values[0]:
                option.default = True

        self.embed_cutename = select.values[0]
        embed = await self.create_embed()
        
        if interaction.user.id != self.user_id:
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            await interaction.edit_original_response(embed=embed, view=self)

    @button(row=1, label="Cookie", style=discord.ButtonStyle.green, emoji="<a:DhsMMKZnFqaFsCVk:1236445806870007910>")
    async def toggle_cookie(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.cookie = not self.cookie
        embed = await self.create_embed()

        button.style = discord.ButtonStyle.red if not self.cookie else discord.ButtonStyle.green

        if interaction.user.id == self.user_id:
            await interaction.response.edit_message(embed=embed, view=self)

        else:
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
