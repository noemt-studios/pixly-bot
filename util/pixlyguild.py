from discord.ui import Button, View
import discord
from discord import Interaction

from constants import MEMBER_ROLE_ID

class VerificationView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(ManualVerifyButton(bot))

class ManualVerifyButton(Button):
    def __init__(self, bot):
        super().__init__(style=discord.ButtonStyle.grey, label="Manual Verify", custom_id="manual_verify")
        self.bot = bot

    async def callback(self, interaction: Interaction):
        role = interaction.guild.get_role(MEMBER_ROLE_ID)

        await interaction.response.send_message("You have been verified!", ephemeral=True)
        await interaction.user.add_roles(role)


