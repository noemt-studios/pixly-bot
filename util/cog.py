from discord.ext import commands
from constants import HYPIXEL_API_KEY

class Cog(commands.Cog):
    def __init__(self, category):
        self.hypixel_api_key = HYPIXEL_API_KEY
        self.category = category
