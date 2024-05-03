import discord

async def timeout_view(self):
    self.counter += 1
    if self.counter == 2:
        for child in self.children:
            child.disabled = True

        try:
            await self.interaction.edit(view=self)
            self.stop()

        except discord.errors.NotFound:
            self.stop()
            return