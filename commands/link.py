import discord
from discord.ext import commands
from discord import option
import aiohttp
from util.profile_autocomplete import get_uuid
from util.footer import get_footer
from constants import HYPIXEL_API_KEY

class LinkAccount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="link",
        description="Links your Discord Account to a Minecraft Account.",
        integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install},
    )
    @option(
        name="username",
        description="The Minecraft Username you want to link.",
        required=True,
        type=str,
    )
    async def link(self, ctx:discord.ApplicationContext, username: str):

        await ctx.defer()
        footer = get_footer("nom")
       
        async with aiohttp.ClientSession() as session:

            uuid = None
            while uuid is None:
                uuid = await get_uuid(session, username)

            if uuid == "Invalid username.":
                await ctx.followup.send(
                    embed=discord.Embed(
                        title="Error",
                        description="Invalid Minecraft Username.",
                        color=discord.Color.red(),
                    )
                )

            else:
                async with session.get(f"https://api.hypixel.net/player?key={HYPIXEL_API_KEY}&uuid="+uuid) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("player") is None:
                            await ctx.followup.send(
                                embed=discord.Embed(
                                    title="Error",
                                    description="This Account has not played on Hypixel yet.",
                                    color=discord.Color.blue(),
                                ).set_thumbnail(url=self.bot.user.avatar.url).set_footer(text=footer)
                            )
                            return

                        social_media = data.get("player").get("socialMedia")
                        if social_media is None:
                            await ctx.followup.send(
                                embed=discord.Embed(
                                    title="Error",
                                    description="This Account has not linked their Discord Account.",
                                    color=discord.Color.blue(),
                                ).set_thumbnail(url=self.bot.user.avatar.url).set_footer(text=footer)
                            )
                            return
                        
                        if social_media.get("links").get("DISCORD") is None:
                            await ctx.followup.send(
                                embed=discord.Embed(
                                    title="Error",
                                    description="This Account has not linked their Discord Account.",
                                    color=discord.Color.blue(),
                                ).set_thumbnail(url=self.bot.user.avatar.url).set_footer(text=footer)
                            )
                            return
                        
                        discord_link = social_media.get("links").get("DISCORD")
                        
                        if discord_link != ctx.author.name:
                            await ctx.followup.send(
                                embed=discord.Embed(
                                    title="Error",
                                    description=f"`{discord_link}` is currently linked to the minecraft account, which does not equal `{ctx.author.name}`. Please relink the account before trying again.",
                                    color=discord.Color.blue(),
                                ).set_thumbnail(url=self.bot.user.avatar.url).set_footer(text=footer)
                            )
                            return
                        

                        self.bot.verified.update_one(
                            {"uuid": uuid},
                            {"$set": {"discord": ctx.author.id}},
                            upsert=True
                        )

                        await ctx.followup.send(
                            embed=discord.Embed(
                                title="Success",
                                description=f"Your Minecraft Account has been linked!\nYou can now use commands without entering a Username.",
                                color=discord.Color.blue(),
                            ).set_thumbnail(url=self.bot.user.avatar.url).set_footer(text=footer)
                        )
                        return

                    else:
                        await ctx.followup.send(
                            embed=discord.Embed(
                                title="Error",
                                description="An error occured while trying to fetch your Hypixel Account.",
                                color=discord.Color.blue(),
                            ).set_thumbnail(url=self.bot.user.avatar.url).set_footer(text=footer)
                        )
                        return


    @commands.slash_command(
        name="unlink",
        description="Unlinks a Discord Account from your Minecraft Account.",
        integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install},
    )
    async def unlink(self, ctx):

        footer = get_footer("nom")

        data = self.bot.verified.find_one({"discord": ctx.author.id})
        if data is None:
            await ctx.followup.send(
                embed=discord.Embed(
                    title="Error",
                    description="You have not linked any Minecraft Account.",
                    color=discord.Color.red(),
                ).set_thumbnail(url=self.bot.user.avatar.url).set_footer(text=footer)
            )
            return

        self.bot.verified.delete_one({"discord": ctx.author.id})
        await ctx.followup.send(
            embed=discord.Embed(
                title="Success",
                description="Your Minecraft Account has been unlinked.",
                color=discord.Color.green(),
            ).set_thumbnail(url=self.bot.user.avatar.url).set_footer(text=footer)
        )


def setup(bot):
    bot.add_cog(LinkAccount(bot))
