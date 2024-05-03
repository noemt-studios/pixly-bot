import discord
from discord.ext import commands
import json
import aiohttp
import asyncio
from constants import EMOJI_SERVERS
from util.embed import get_embed

class HelpCommand(commands.Cog):
    def __init__(self, bot):

        self.bot = bot

    @commands.slash_command(
        name="help",
        description="Shows a list of commands.",
    )
    async def help(self, ctx):
        await ctx.defer()

        all_commands = ""
        for cog in self.bot.cogs:
            for command in self.bot.get_cog(cog).walk_commands():

                if isinstance(commands, discord.SlashCommandGroup):
                    continue


                if not isinstance(command, discord.SlashCommand):
                    continue
                

                string = f"</{command.qualified_name}:{command.qualified_id}> "
                for option in command.options:
                    string += f"`[{option.name}]` " if option.required else f"`<{option.name}>` "

                string += "\n"
                all_commands += string


        embed = discord.Embed(
            title="Help",
            color=discord.Color.blue(),
            description="[..] = Required, <..> = Optional\n\n"+all_commands
        )
    
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="fetch-emojis",
        description="Fetches all emojis from the server. in the format <name:id>.",
    )
    @commands.is_owner()
    async def fetch_emojis(self, ctx:discord.ApplicationContext):
        await ctx.defer()

        emojis = {}
        for guild in self.bot.guilds:
            for emoji in guild.emojis:
                emojis[emoji.name] = f"<:{emoji.name}:{emoji.id}>"
        
        with open("emojis.json", "w") as file:
            json.dump(emojis, file, indent=4)

        await ctx.respond(file=discord.File("emojis.json"))


    @commands.slash_command(
        name="upload-emojis-to-servers",
        description="Uploads all missing emojis to an available emoji slot and updates the mappings accordingly.",
    )
    @commands.is_owner()
    async def upload_emojis_to_servers(self, ctx:discord.ApplicationContext):
        available_slots = {}

        for server in EMOJI_SERVERS:
            guild:discord.Guild = self.bot.get_guild(server)
            emoji_amount = len(guild.emojis)
            if emoji_amount >= 50:
                continue

            available_slots[server] = 50 - emoji_amount
        
        with open("./emojis/itemHash.json", "r") as f:
            item_hashes:dict = json.load(f)

        my_emojis = {}
        for guild in self.bot.guilds:
            for emoji in guild.emojis:
                my_emojis[emoji.name] = f"<:{emoji.name}:{emoji.id}>"

        with open("./emojis/emojis.json", "r") as f:
            new_emojis:dict = json.load(f)

        with open("./data/mappings.json", "r") as file:
            mappings:dict = json.load(file)


        need_uploading = []

        for item in item_hashes:
            item_hash = item_hashes[item]

            emoji_data = new_emojis[item_hash]

            emoji_data_normal_name = emoji_data["normal"]["name"]
            my_emoji:str = my_emojis.get(emoji_data_normal_name, None)
            if not my_emoji:
                need_uploading.append(item)


        if len(need_uploading) > sum(available_slots.values()):
            return await ctx.respond("Not enough emoji slots available please add the bot to more emoji servers.")

        session = aiohttp.ClientSession()
        await ctx.defer()
        
        for item in need_uploading:
            item_hash = item_hashes[item]
            emoji_data = new_emojis[item_hash]

            emoji_data_normal_name = emoji_data["normal"]["name"]
            emoji_data_normal_id = emoji_data["normal"]["id"]
            animated = emoji_data["normal"]["animated"]

            emoji_data_normal_url = f"https://cdn.discordapp.com/emojis/{emoji_data_normal_id}.{'gif' if animated else 'png'}"
            async with session.get(emoji_data_normal_url) as response:
                if response.status != 200:
                    continue

                emoji_data = await response.read()

            for server in EMOJI_SERVERS:
                guild:discord.Guild = self.bot.get_guild(server)
                emoji_amount = len(guild.emojis)

                if emoji_amount >= 50:
                    continue

                emoji = await guild.create_custom_emoji(name=emoji_data_normal_name, image=emoji_data)
                mappings[item] = {
                    "name": emoji.name,
                    "url": emoji.url,
                    "id": emoji.id
                }

                break

            await asyncio.sleep(3)

        with open("./data/mappings.json", "w") as file:
            json.dump(mappings, file, indent=4)

        await session.close()
        embed = self.bot.embed(f"Finished uploading {len(need_uploading)} emojis.")
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="info",
        description="Shows information about the bot.",
    )
    async def info(self, ctx:discord.ApplicationContext):
        await ctx.defer()

        view = discord.ui.View()
        info = discord.ui.Button(row=1, label="Info:", disabled=True)
        github_button = discord.ui.Button(row=1, label="Support Server", url="https://discord.gg/wPvD9c6FBc")
        website_button = discord.ui.Button(row=1, label="Website", url="https://pixly.noemt.dev")
        legal = discord.ui.Button(row=2, label="Legal:", disabled=True)
        tos_button = discord.ui.Button(row=2, label="Terms of Service", url="https://pixly.noemt.dev/tos")
        privacy_button = discord.ui.Button(row=2, label="Privacy Policy", url="https://pixly.noemt.dev/privacy")

        view.add_item(info)
        view.add_item(github_button)
        view.add_item(website_button)
        view.add_item(legal)
        view.add_item(tos_button)
        view.add_item(privacy_button)


        embed = discord.Embed(
            title="Info",
            color=discord.Color.blue(),
            description="A bot that fetches data from the Hypixel API and displays it in a user-friendly way."
        )
        embed.set_author(name="@noemt", icon_url="https://cdn.discordapp.com/avatars/1102912537424560160/b0845cf357bb9425539f098d46012cf6", url="https://github.com/noemtdev")
        embed.set_image(url=self.bot.user.avatar.url)

        embed.add_field(
            name="Programming Language",
            value="`🐍` Python (py-cord library)",
        )

        embed.add_field(
            name="Hosting",
            value="`🌐` Hetzner",
        )

        embed.add_field(
            name="Last Update (Bazaar and Skyblock Items)",
            value=f"<t:{int(self.bot.update)}:R>",
            inline=False
        )

        await ctx.respond(embed=embed, view=view)


    @fetch_emojis.error
    @upload_emojis_to_servers.error
    async def on_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            embed = get_embed("You are not the owner of the bot.", self.bot)
            await ctx.respond(embed=embed)
        else:
            raise error


def setup(bot):
    bot.add_cog(HelpCommand(bot))