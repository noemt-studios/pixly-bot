async def get_data_from_cache(self):

    cache = self.bot.cache
    if not cache.get(self.parser.uuid):

        cache[self.parser.uuid] = {"parser": self.parser}

        profile_data = self.parser.select_profile(self.embed_cutename)
        await profile_data.init()

        self.bot.cache[profile_data.uuid][profile_data.cute_name] = profile_data

    else:
        if cache[self.parser.uuid].get(self.embed_cutename):
            profile_data = cache[self.parser.uuid][self.embed_cutename]

        else:
            profile_data = self.parser.select_profile(self.embed_cutename)
            await profile_data.init()
            self.bot.cache[profile_data.uuid][profile_data.cute_name] = profile_data

    await self.bot.handle_data(profile_data.uuid, profile_data, self.username)

    return profile_data