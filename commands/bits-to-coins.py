import discord
from discord.ext import commands
from util.cog import Cog
from util.views import BasePaginator
from numerize.numerize import numerize

class Bits(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(category="Bits Commands")

    @commands.slash_command(
        name="bits",
        description="Shows best bit-shop items for you to buy.",
        integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install},
    )
    async def bits(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        price_database = self.bot.prices
        bits_data:dict = self.bot.bits_data

        bits_prices = {}
        for item in bits_data:

            item_data = bits_data[item]

            price = item_data["price"]
            coin_value = price_database.find_one({"item": item.lower()})

            try:
                coin_value = coin_value["price"]
            except:
                continue

            if item == "64_INFERNO_FUEL_BLOCK":
                coin_value = price_database.find_one({"item": "INFERNO_FUEL_BLOCK"})["price"]*64

            bits_prices[item] = {**item_data, "per_bit": coin_value/price, "value": coin_value}

        sorted_prices = sorted(bits_prices.items(), key=lambda x: x[1]["per_bit"], reverse=True)
        pages = [sorted_prices[i:i+20] for i in range(0, len(sorted_prices), 20)]
        embeds = []

        for page in enumerate(pages):
            index = page[0]
            page = page[1]

            embed = discord.Embed(
                title="Bits to Coins",
                color=discord.Color.blue()
            ).set_footer(text=f"Page {index+1}/{len(pages)} | Made by nom")

            desc_text = ""

            for item in enumerate(page):
                item_index = item[0]
                item = item[1]

                item_data = item[1]
                item_id = item[0]

                if item_data.get("texture") is not None:
                    item_id = item_data["texture"]

                emoji_data = self.bot.item_emojis.get(item_id)
                if emoji_data is not None:
                    emoji_start = "<:"
                    if emoji_data["url"].endswith(".gif"):
                        emoji_start = "<a:"

                    emoji = f"{emoji_start}{emoji_data['name']}:{emoji_data['id']}>"
                else:
                    emoji = "❔"

                fbp = format(item_data['price'], ',d')
                fiv = numerize(item_data["value"])
                fperb = round(["per_bit"], 2)
                item_position = item_index+1+(20*index)

                desc_text += f"`{item_position}.` {emoji} **{item_data['name']}**: **{fperb}** coins/bit ({fbp} bits, {fiv})\n"

            embed.description = desc_text
            embeds.append(embed)

        paginator = BasePaginator(embeds, ctx.author.id)
        await ctx.followup.send(embed=embeds[0], view=paginator)

def setup(bot):
    bot.add_cog(Bits(bot))
