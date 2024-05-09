import discord
from discord.ext import commands
from discord import option
from util.views import LeaderboardView
import json

async def leaderboard_autocompete(ctx:discord.AutocompleteContext):
    with open("./data/lb.json", "r") as f:
        options = json.load(f)

    stat = ctx.options["statistic"]

    return [key for key in options if key.lower().startswith(stat.lower())]

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="leaderboard",
        description="Shows the leaderboard for a specific statistic.",
        integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install},
    )
    @option(
        name="statistic",
        description="The statistic to show the leaderboard for.",
        required=True,
        type=str,
        autocomplete=leaderboard_autocompete
    )
    async def leaderboard(self, ctx:discord.ApplicationContext, statistic:str):
        with open("./data/lb.json", "r") as f:
            options = json.load(f)

        if statistic not in options:
            return await ctx.respond("Invalid statistic.")
        
        ugly_statistic = options[statistic]
        
        await ctx.defer()

        view = LeaderboardView(ctx.author.id, self.bot, ugly_statistic, statistic)
        embed = await view.create_embed()
    
        await ctx.respond(embed=embed, view=view)

def setup(bot):
    bot.add_cog(Leaderboard(bot))