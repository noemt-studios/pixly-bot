import discord
from discord.ext import commands, tasks
import os, aiohttp, json

from constants import DISCORD_BOT_TOKEN
from util.context import PixlyContext
from pymongo import MongoClient
from skyblockparser.profile import Profile
from datetime import datetime

def traverse_and_add_options(data_dict, path=""):

    options = {}
    if not isinstance(data_dict, dict):
        return options

    for key, value in data_dict.items():
        current_path = path + "." + key if path else key
        if isinstance(value, (int, float)):
            name = current_path.replace(".", " ").replace("_", " ").title()
            options[name] = current_path

        elif isinstance(value, dict):
            options.update(traverse_and_add_options(value, current_path))

    return options


class Emojis:
    def __init__(self):
        with open("./data/emojis.json") as file:
            emojis = json.load(file)

        for name, emoji in emojis.items():
            setattr(self, name, emoji)

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.command_prefix = ">"
        self.owner_ids = [1233409760078991422]
        self.token = DISCORD_BOT_TOKEN
        self.session = None
        self.cache = {}
        self._emojis = Emojis()
        self.exchange_rates = {}
        self.auctionable = []
        self.item_emojis = {}

        self.client = MongoClient("mongodb://127.0.0.1:27017/")
        self.db = self.client["pixly"]

        self.collection = self.db["profiles"]
        self.bazaar = self.db["bazaar"]
        self.items = self.db["items"]


        for filename in os.listdir("commands"):
            if filename.endswith(".py"):
                self.load_extension(f"commands.{filename[:-3]}")


    def get_data(self, uuid, cute_name):
        return self.collection.find_one({"string": f"{uuid}-{cute_name}"})
    

    async def handle_data(self, uuid: str, profile_data: Profile, username: str):
        data = self.get_data(uuid, profile_data.cute_name)
        if data is None:
            data = {"uuid": uuid, "cute_name": profile_data.cute_name, "data": {}, "username": username}
        
        data["data"] = await profile_data.get_json()
        self.collection.update_one({"string": f"{uuid}-{profile_data.cute_name}"}, {"$set": data}, upsert=True)


    async def get_leaderboard(self, stat: str, page: int):

        query = self.collection.find({f"data.{stat}": {"$exists": True}}).sort(f"data.{stat}", -1).skip(25*page).limit(25)

        leaderboard = []

        for data in query:
            leaderboard.append(data)

        return leaderboard


    def embed(self, description):
        embed=discord.Embed(description=description, color=discord.Color.blue())
        embed.set_author(name=self.user.name, icon_url=self.user.avatar.url if self.user.avatar else self.user.default_avatar.url)
        return embed

    @property
    def emojis(self):
        return self._emojis

    @emojis.setter
    def emojis(self, value):
        self._emojis = value

    @tasks.loop(seconds=120)
    async def clear_cache(self):
        self.cache = {}

    async def on_ready(self):
        self.clear_cache.start()
        self.session = aiohttp.ClientSession()
        self.update_skyblock_data.start()

        with open("./data/mappings.json") as f:
            self.item_emojis = json.load(f)
            
        print(f"Logged in as {self.user}")

        query = self.collection.find({"string": "fb3d96498a5b4d5b91b763db14b195ad-Blueberry"})
        
        options = traverse_and_add_options(query[0]["data"])
                
        with open("./data/lb.json", "w") as f:
            json.dump(options, f, indent=4)

    async def get_application_context(self, 
        interaction: discord.Interaction, 
        cls=PixlyContext
    ):
        return await super().get_application_context(interaction, cls=cls)
    
    async def on_interaction(self, interaction:discord.Interaction):
        return await super().on_interaction(interaction)

    @tasks.loop(seconds=90)
    async def update_skyblock_data(self):
        async with self.session.get("https://api.hypixel.net/skyblock/bazaar") as resp:
            data = await resp.json()
            bazaar = data["products"]
            
        async with self.session.get("https://api.hypixel.net/v2/resources/skyblock/items") as resp:
            data = await resp.json()
            items = data["items"]

        self.auctionable = []

        for item in items:
            if item["id"] not in bazaar:
                self.auctionable.append(item)

        self.update = datetime.now().timestamp()
        self.items.update_one({"_id": 1}, {"$set": {"data": items}}, upsert=True)
        self.bazaar.update_one({"_id": 1}, {"$set": {"data": bazaar, "timestamp": self.update}}, upsert=True)
        

    def run(self):
        self.loop.create_task(self.start(self.token))
        self.loop.run_forever()


intents = discord.Intents.default()
activity = discord.CustomActivity("/help | by @noemt")
# intents.members = True

bot = Bot(command_prefix=">", intents=intents, activity=activity)

bot.run()