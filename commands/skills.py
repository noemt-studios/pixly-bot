import discord
from discord import slash_command, option
from util.cog import Cog
from util.profile_autocomplete import get_profiles, get_uuid
from skyblockparser.profile import SkyblockParser
from util.views import SkillsView
from util.embed import get_embed

class Skills(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(category="Stat Commands")

    @slash_command(
        name="skills",
        description="Get the skills of a player",
        integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install},
    )
    @option(
        name="player",
        description="The player to get the skills of",
        required=True,
        type=str,
    )
    @option(
        name="profile",
        description="The profile to get the skills of",
        required=False,
        type=str,
        autocomplete=get_profiles
    )
    async def skills(self, ctx:discord.ApplicationContext, name: str, profile: str = "selected"):
        await ctx.defer()

        while True:
            _uuid = await get_uuid(self.bot.session, name, True)
            if _uuid == "Invalid username.":
                return await ctx.respond(embed=get_embed("Invalid username.", self.bot))
            
            elif _uuid is not None:
                break
            
        uuid = _uuid["id"]
        username = _uuid["name"]

        cached_data = self.bot.cache.get(uuid, {})

        if cached_data is not {}:
            async with self.bot.session.get(f"https://api.hypixel.net/v2/skyblock/profiles?key={self.hypixel_api_key}&uuid={uuid}") as request:
                data = await request.json()
                if data["success"] is False:
                    return await ctx.respond(embed=get_embed("Something went wrong.", self.bot))

                if data["profiles"] is None:
                    return await ctx.respond(embed=get_embed("No profiles found.", self.bot))

            parser = SkyblockParser(data, uuid, self.hypixel_api_key)
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

        interaction = await ctx.respond("\u200b")
        view = SkillsView(username, self.bot, parser, cute_name, interaction)
        embed = await view.create_embed()
        await interaction.edit(embed=embed, view=view)


def setup(bot):
    bot.add_cog(Skills(bot))
