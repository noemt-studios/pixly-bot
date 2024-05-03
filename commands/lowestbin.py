import discord
from discord.ext import commands
from util.cog import Cog
from discord import option
from PIL import Image
from util.renderer import render
import io
from numerize.numerize import numerize
import urllib.parse

url = "https://auction-house.noemt.dev"


colors = {
    "COMMON": 0x9e9e9e,
    "UNCOMMON": 0x00ff00,
    "RARE": 0x0000ff,
    "EPIC": 0x800080,
    "LEGENDARY": 0xffa500,
    "MYTHIC": 0xff00ff,
    "SPECIAL": 0xff0000,
    "VERY SPECIAL": 0xff0000,
    "SUPREME": 0x55FFFF
}

async def items_autocomplete(ctx: discord.AutocompleteContext):
    return [item["name"] for item in ctx.bot.auctionable if item["name"].lower().startswith(ctx.value.lower())]


class LBin(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(category="Auction Commands")

    @commands.slash_command(
        name="lowest-bin",
        description="Get's the lowest BIN price for an item.",
        integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install},
    )
    @option(
        name="item",
        description="The item you want to get the lowest BIN for.",
        required=True,
        type=str,
        autocomplete=items_autocomplete
    )
    async def lbin(self, ctx, item: str):
        await ctx.defer()

        item = urllib.parse.quote(item)

        async with self.bot.session.get(f"{url}/lowestprice/"+item) as resp:

            if resp.status != 200:
                return await ctx.respond(embed=self.bot.embed("An error occurred while fetching the data."))
            
            response = await resp.json()

        if response.get("error"):
            return await ctx.respond(embed=self.bot.embed("That item doesn't exist."))
        
        
        embed = discord.Embed(
            title=f"Lowest BIN for {urllib.parse.unquote(item)}", 
            color=colors[response["rarity"]]
        )

        lore:list = response["itemLore"].split("\n")
        name:str = response["itemName"]

        lore.insert(0, name)

        image: Image = render(lore)
        image_binary = io.BytesIO()
        image.save(image_binary, format="PNG")
        image_binary.seek(0)

        async with self.bot.session.get("https://sessionserver.mojang.com/session/minecraft/profile/"+response['auctioneer']) as resp:
            if resp.status != 200:
                username = "Unknown"

            data = await resp.json()
            username = data["name"]
        
        embed.description = f"""
Auctioneer: **{username}**
Price: **{numerize(response['price'])}**
"""
        
        embed.set_image(
            url="attachment://image.png"
        )
    
        embed.add_field(
            name="View Auction",
            value=f"`{response['command']}`"
        )
        await ctx.respond(embed=embed, file=discord.File(fp=image_binary, filename="image.png"))


def setup(bot):
    bot.add_cog(LBin(bot))
