from discord.ext import commands
from util.pixlyguild import VerificationView
from constants import MAIN_SERVER_ID, MEMBER_ROLE_ID

class PixlyUtil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="setup-verify",
        description="Setup the verification system for your server",
        guild_ids=[MAIN_SERVER_ID],
    )
    @commands.has_permissions(administrator=True)
    async def setup_verify(self, ctx):
        view = VerificationView(self.bot)
        await ctx.send(f"Click the Button below to obtain the <@&{MEMBER_ROLE_ID}> role", view=view)
        await ctx.respond("Verification system has been setup!", ephemeral=True)

def setup(bot):
    bot.add_cog(PixlyUtil(bot))
