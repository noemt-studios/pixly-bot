import discord
from discord import slash_command, option
from util.cog import Cog
from util.embed import get_embed
import aiohttp
from util.profile_autocomplete import get_usernames

class Status(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(category="Stat Commands")
 
    @slash_command(
        name="status",
        description="Get the online status of a player",
        integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install},
    )
    @option(
        name="name",
        description="The player to get the status of",
        required=True,
        type=str,
        autocomplete=get_usernames
    )
    async def status(self, ctx: discord.ApplicationContext, name: str):
        await ctx.defer()

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.mojang.com/users/profiles/minecraft/{name}") as request:
                if request.status == 204:
                    embed = get_embed("Invalid username.", self.bot)
                    return await ctx.followup.send(embed=embed)
                
                data = await request.json()
                uuid = data["id"]
                username = data["name"]
                async with session.get(f"https://api.hypixel.net/status?key={self.hypixel_api_key}&uuid={uuid}") as request:
                    data = await request.json()
                    if data["success"] is False:
                        embed = get_embed("Something went wrong.", self.bot)
                        return await ctx.respond(embed=embed)
                    
                    async with session.get(f"https://api.hypixel.net/player?key={self.hypixel_api_key}&uuid={uuid}") as request:
                        _data = await request.json()
                        if _data["success"] is False:
                            embed = get_embed("Something went wrong.", self.bot)
                            return await ctx.respond(embed=embed)
                        
                        last_login = _data["player"]["lastLogin"]//1000
                    
                    if data["session"]["online"] is False:
                        embed = discord.Embed(
                            title=f"Online Status for {username}",
                            url=f"https://plancke.io/hypixel/player/stats/{username}",
                            description=f"""{username} is currently **offline**.
Last login: **<t:{last_login}:R>**""",
                            color=discord.Color.blue()

                        ).set_thumbnail(url=f"https://mc-heads.net/body/{uuid}/left")
                        return await ctx.respond(embed=embed)
                    
                    elif data["session"]["online"] is True:
                        embed = discord.Embed(
                            title=f"Online Status for {username}",
                            url=f"https://plancke.io/hypixel/player/stats/{username}",
                            description=f"""{username} is currently **online**.
Last login: **<t:{last_login}:R>**""",
                            color=discord.Color.blue()

                        ).set_thumbnail(url=f"https://mc-heads.net/body/{uuid}/left")
                        embed.add_field(
                            name="Game",
                            value=data["session"]["gameType"].title(),
                        )
                        mode = data["session"].get("mode")
                        if mode:
                            embed.add_field(
                                name="Gamemode",
                                value=mode.title(),
                            )
                        
                        return await ctx.respond(embed=embed)
                    
                    else:
                        embed = get_embed("An unknown issue occured.", self.bot)
                        return await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Status(bot))
